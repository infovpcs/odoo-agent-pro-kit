# Per-session PyPI requirements on top of the pinned Odoo dev image (sandboxctl create --requirements).
# The build context holds only the validated requirements.txt and constraints.txt (the exact pins of a
# replayed results/requirements-freeze.txt, or empty).
# pip's default 15 s read timeout with 5 retries turned slow PyPI answers into ResolutionImpossible
# (Phase 11 finding 7), so the build waits longer and retries more.
# A --system-site-packages venv (using the image's own pip) keeps every Debian package that already
# satisfies the requirements and installs only what is missing or too old; PYTHONPATH puts that
# small overlay in front of the Debian copies. pip freeze of the overlay is kept for the record,
# and the build fails if the overlay breaks Odoo's own imports (e.g. a cryptography upgrade that
# the Debian pyOpenSSL cannot load).
ARG ODOO_DEV_IMAGE
FROM ${ODOO_DEV_IMAGE}

USER root
# Build args are environment variables for RUN only; they are not kept in the image.
ARG PIP_DEFAULT_TIMEOUT=60
ARG PIP_RETRIES=10
COPY requirements.txt constraints.txt /tmp/
RUN mv /tmp/requirements.txt /tmp/sandbox-requirements.txt && mv /tmp/constraints.txt /tmp/sandbox-constraints.txt \
    && python3 -m venv --without-pip --system-site-packages /opt/sandbox-venv \
    && /opt/sandbox-venv/bin/python3 -m pip install --no-cache-dir -r /tmp/sandbox-requirements.txt -c /tmp/sandbox-constraints.txt \
    && ln -s "$(/opt/sandbox-venv/bin/python3 -c 'import sysconfig; print(sysconfig.get_path("purelib"))')" /opt/sandbox-site-packages \
    && /opt/sandbox-venv/bin/python3 -m pip freeze --path /opt/sandbox-site-packages > /opt/sandbox-requirements.freeze \
    && PYTHONPATH=/opt/sandbox-site-packages python3 -c "import odoo.addons.base.models" \
    && rm /tmp/sandbox-requirements.txt /tmp/sandbox-constraints.txt
ENV PYTHONPATH=/opt/sandbox-site-packages
USER odoo
