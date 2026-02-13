import secrets
import time
from k8s_client import K8sClient
from templates.mysql import get_mysql_secret, get_mysql_service, get_mysql_statefulset
from templates.wordpress import get_wordpress_config, get_wordpress_pvc, get_wp_setup_script, get_wordpress_deployment, get_wordpress_service
from templates.ingress import get_ingress
import database

class StoreManager:
    def __init__(self):
        self.k8s = K8sClient()
        # database.init_db() - Now handled in app.py
    
    def generate_store_id(self):
        """Generate unique store ID"""
        return secrets.token_hex(4)
    
    def create_store(self, user_id, sample_products=None, store_url_suffix=None, admin_password=None, storage_size_gi=2):
        """Create a new store"""
        # 1. Quota Check
        user = database.get_user(user_id)
        if not user:
            return {"error": "User not found"}

        usage = database.get_user_usage(user_id)
        current_stores = usage['store_count'] or 0
        current_storage = usage['total_storage'] or 0

        if current_stores >= user['max_stores']:
            return {"error": f"Store limit reached ({user['max_stores']} stores)."}

        # Assuming MySQL takes 2Gi fixed + requested Wordpress storage
        total_request = storage_size_gi + 2

        if (current_storage + total_request) > user['max_storage_gi']:
            return {"error": f"Storage quota exceeded. Available: {user['max_storage_gi'] - current_storage}Gi, Requested: {total_request}Gi"}

        # 2. Generate Store Details
        store_id = self.generate_store_id()
        namespace = f"store-{store_id}"
        if store_url_suffix:
            store_url = f"store-{store_id}.{store_url_suffix}"
        else:
            store_url = f"store-{store_id}.local"

        # Use provided password or generate one
        db_password = admin_password if admin_password else secrets.token_urlsafe(16)

        if sample_products is None:
            sample_products = "Sample Product 1|10.00|This is a sample product\nSample Product 2|20.00|Another sample product"

        # 3. Register in DB with "initialized" status
        database.register_store(store_id, user_id, total_request, status="initialized")

        print(f"\n=== Creating store: {store_id} ===")
        print(f"📝 Status: initialized")

        try:
            # 4. Update status to "provisioning" before starting k8s operations
            database.update_store_status(store_id, "provisioning")
            print(f"🚀 Status: provisioning")

            # Create namespace
            if not self.k8s.create_namespace(namespace):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create namespace"}

            # Create MySQL secret
            mysql_secret = get_mysql_secret(store_id, db_password)
            if not self.k8s.create_secret(namespace, mysql_secret):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create MySQL secret"}

            # Create MySQL service
            mysql_svc = get_mysql_service(store_id)
            if not self.k8s.create_service(namespace, mysql_svc):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create MySQL service"}

            # Create MySQL StatefulSet
            mysql_ss = get_mysql_statefulset(store_id)
            if not self.k8s.create_statefulset(namespace, mysql_ss):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create MySQL"}

            # Wait for MySQL to be ready
            print("⏳ Waiting for MySQL to be ready...")
            time.sleep(30)  # Simple wait; improve with actual pod checking

            # Create WordPress ConfigMap
            wp_config = get_wordpress_config(store_id, db_password, store_url, sample_products)
            if not self.k8s.create_configmap(namespace, wp_config):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create WordPress config"}

            # Create WordPress PVC (With custom size)
            wp_pvc = get_wordpress_pvc(store_id, storage_size_gi)
            if not self.k8s.create_pvc(namespace, wp_pvc):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create WordPress PVC"}

            # Create WP Setup Script ConfigMap
            wp_setup = get_wp_setup_script(store_id, db_password, store_url, sample_products)
            if not self.k8s.create_configmap(namespace, wp_setup):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create WP setup script"}

            # Create WordPress Deployment
            wp_deployment = get_wordpress_deployment(store_id, db_password, store_url)
            if not self.k8s.create_deployment(namespace, wp_deployment):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create WordPress"}

            # Create WordPress Service
            wp_service = get_wordpress_service(store_id)
            if not self.k8s.create_service(namespace, wp_service):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create WordPress service"}

            # Create Ingress
            ingress = get_ingress(store_id, store_url)
            if not self.k8s.create_ingress(namespace, ingress):
                database.update_store_status(store_id, "failed")
                return {"error": "Failed to create Ingress"}

            # 5. Update status to "ready" when complete
            database.update_store_status(store_id, "ready")
            print(f"✅ Store created successfully! Status: ready\n")

            return {
                "id": store_id,
                "namespace": namespace,
                "url": f"http://{store_url}",
                "admin_url": f"http://{store_url}/wp-admin",
                "admin_user": "admin",
                "admin_password": db_password,
                "status": "ready",
                "created_at": time.time(),
                "owner": user['username']
            }
        except Exception as e:
            # If any unexpected error occurs, mark as failed
            database.update_store_status(store_id, "failed")
            print(f"❌ Error creating store: {e}")
            return {"error": f"Store creation failed: {str(e)}"}
    
    def list_stores(self, user_id=None):
        """List all stores, optionally filtered by user"""
        namespaces = self.k8s.list_store_namespaces()

        # Use new database function that returns all stores at once
        db_stores = database.get_all_stores_with_users()

        stores = []

        for ns in namespaces:
            store_id = ns.replace("store-", "")

            # Filter by user if provided
            if user_id:
                if store_id not in db_stores:
                    continue # Skip unmanaged/system stores if filtering by user
                if str(db_stores[store_id].get('user_id')) != str(user_id):
                    continue

            # Get status from database if available, otherwise from k8s
            if store_id in db_stores:
                status = db_stores[store_id].get('status', 'unknown')
            else:
                status = self.k8s.get_namespace_status(ns)

            store_data = {
                "id": store_id,
                "namespace": ns,
                "url": f"http://store-{store_id}.local",
                "status": status,
            }

            # Enrich with DB data
            if store_id in db_stores:
                store_data['owner'] = db_stores[store_id]['username']
                store_data['storage_gi'] = db_stores[store_id]['storage_size_gi']

            stores.append(store_data)

        return stores
    
    def delete_store(self, store_id, user_id=None):
        """Delete a store"""
        # Ownership check
        if user_id:
            db_stores = database.get_all_stores_with_users()
            if store_id in db_stores:
                store_owner_id = db_stores[store_id].get('user_id')
                # Allow if user matches OR if user is admin (assuming admin has id=1 or specific role, simple check for now)
                # For now strict ownership:
                if str(store_owner_id) != str(user_id):
                     return {"error": "Unauthorized: You do not own this store"}

        namespace = f"store-{store_id}"
        
        if not self.k8s.namespace_exists(namespace):
            return {"error": "Store not found"}
        
        print(f"\n=== Deleting store: {store_id} ===")

        # Update status to "deleted" before removing
        database.update_store_status(store_id, "deleted")
        print(f"🗑️  Status: deleted")

        if self.k8s.delete_namespace(namespace):
            # Clean up DB after successful k8s deletion
            database.deregister_store(store_id)
            print(f"✅ Store deleted successfully!\n")
            return {"success": True}
        else:
            # If k8s deletion fails, keep the record with "deleted" status for troubleshooting
            return {"error": "Failed to delete store from Kubernetes"}