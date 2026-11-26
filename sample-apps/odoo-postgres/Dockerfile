ARG ODOO_IMAGE=odoo:16.0
FROM ${ODOO_IMAGE}

USER root

# Odoo 18 and later refuse system-wide pip installs without this. Older pip ignores it.
ENV PIP_BREAK_SYSTEM_PACKAGES=1

COPY dist/*.whl /tmp/aikido-zen/
RUN python3 -m pip install --no-cache-dir /tmp/aikido-zen/*.whl \
    && rm -rf /tmp/aikido-zen

COPY sample-apps/odoo-postgres/config/odoo.conf /etc/odoo/odoo.conf
COPY --chown=odoo:odoo sample-apps/odoo-postgres/addons/ /mnt/extra-addons/
COPY sample-apps/odoo-postgres/scripts/initialize-database.sh /usr/local/bin/initialize-odoo-database
RUN chmod +x /usr/local/bin/initialize-odoo-database \
    && install --directory --owner=odoo --group=odoo /tmp/zen_files

USER odoo
