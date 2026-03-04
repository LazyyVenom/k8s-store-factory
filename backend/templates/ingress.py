from kubernetes import client

def get_ingress(store_id, store_url):
    namespace = f"store-{store_id}"
    return client.V1Ingress(
        metadata=client.V1ObjectMeta(
            name="store-ingress",
            namespace=namespace,
            annotations={
                "nginx.ingress.kubernetes.io/proxy-body-size": "50m",
                "cert-manager.io/cluster-issuer": "letsencrypt-prod",
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
            }
        ),
        spec=client.V1IngressSpec(
            ingress_class_name="nginx",
            tls=[
                client.V1IngressTLS(
                    hosts=[store_url],
                    secret_name=f"store-{store_id}-tls"
                )
            ],
            rules=[
                client.V1IngressRule(
                    host=store_url,
                    http=client.V1HTTPIngressRuleValue(
                        paths=[
                            client.V1HTTPIngressPath(
                                path="/",
                                path_type="Prefix",
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name="wordpress",
                                        port=client.V1ServiceBackendPort(
                                            number=80
                                        )
                                    )
                                )
                            )
                        ]
                    )
                )
            ]
        )
    )
