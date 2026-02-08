import os
import jinja2
import yaml
from kubernetes.client.models import V1Ingress, V1ObjectMeta

template_dir = os.path.join(os.path.dirname(__file__), '..', 'templates')
env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir))

def get_ingress(store_id, store_url):
    template = env.get_template('ingress.yaml.j2')
    rendered = template.render(
        ingress_name=f'ingress-{store_id}',
        namespace=f'store-{store_id}',
        host=store_url,
        wordpress_service_name=f'wordpress-{store_id}',
        wordpress_port=80
    )
    d = yaml.safe_load(rendered)
    return V1Ingress(metadata=V1ObjectMeta(**d['metadata']), spec=d['spec'])