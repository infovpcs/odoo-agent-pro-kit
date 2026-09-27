# Odoo 20.0 dev image.
#
# Docker Hub has no official odoo:20.0 image yet, so the first part reproduces the official
# recipe from odoo/docker commit d54316042067a95e28d8ef64280d41c2182d3804 (20.0/Dockerfile,
# 2026-09-26) with its sha1 checks, on the ubuntu:noble digest pinned as
# ODOO_20_BASE in sandbox/config/images.lock. Its three helper files are fetched from the same
# commit and checked by sha256. One deviation: the pgdg signing key is fetched over HTTPS and
# fingerprint-checked (see that step). When Hub publishes odoo:20.0, pin that digest as ODOO_20_BASE
# and reduce this file to the dev layer at the bottom, like 17/18/19.
ARG ODOO_BASE_IMAGE=ubuntu:noble
FROM ${ODOO_BASE_IMAGE}
LABEL maintainer="Odoo S.A. <info@odoo.com>"

SHELL ["/bin/bash", "-xo", "pipefail", "-c"]

# Generate locale C.UTF-8 for postgres and general locale data
ENV LANG=en_US.UTF-8

# Retrieve the target architecture to install the correct wkhtmltopdf package
ARG TARGETARCH

# Install some deps, lessc and less-plugin-clean-css, and wkhtmltopdf

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        dirmngr \
        fonts-noto-cjk \
        gnupg \
        libssl-dev \
        node-less \
        python3-magic \
        python3-num2words \
        python3-odf \
        python3-pdfminer \
        python3-pip \
        python3-phonenumbers \
        python3-pyldap \
        python3-qrcode \
        python3-renderpm \
        python3-setuptools \
        python3-slugify \
        python3-vobject \
        python3-watchdog \
        python3-xlrd \
        python3-xlwt \
        xz-utils && \
    if [ -z "${TARGETARCH}" ]; then \
        TARGETARCH="$(dpkg --print-architecture)"; \
    fi; \
    WKHTMLTOPDF_ARCH=${TARGETARCH} && \
    case ${TARGETARCH} in \
    "amd64") WKHTMLTOPDF_ARCH=amd64 && WKHTMLTOPDF_SHA=967390a759707337b46d1c02452e2bb6b2dc6d59  ;; \
    "arm64")  WKHTMLTOPDF_SHA=90f6e69896d51ef77339d3f3a20f8582bdf496cc  ;; \
    "ppc64le" | "ppc64el") WKHTMLTOPDF_ARCH=ppc64el && WKHTMLTOPDF_SHA=5312d7d34a25b321282929df82e3574319aed25c  ;; \
    esac \
    && curl -o wkhtmltox.deb -sSL https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.jammy_${WKHTMLTOPDF_ARCH}.deb \
    && echo ${WKHTMLTOPDF_SHA} wkhtmltox.deb | sha1sum -c - \
    && apt-get install -y --no-install-recommends ./wkhtmltox.deb \
    && rm -rf /var/lib/apt/lists/* wkhtmltox.deb

# install latest postgresql-client
# Deviation from upstream: the key comes from the same keyserver over HTTPS with curl instead of
# `gpg --recv-keys` (dirmngr fails inside Docker Sandbox microVMs, which intercept only 80/443),
# and the build fails unless its primary fingerprint equals the upstream full-fingerprint pin.
RUN echo 'deb http://apt.postgresql.org/pub/repos/apt/ noble-pgdg main' > /etc/apt/sources.list.d/pgdg.list \
    && GNUPGHOME="$(mktemp -d)" \
    && export GNUPGHOME \
    && repokey='B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8' \
    && curl -fsSL -o /tmp/pgdg.asc "https://keyserver.ubuntu.com/pks/lookup?op=get&options=mr&search=0x${repokey}" \
    && test "$(gpg --batch --with-colons --import-options show-only --import /tmp/pgdg.asc | awk -F: '$1 == "fpr" {print $10; exit}')" = "${repokey}" \
    && gpg --batch --import /tmp/pgdg.asc \
    && rm -f /tmp/pgdg.asc \
    && gpg --batch --armor --export "${repokey}" > /etc/apt/trusted.gpg.d/pgdg.gpg.asc \
    && gpgconf --kill all \
    && rm -rf "$GNUPGHOME" \
    && apt-get update  \
    && apt-get install --no-install-recommends -y postgresql-client \
    && rm -f /etc/apt/sources.list.d/pgdg.list \
    && rm -rf /var/lib/apt/lists/*

# Install rtlcss (on Debian buster)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nodejs npm \
    && npm install -g rtlcss \
    && apt-get purge --autoremove -y npm \
    && rm -rf /var/lib/apt/lists/*

# Install Odoo
ENV ODOO_VERSION=20.0
ARG ODOO_RELEASE=20260926
ARG ODOO_SHA=7cb4a582ebe275a4f9c22eae24ce2bcb7fa27040
RUN curl -o odoo.deb -sSL http://nightly.odoo.com/${ODOO_VERSION}/nightly/deb/odoo_${ODOO_VERSION}.${ODOO_RELEASE}_all.deb \
    && echo "${ODOO_SHA} odoo.deb" | sha1sum -c - \
    && apt-get update \
    && apt-get -y install --no-install-recommends ./odoo.deb \
    && rm -rf /var/lib/apt/lists/* odoo.deb

# Copy entrypoint script and Odoo configuration file
ADD --chmod=0755 --checksum=sha256:18ea7deeebfb22ea625c72b45f84ff3356644443f89942f1a82cb73a8f10c205 https://raw.githubusercontent.com/odoo/docker/d54316042067a95e28d8ef64280d41c2182d3804/20.0/entrypoint.sh /entrypoint.sh
ADD --chmod=0644 --checksum=sha256:4d772957164d15f1c5c13d5b0e11be0b0ee54b1d1e9068487db403a5b51c7b32 https://raw.githubusercontent.com/odoo/docker/d54316042067a95e28d8ef64280d41c2182d3804/20.0/odoo.conf /etc/odoo/odoo.conf

# Set permissions and Mount /var/lib/odoo to allow restoring filestore and /mnt/extra-addons for users addons
RUN chown odoo /etc/odoo/odoo.conf \
    && mkdir -p /mnt/extra-addons \
    && chown -R odoo /mnt/extra-addons
VOLUME ["/var/lib/odoo", "/mnt/extra-addons"]

# Expose Odoo services
EXPOSE 8069 8071 8072

# Set the default config file
ENV ODOO_RC=/etc/odoo/odoo.conf

ADD --chmod=0755 --checksum=sha256:69d21ecbd9ac92d149f7d3edacfddf05f44ddb83d07590940fdf83b95d7679ab https://raw.githubusercontent.com/odoo/docker/d54316042067a95e28d8ef64280d41c2182d3804/20.0/wait-for-psql.py /usr/local/bin/wait-for-psql.py

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]

# --- Sandbox dev layer (same as 17/18/19) ---
COPY --chmod=0755 sandbox/scripts/odoo-healthcheck.sh /usr/local/bin/odoo-healthcheck
RUN wkhtmltopdf --version | grep -Eq '0\.12\.6.*patched qt' \
    && wkhtmltoimage --version | grep -Eq '0\.12\.6.*patched qt'
USER odoo

HEALTHCHECK --interval=5s --timeout=3s --start-period=20s --retries=18 \
  CMD ["/usr/local/bin/odoo-healthcheck"]
