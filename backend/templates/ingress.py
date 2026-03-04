from kubernetes import client


def get_ingress(store_id, store_url):
    namespace = f"store-{store_id}"
    return client.V1Ingress(
        metadata=client.V1ObjectMeta(
            name="store-ingress",
            namespace=namespace,
            annotations={
                # Increase max body size for uploads
                "nginx.ingress.kubernetes.io/proxy-body-size": "50m",
                # Force HTTPS redirect (though handled by external Nginx)
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                # Tell Nginx backend is HTTP
                "nginx.ingress.kubernetes.io/backend-protocol": "HTTP",
                # Forward HTTPS headers so WordPress knows it's HTTPS
                "nginx.ingress.kubernetes.io/configuration-snippet": "proxy_set_header X-Forwarded-Proto $scheme;",
            },
        ),
        spec=client.V1IngressSpec(
            ingress_class_name="nginx",
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
                                        port=client.V1ServiceBackendPort(number=80),
                                    )
                                ),
                            )
                        ]
                    ),
                )
            ],
            # No TLS block needed because external Nginx handles SSL
        ),
    )
