FROM odoo:16.0

USER root

# Install system dependencies for MySQL client and Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir \
    mysqlclient \
    requests \
    sentry-sdk

# Copy custom addons from the correct path
COPY ./sample-apps/odoo-mysql/addons /mnt/extra-addons

# Copy Odoo configuration
COPY ./sample-apps/odoo-mysql/odoo.conf /etc/odoo/

# Copy entrypoint script
COPY ./sample-apps/odoo-mysql/entrypoint.sh /usr/local/bin/aikido-entrypoint.sh
RUN chmod +x /usr/local/bin/aikido-entrypoint.sh

USER odoo

# Initialize Aikido protection environment variables
ENV AIKIDO_DEBUG=true \
    AIKIDO_BLOCK=true \
    AIKIDO_TOKEN="AIK_secret_token" \
    AIKIDO_REALTIME_ENDPOINT="http://localhost:5000/" \
    AIKIDO_ENDPOINT="http://localhost:5000/" \
    AIKIDO_DISABLE=0

# Use custom entrypoint that initializes Aikido
ENTRYPOINT ["/usr/local/bin/aikido-entrypoint.sh"]
CMD ["odoo"]
