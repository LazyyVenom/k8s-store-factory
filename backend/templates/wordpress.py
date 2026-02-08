import os
import jinja2
import yaml
from kubernetes.client.models import V1ConfigMap, V1PersistentVolumeClaim, V1Deployment, V1Service, V1ObjectMeta

template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

def get_wordpress_config(store_id, db_password, store_url, sample_products):
    template = env.get_template('wordpress-config.yaml.j2')
    rendered = template.render(
        wordpress_config_name=f'wordpress-config-{store_id}',
        namespace=f'store-{store_id}',
        wp_admin_user='admin',
        wp_admin_password=db_password,
        wp_admin_email='admin@example.com',
        wp_site_title=f'WooCommerce Store {store_id}',
        wp_site_url=f'http://{store_url}',
        wc_store_name=f'WooCommerce Store {store_id}',
        wc_store_address='123 Main St',
        wc_store_city='Anytown',
        wc_store_postcode='12345',
        wc_store_country='US',
        wc_store_currency='USD',
        sample_products=sample_products
    )
    d = yaml.safe_load(rendered)
    return V1ConfigMap(metadata=V1ObjectMeta(**d['metadata']), data=d.get('data'))

def get_wordpress_pvc(store_id):
    template = env.get_template('wordpress-pvc.yaml.j2')
    rendered = template.render(
        wordpress_pvc_name=f'wordpress-pvc-{store_id}',
        namespace=f'store-{store_id}',
        wordpress_storage_size='1Gi'
    )
    d = yaml.safe_load(rendered)
    return V1PersistentVolumeClaim(metadata=V1ObjectMeta(**d['metadata']), spec=d['spec'])

def get_wp_setup_script(store_id, db_password, store_url, sample_products):
    template = env.get_template('wp-setup-script.yaml.j2')
    rendered = template.render(
        wp_setup_script_name=f'wp-setup-script-{store_id}',
        namespace=f'store-{store_id}',
        wp_admin_user='admin',
        wp_admin_password=db_password,
        wp_admin_email='admin@example.com',
        wp_site_url=f'http://{store_url}',
        wc_store_name=f'WooCommerce Store {store_id}',
        wc_store_currency='USD',
        sample_products=sample_products
    )
    d = yaml.safe_load(rendered)
    return V1ConfigMap(metadata=V1ObjectMeta(**d['metadata']), data=d.get('data'))

def get_wordpress_deployment(store_id, db_password, store_url):
    template = env.get_template('wordpress-deployment.yaml.j2')
    rendered = template.render(
        wordpress_deployment_name=f'wordpress-{store_id}',
        namespace=f'store-{store_id}',
        wordpress_replicas=1,
        wordpress_cli_image='wordpress:latest',
        mysql_service_name=f'mysql-{store_id}',
        mysql_secret_name=f'mysql-secret-{store_id}',
        wordpress_config_name=f'wordpress-config-{store_id}',
        wordpress_image='wordpress:latest',
        wordpress_pvc_name=f'wordpress-pvc-{store_id}',
        wp_setup_script_name=f'wp-setup-script-{store_id}'
    )
    d = yaml.safe_load(rendered)
    return V1Deployment(metadata=V1ObjectMeta(**d['metadata']), spec=d['spec'])

def get_wordpress_service(store_id):
    template = env.get_template('wordpress-service.yaml.j2')
    rendered = template.render(
        wordpress_service_name=f'wordpress-{store_id}',
        namespace=f'store-{store_id}',
        wordpress_port=80,
        wordpress_service_type='ClusterIP'
    )
    d = yaml.safe_load(rendered)
    return V1Service(metadata=V1ObjectMeta(**d['metadata']), spec=d['spec'])