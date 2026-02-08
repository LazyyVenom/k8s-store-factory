import secrets
import time
from k8s_client import K8sClient
from templates.mysql import get_mysql_secret, get_mysql_service, get_mysql_statefulset
from templates.wordpress import get_wordpress_config, get_wordpress_pvc, get_wp_setup_script, get_wordpress_deployment, get_wordpress_service
from templates.ingress import get_ingress

class StoreManager:
    def __init__(self):
        self.k8s = K8sClient()
    
    def generate_store_id(self):
        """Generate unique store ID"""
        return secrets.token_hex(4)
    
    def create_store(self, sample_products=None, store_url_suffix=None):
        """Create a new store"""
        store_id = self.generate_store_id()
        namespace = f"store-{store_id}"
        if store_url_suffix:
            store_url = f"store-{store_id}.{store_url_suffix}"
        else:
            store_url = f"store-{store_id}.local"
        db_password = secrets.token_urlsafe(16)
        if sample_products is None:
            sample_products = "Sample Product 1|10.00|This is a sample product\nSample Product 2|20.00|Another sample product"
        
        print(f"\n=== Creating store: {store_id} ===")
        
        # Create namespace
        if not self.k8s.create_namespace(namespace):
            return {"error": "Failed to create namespace"}
        
        # Create MySQL secret
        mysql_secret = get_mysql_secret(store_id, db_password)
        if not self.k8s.create_secret(namespace, mysql_secret):
            return {"error": "Failed to create MySQL secret"}
        
        # Create MySQL service
        mysql_svc = get_mysql_service(store_id)
        if not self.k8s.create_service(namespace, mysql_svc):
            return {"error": "Failed to create MySQL service"}
        
        # Create MySQL StatefulSet
        mysql_ss = get_mysql_statefulset(store_id)
        if not self.k8s.create_statefulset(namespace, mysql_ss):
            return {"error": "Failed to create MySQL"}
        
        # Wait for MySQL to be ready
        print("⏳ Waiting for MySQL to be ready...")
        time.sleep(30)  # Simple wait; improve with actual pod checking
        
        # Create WordPress ConfigMap
        wp_config = get_wordpress_config(store_id, db_password, store_url, sample_products)
        if not self.k8s.create_configmap(namespace, wp_config):
            return {"error": "Failed to create WordPress config"}
        
        # Create WordPress PVC
        wp_pvc = get_wordpress_pvc(store_id)
        if not self.k8s.create_pvc(namespace, wp_pvc):
            return {"error": "Failed to create WordPress PVC"}
        
        # Create WP Setup Script ConfigMap
        wp_setup = get_wp_setup_script(store_id, db_password, store_url, sample_products)
        if not self.k8s.create_configmap(namespace, wp_setup):
            return {"error": "Failed to create WP setup script"}
        
        # Create WordPress Deployment
        wp_deployment = get_wordpress_deployment(store_id, db_password, store_url)
        if not self.k8s.create_deployment(namespace, wp_deployment):
            return {"error": "Failed to create WordPress"}
        
        # Create WordPress Service
        wp_service = get_wordpress_service(store_id)
        if not self.k8s.create_service(namespace, wp_service):
            return {"error": "Failed to create WordPress service"}
        
        # Create Ingress
        ingress = get_ingress(store_id, store_url)
        if not self.k8s.create_ingress(namespace, ingress):
            return {"error": "Failed to create Ingress"}
        
        print(f"✅ Store created successfully!\n")
        
        return {
            "id": store_id,
            "namespace": namespace,
            "url": f"http://{store_url}",
            "admin_url": f"http://{store_url}/wp-admin",
            "admin_user": "admin",
            "admin_password": db_password,
            "status": "provisioning",
            "created_at": time.time()
        }
    
    def list_stores(self):
        """List all stores"""
        namespaces = self.k8s.list_store_namespaces()
        stores = []
        
        for ns in namespaces:
            store_id = ns.replace("store-", "")
            status = self.k8s.get_namespace_status(ns)
            
            stores.append({
                "id": store_id,
                "namespace": ns,
                "url": f"http://store-{store_id}.local",
                "status": status
            })
        
        return stores
    
    def delete_store(self, store_id):
        """Delete a store"""
        namespace = f"store-{store_id}"
        
        if not self.k8s.namespace_exists(namespace):
            return {"error": "Store not found"}
        
        print(f"\n=== Deleting store: {store_id} ===")
        
        if self.k8s.delete_namespace(namespace):
            print(f"✅ Store deleted successfully!\n")
            return {"success": True}
        else:
            return {"error": "Failed to delete store"}