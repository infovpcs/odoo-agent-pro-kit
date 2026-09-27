# Per-session PyPI requirements on top of the pinned Odoo dev image (sandboxctl create --requirements).
# The build context holds only the validated requirements.txt.
# A --system-site-packages venv (using the image's own pip) keeps every Debian package that already
# satisfies the requirements and installs only what is missing or too old; PYTHONPATH puts that
# small overlay in front of the Debian copies. pip freeze of the overlay is kept for the record,
# and the build fails if the overlay breaks Odoo's own imports (e.g. a cryptography upgrade that
# the Debian pyOpenSSL cannot load).
ARG ODOO_DEV_IMAGE
FROM ${ODOO_DEV_IMAGE}

USER root
COPY requirements.txt /tmp/sandbox-requirements.txt
RUN python3 -m venv --without-pip --system-site-packages /opt/sandbox-venv \
    && /opt/sandbox-venv/bin/python3 -m pip install --no-cache-dir -r /tmp/sandbox-requirements.txt \
    && ln -s "$(/opt/sandbox-venv/bin/python3 -c 'import sysconfig; print(sysconfig.get_path("purelib"))')" /opt/sandbox-site-packages \
    && /opt/sandbox-venv/bin/python3 -m pip freeze --path /opt/sandbox-site-packages > /opt/sandbox-requirements.freeze \
    && PYTHONPATH=/opt/sandbox-site-packages python3 -c "import odoo.addons.base.models" \
    && rm /tmp/sandbox-requirements.txt
ENV PYTHONPATH=/opt/sandbox-site-packages
USER odoo
