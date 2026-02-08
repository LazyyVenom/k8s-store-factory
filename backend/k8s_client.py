from kubernetes import client, config
from kubernetes.client.rest import ApiException
import os

class K8sClient:
    def __init__(self):
        """Initialize Kubernetes client - works both in-cluster and locally"""
        try:
            # Try in-cluster config first (when running in K8s)
            config.load_incluster_config()
            print("Using in-cluster config")
        except:
            # Fall back to local kubeconfig (for development)
            config.load_kube_config()
            print("Using local kubeconfig")
        
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.networking_v1 = client.NetworkingV1Api()
    
    def create_namespace(self, name):
        """Create a namespace"""
        namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(
                name=name,
                labels={
                    "app": "store",
                    "managed-by": "store-platform"
                }
            )
        )
        try:
            self.core_v1.create_namespace(namespace)
            print(f"✓ Created namespace: {name}")
            return True
        except ApiException as e:
            if e.status == 409:  # Already exists
                print(f"⚠ Namespace {name} already exists")
                return True
            print(f"✗ Error creating namespace: {e}")
            return False
    
    def delete_namespace(self, name):
        """Delete a namespace and all its resources"""
        try:
            self.core_v1.delete_namespace(name)
            print(f"✓ Deleted namespace: {name}")
            return True
        except ApiException as e:
            print(f"✗ Error deleting namespace: {e}")
            return False
    
    def namespace_exists(self, name):
        """Check if namespace exists"""
        try:
            self.core_v1.read_namespace(name)
            return True
        except ApiException:
            return False
    
    def get_namespace_status(self, name):
        """Get status of pods in namespace"""
        try:
            pods = self.core_v1.list_namespaced_pod(name)
            
            total = len(pods.items)
            ready = sum(1 for pod in pods.items 
                       if pod.status.phase == "Running" and
                       all(c.ready for c in pod.status.container_statuses or []))
            
            if total == 0:
                return "provisioning"
            elif ready == total:
                return "ready"
            elif any(pod.status.phase == "Failed" for pod in pods.items):
                return "failed"
            else:
                return "provisioning"
        except ApiException:
            return "unknown"
    
    def create_secret(self, namespace, secret_spec):
        """Create a secret"""
        try:
            self.core_v1.create_namespaced_secret(namespace, secret_spec)
            print(f"✓ Created secret: {secret_spec.metadata.name}")
            return True
        except ApiException as e:
            if e.status == 409:
                print(f"⚠ Secret {secret_spec.metadata.name} already exists")
                return True
            print(f"✗ Error creating secret: {e}")
            return False
    
    def create_statefulset(self, namespace, statefulset_spec):
        """Create a StatefulSet"""
        try:
            self.apps_v1.create_namespaced_stateful_set(namespace, statefulset_spec)
            print(f"✓ Created StatefulSet: {statefulset_spec.metadata.name}")
            return True
        except ApiException as e:
            if e.status == 409:
                print(f"⚠ StatefulSet already exists")
                return True
            print(f"✗ Error creating StatefulSet: {e}")
            return False
    
    def create_deployment(self, namespace, deployment_spec):
        """Create a Deployment"""
        try:
            self.apps_v1.create_namespaced_deployment(namespace, deployment_spec)
            print(f"✓ Created Deployment: {deployment_spec.metadata.name}")
            return True
        except ApiException as e:
            if e.status == 409:
                print(f"⚠ Deployment already exists")
                return True
            print(f"✗ Error creating Deployment: {e}")
            return False
    
    def create_service(self, namespace, service_spec):
        """Create a Service"""
        try:
            self.core_v1.create_namespaced_service(namespace, service_spec)
            print(f"✓ Created Service: {service_spec.metadata.name}")
            return True
        except ApiException as e:
            if e.status == 409:
                print(f"⚠ Service already exists")
                return True
            print(f"✗ Error creating Service: {e}")
            return False
    
    def create_ingress(self, namespace, ingress_spec):
        """Create an Ingress"""
        try:
            self.networking_v1.create_namespaced_ingress(namespace, ingress_spec)
            print(f"✓ Created Ingress: {ingress_spec.metadata.name}")
            return True
        except ApiException as e:
            if e.status == 409:
                print(f"⚠ Ingress already exists")
                return True
            print(f"✗ Error creating Ingress: {e}")
            return False
    
    def create_configmap(self, namespace, configmap_spec):
        """Create a ConfigMap"""
        try:
            self.core_v1.create_namespaced_config_map(namespace, configmap_spec)
            print(f"✓ Created ConfigMap: {configmap_spec.metadata.name}")
            return True
        except ApiException as e:
            if e.status == 409:
                print(f"⚠ ConfigMap already exists")
                return True
            print(f"✗ Error creating ConfigMap: {e}")
            return False
    
    def create_pvc(self, namespace, pvc_spec):
        """Create a PersistentVolumeClaim"""
        try:
            self.core_v1.create_namespaced_persistent_volume_claim(namespace, pvc_spec)
            print(f"✓ Created PVC: {pvc_spec.metadata.name}")
            return True
        except ApiException as e:
            if e.status == 409:
                print(f"⚠ PVC already exists")
                return True
            print(f"✗ Error creating PVC: {e}")
            return False
    
    def list_store_namespaces(self):
        """List all store namespaces"""
        try:
            namespaces = self.core_v1.list_namespace(
                label_selector="app=store,managed-by=store-platform"
            )
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as e:
            print(f"✗ Error listing namespaces: {e}")
            return []