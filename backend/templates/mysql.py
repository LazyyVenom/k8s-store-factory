import os
import jinja2
import yaml
from kubernetes.client.models import V1Secret, V1Service, V1StatefulSet, V1ObjectMeta

template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

def get_mysql_secret(store_id, db_password):
    template = env.get_template('mysql-secret.yaml.j2')
    rendered = template.render(
        mysql_secret_name=f'mysql-secret-{store_id}',
        namespace=f'store-{store_id}',
        mysql_root_password=db_password,
        mysql_database='wordpress',
        mysql_user='wordpress',
        mysql_password=db_password
    )
    d = yaml.safe_load(rendered)
    return V1Secret(metadata=V1ObjectMeta(**d['metadata']), type=d.get('type'), string_data=d.get('stringData'))

def get_mysql_service(store_id):
    template = env.get_template('mysql-service.yaml.j2')
    rendered = template.render(
        mysql_service_name=f'mysql-{store_id}',
        namespace=f'store-{store_id}'
    )
    d = yaml.safe_load(rendered)
    return V1Service(metadata=V1ObjectMeta(**d['metadata']), spec=d['spec'])

def get_mysql_statefulset(store_id):
    template = env.get_template('mysql-statefulset.yaml.j2')
    rendered = template.render(
        mysql_statefulset_name=f'mysql-{store_id}',
        namespace=f'store-{store_id}',
        mysql_replicas=1,
        mysql_service_name=f'mysql-{store_id}',
        mysql_image='mysql:8.0',
        mysql_secret_name=f'mysql-secret-{store_id}',
        mysql_storage_size='1Gi'
    )
    d = yaml.safe_load(rendered)
    return V1StatefulSet(metadata=V1ObjectMeta(**d['metadata']), spec=d['spec'])