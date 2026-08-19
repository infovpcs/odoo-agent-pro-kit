ARG ODOO_BASE_IMAGE=odoo:18.0
FROM ${ODOO_BASE_IMAGE}

USER root
COPY --chmod=0755 sandbox/scripts/odoo-healthcheck.sh /usr/local/bin/odoo-healthcheck
RUN wkhtmltopdf --version | grep -Eq '0\.12\.6.*patched qt' \
    && wkhtmltoimage --version | grep -Eq '0\.12\.6.*patched qt'
USER odoo

HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=18 \
  CMD ["/usr/local/bin/odoo-healthcheck"]
