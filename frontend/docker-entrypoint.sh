#!/bin/sh
# Generate runtime config from environment variables
# This runs when the container starts

cat > /usr/share/nginx/html/config.js << EOF
window.ENV = {
  VITE_API_URL: "${VITE_API_URL}"
};
EOF

echo "Runtime config generated:"
cat /usr/share/nginx/html/config.js

# Start nginx
exec nginx -g 'daemon off;'
