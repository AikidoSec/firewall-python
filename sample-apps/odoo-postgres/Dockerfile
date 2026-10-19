ARG ODOO_IMAGE=odoo:16.0@sha256:0f36a5002a200bb1649771c2cb9403ca5392d7ac4bb23f9ad500b339df3f5a3a
FROM ${ODOO_IMAGE}

USER root

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY dist/*.whl /tmp/aikido-zen/
RUN python3 -m pip install --no-cache-dir /tmp/aikido-zen/*.whl \
    && rm -rf /tmp/aikido-zen

COPY sample-apps/odoo-postgres/config/odoo.conf /etc/odoo/odoo.conf
COPY --chown=odoo:odoo sample-apps/odoo-postgres/addons/ /mnt/extra-addons/
COPY sample-apps/odoo-postgres/scripts/initialize-database.sh /usr/local/bin/initialize-odoo-database
RUN chmod +x /usr/local/bin/initialize-odoo-database

USER odoo
