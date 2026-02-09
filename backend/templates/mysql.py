from kubernetes import client

def get_mysql_secret(store_id, password):
    namespace = f"store-{store_id}"
    return client.V1Secret(
        metadata=client.V1ObjectMeta(
            name="mysql-secret",
            namespace=namespace
        ),
        type="Opaque",
        string_data={
            "mysql-root-password": "rootpassword",
            "mysql-database": "wordpress",
            "mysql-user": "wordpress",
            "mysql-password": password
        }
    )

def get_mysql_service(store_id):
    namespace = f"store-{store_id}"
    return client.V1Service(
        metadata=client.V1ObjectMeta(
            name="mysql",
            namespace=namespace,
            labels={
                "app": "mysql"
            }
        ),
        spec=client.V1ServiceSpec(
            ports=[
                client.V1ServicePort(
                    port=3306,
                    target_port=3306,
                    protocol="TCP"
                )
            ],
            selector={
                "app": "mysql"
            },
            cluster_ip="None"
        )
    )

def get_mysql_statefulset(store_id):
    namespace = f"store-{store_id}"
    return client.V1StatefulSet(
        metadata=client.V1ObjectMeta(
            name="mysql",
            namespace=namespace
        ),
        spec=client.V1StatefulSetSpec(
            service_name="mysql",
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={
                    "app": "mysql"
                }
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": "mysql"
                    }
                ),
                spec=client.V1PodSpec(
                    containers=[
                        client.V1Container(
                            name="mysql",
                            image="mysql:8.0",
                            ports=[
                                client.V1ContainerPort(
                                    container_port=3306,
                                    name="mysql"
                                )
                            ],
                            env=[
                                client.V1EnvVar(
                                    name="MYSQL_ROOT_PASSWORD",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-root-password"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="MYSQL_DATABASE",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-database"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="MYSQL_USER",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-user"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="MYSQL_PASSWORD",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-password"
                                        )
                                    )
                                )
                            ],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="mysql-storage",
                                    mount_path="/var/lib/mysql"
                                )
                            ]
                        )
                    ]
                )
            ),
            volume_claim_templates=[
                client.V1PersistentVolumeClaim(
                    metadata=client.V1ObjectMeta(
                        name="mysql-storage"
                    ),
                    spec=client.V1PersistentVolumeClaimSpec(
                        access_modes=["ReadWriteOnce"],
                        resources=client.V1ResourceRequirements(
                            requests={
                                "storage": "2Gi"
                            }
                        )
                    )
                )
            ]
        )
    )
