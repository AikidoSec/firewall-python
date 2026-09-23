#!/bin/bash
set -e

# Initialize Aikido protection if enabled
if [ "${AIKIDO_DISABLE}" != "1" ]; then
    echo "Initializing Aikido Zen protection..."
    cat > /tmp/aikido_init.py << 'EOF'
import os
os.environ.setdefault('AIKIDO_DEBUG', 'true')
os.environ.setdefault('AIKIDO_BLOCK', 'true')

import aikido_zen
aikido_zen.protect()

# Set user context for Aikido
aikido_zen.set_user({"id": "odoo-system", "name": "Odoo System"})

print("✓ Aikido Zen protection initialized")
EOF
    export PYTHONSTARTUP=/tmp/aikido_init.py
fi

# Execute the main Odoo command
exec "$@"
