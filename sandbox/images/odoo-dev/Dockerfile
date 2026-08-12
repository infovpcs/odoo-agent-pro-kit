ARG ODOO_BASE_IMAGE=odoo:19.0
FROM ${ODOO_BASE_IMAGE}

USER root
COPY sandbox/scripts/odoo-healthcheck.sh /usr/local/bin/odoo-healthcheck
RUN chmod 0755 /usr/local/bin/odoo-healthcheck \
    && mkdir -p /var/lib/odoo/.cache /var/log/odoo /var/lib/odoo/results \
    && chown -R odoo:odoo /var/lib/odoo /var/log/odoo
USER odoo

HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=18 \
  CMD ["/usr/local/bin/odoo-healthcheck"]
