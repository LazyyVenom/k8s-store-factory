from kubernetes import client

def get_wordpress_config(store_id, db_password, store_url, sample_products):
    namespace = f"store-{store_id}"
    return client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name="wordpress-config",
            namespace=namespace
        ),
        data={
            "WP_ADMIN_USER": "admin",
            "WP_ADMIN_PASSWORD": db_password,
            "WP_ADMIN_EMAIL": "admin@example.com",
            # Use manual-k8s values for defaults but allow override if needed? 
            # Manual has "My WooCommerce Store"
            "WP_SITE_TITLE": "My WooCommerce Store",
            "WP_SITE_URL": f"http://{store_url}", # Parameterized as requested

            "WC_STORE_NAME": "My Awesome Store",
            "WC_STORE_ADDRESS": "123 MG Road",
            "WC_STORE_CITY": "Mumbai",
            "WC_STORE_POSTCODE": "400001",
            "WC_STORE_COUNTRY": "IN",
            "WC_STORE_CURRENCY": "INR",
            
            "SAMPLE_PRODUCTS": sample_products
        }
    )

def get_wordpress_pvc(store_id, storage_size_gi=2):
    namespace = f"store-{store_id}"
    return client.V1PersistentVolumeClaim(
        metadata=client.V1ObjectMeta(
            name="wordpress-pvc",
            namespace=namespace
        ),
        spec=client.V1PersistentVolumeClaimSpec(
            access_modes=["ReadWriteOnce"],
            resources=client.V1ResourceRequirements(
                requests={
                    "storage": f"{storage_size_gi}Gi"
                }
            )
        )
    )

def get_wp_setup_script(store_id, db_password, store_url, sample_products):
    namespace = f"store-{store_id}"
    script_content = r"""#!/bin/bash
set -e

echo "=== WooCommerce Compact Layout Script ==="

# 1. Wait for DB
until nc -z ${WORDPRESS_DB_HOST%:*} ${WORDPRESS_DB_HOST#*:} 2>/dev/null; do sleep 3; done
sleep 5

# 2. Core Setup
if [ ! -f /var/www/html/wp-config.php ]; then
  wp core download --allow-root --force --skip-content
  wp config create --dbname="${WORDPRESS_DB_NAME}" --dbuser="${WORDPRESS_DB_USER}" --dbpass="${WORDPRESS_DB_PASSWORD}" --dbhost="${WORDPRESS_DB_HOST}" --allow-root
  wp core install --url="${WP_SITE_URL}" --title="${WC_STORE_NAME}" --admin_user="${WP_ADMIN_USER}" --admin_password="${WP_ADMIN_PASSWORD}" --admin_email="${WP_ADMIN_EMAIL}" --skip-email --allow-root
fi

# 3. Theme & Plugins
wp theme install storefront --activate --allow-root --force
wp plugin install woocommerce --activate --allow-root --force

# 4. --- CLEANUP & STYLING ---

# A. Delete Sample Page
wp post delete $(wp post list --post_type=page --name='sample-page' --format=ids --allow-root) --force --allow-root 2>/dev/null || true

# B. Minimalist Menu (Home, Cart, Checkout)
if wp menu list --fields=name --format=csv --allow-root | grep -q "Primary Menu"; then
  wp menu delete "Primary Menu" --allow-root
fi
wp menu create "Primary Menu" --allow-root
wp menu location assign "Primary Menu" primary --allow-root

SHOP_ID=$(wp post list --post_type=page --name='shop' --format=ids --allow-root | head -n 1)
CART_ID=$(wp post list --post_type=page --name='cart' --format=ids --allow-root | head -n 1)
CHECK_ID=$(wp post list --post_type=page --name='checkout' --format=ids --allow-root | head -n 1)

if [ -n "$SHOP_ID" ]; then wp menu item add-post "Primary Menu" $SHOP_ID --title="Home" --allow-root; fi
if [ -n "$CART_ID" ]; then wp menu item add-post "Primary Menu" $CART_ID --title="Cart" --allow-root; fi
if [ -n "$CHECK_ID" ]; then wp menu item add-post "Primary Menu" $CHECK_ID --title="Checkout" --allow-root; fi

# C. Remove Widgets
wp widget reset sidebar-1 --allow-root

# D. Inject CSS (Compact Layout Fix)
wp eval '
  $css = "
  /* 1. Hide Elements */
  .woocommerce-products-header__title.page-title,
  .woocommerce-ordering, 
  .woocommerce-result-count,
  .site-search,
  .woocommerce-breadcrumb,
  .storefront-breadcrumb { display: none !important; }

  /* 2. Remove Header Spacing */
  .site-header { padding-bottom: 0 !important; margin-bottom: 10px !important; }
  
  /* 3. Remove Main Content Top/Bottom Spacing */
  .site-content { padding-top: 10px !important; padding-bottom: 0 !important; }
  .storefront-full-width-content .site-main { margin-bottom: 0 !important; padding-bottom: 0 !important; }
  
  /* 4. Remove Product Grid Spacing */
  ul.products { margin-top: 0 !important; padding-top: 0 !important; margin-bottom: 20px !important; }
  
  /* 5. Force Full Width */
  .right-sidebar .content-area { width: 100% !important; float: none !important; }
  ";
  wp_update_custom_css_post($css);
' --allow-root

# 5. Settings & Products
if ! wp post list --post_type=page --name=shop --format=ids --allow-root | grep -q .; then
   wp wc tool run install_pages --user="${WP_ADMIN_USER}" --allow-root
fi
SHOP_ID=$(wp post list --post_type=page --name=shop --format=ids --allow-root | head -n 1)
if [ -n "$SHOP_ID" ]; then
  wp option update show_on_front 'page' --allow-root
  wp option update page_on_front $SHOP_ID --allow-root
fi

wp option update woocommerce_currency "${WC_STORE_CURRENCY}" --allow-root
wp option update woocommerce_cod_settings '{"enabled":"yes","title":"Cash on Delivery","description":"Pay upon delivery."}' --format=json --allow-root

echo "Refreshing Products..."
while IFS='|' read -r name price description; do
  if [ -n "$name" ] && [ "$name" != " " ]; then
    name=$(echo "$name" | xargs)
    price=$(echo "$price" | xargs)
    desc=$(echo "$description" | xargs)
    SLUG=$(echo "$name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
    
    if ! wp post list --post_type=product --name="$SLUG" --format=ids --allow-root | grep -q .; then
      echo "Adding: $name"
      wp wc product create --name="$name" --type=simple --regular_price="$price" --description="$desc" --status=publish --user="${WP_ADMIN_USER}" --allow-root
    fi
  fi
done <<< "$SAMPLE_PRODUCTS"

echo "=== SETUP COMPLETE ==="
"""
    return client.V1ConfigMap(
        metadata=client.V1ObjectMeta(
            name="wp-setup-script",
            namespace=namespace
        ),
        data={
            "wp-setup.sh": script_content
        }
    )

def get_wordpress_deployment(store_id, db_password, store_url):
    namespace = f"store-{store_id}"
    return client.V1Deployment(
        metadata=client.V1ObjectMeta(
            name="wordpress",
            namespace=namespace,
            labels={
                "app": "wordpress"
            }
        ),
        spec=client.V1DeploymentSpec(
            replicas=1,
            selector=client.V1LabelSelector(
                match_labels={
                    "app": "wordpress"
                }
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={
                        "app": "wordpress"
                    }
                ),
                spec=client.V1PodSpec(
                    init_containers=[
                        client.V1Container(
                            name="wp-init",
                            image="wordpress:cli-php8.1",
                            command=[
                                "/bin/bash",
                                "-c",
                                "mkdir -p /tmp/conf.d\n"
                                "echo \"memory_limit = 512M\" > /tmp/conf.d/custom.ini\n"
                                "export PHP_INI_SCAN_DIR=:$PHP_INI_SCAN_DIR:/tmp/conf.d\n\n"
                                "# --- FIX: Filter Logs ---\n"
                                "# We redirect stderr to stdout (2>&1) and filter out the noisy warnings\n"
                                "/scripts/wp-setup.sh 2>&1 | grep -v \"already loaded\""
                            ],
                            env_from=[
                                client.V1EnvFromSource(
                                    config_map_ref=client.V1ConfigMapEnvSource(
                                        name="wordpress-config"
                                    )
                                )
                            ],
                            env=[
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_HOST",
                                    value="mysql:3306"
                                ),
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_NAME",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-database"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_USER",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-user"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_PASSWORD",
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
                                    name="wordpress-storage",
                                    mount_path="/var/www/html"
                                ),
                                client.V1VolumeMount(
                                    name="setup-script",
                                    mount_path="/scripts"
                                )
                            ]
                        )
                    ],
                    containers=[
                        client.V1Container(
                            name="wordpress",
                            image="wordpress:latest",
                            ports=[
                                client.V1ContainerPort(
                                    container_port=80,
                                    name="http"
                                )
                            ],
                            env=[
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_HOST",
                                    value="mysql:3306"
                                ),
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_NAME",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-database"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_USER",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-user"
                                        )
                                    )
                                ),
                                client.V1EnvVar(
                                    name="WORDPRESS_DB_PASSWORD",
                                    value_from=client.V1EnvVarSource(
                                        secret_key_ref=client.V1SecretKeySelector(
                                            name="mysql-secret",
                                            key="mysql-password"
                                        )
                                    )
                                )
                            ],
                            env_from=[
                                client.V1EnvFromSource(
                                    config_map_ref=client.V1ConfigMapEnvSource(
                                        name="wordpress-config"
                                    )
                                )
                            ],
                            volume_mounts=[
                                client.V1VolumeMount(
                                    name="wordpress-storage",
                                    mount_path="/var/www/html"
                                )
                            ]
                        )
                    ],
                    volumes=[
                        client.V1Volume(
                            name="wordpress-storage",
                            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                claim_name="wordpress-pvc"
                            )
                        ),
                        client.V1Volume(
                            name="setup-script",
                            config_map=client.V1ConfigMapVolumeSource(
                                name="wp-setup-script",
                                default_mode=0o755
                            )
                        )
                    ]
                )
            )
        )
    )

def get_wordpress_service(store_id):
    namespace = f"store-{store_id}"
    return client.V1Service(
        metadata=client.V1ObjectMeta(
            name="wordpress",
            namespace=namespace,
            labels={
                "app": "wordpress"
            }
        ),
        spec=client.V1ServiceSpec(
            selector={
                "app": "wordpress"
            },
            ports=[
                client.V1ServicePort(
                    port=80,
                    target_port=80,
                    protocol="TCP",
                    name="http"
                )
            ],
            type="ClusterIP"
        )
    )
