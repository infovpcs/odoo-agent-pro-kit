#!/bin/bash
set -euo pipefail

# Multi-version Odoo bootstrap (12-20)
# Usage: ./bootstrap_odoo_env.sh --base-dir /opt/odoo --versions 12,13,14,15,16,17,18,19,20

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BASE_DIR="$(pwd)"
VERSIONS="17,18,19"
DB_USER="${DB_USER:-odoo}"
DB_PASSWORD="${DB_PASSWORD:-odoo}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
ADMIN_PASSWD="admin"
EXTRA_ADDONS=""
ODOO_REPO_URL="${ODOO_REPO_URL:-https://github.com/odoo/odoo.git}"
FORCE=0
SKIP_DEPS=0
SKIP_DB=0

usage() {
  cat <<USAGE
Usage: $0 [options]

Options:
  --base-dir PATH         Base directory for workspaces (default: cwd)
  --versions LIST         Comma list: 12-20 (default: 17,18,19)
  --db-user USER          PostgreSQL user (default: odoo)
  --db-password PASS      PostgreSQL password (default: odoo)
  --db-host HOST          PostgreSQL host (default: localhost)
  --db-port PORT          PostgreSQL port (default: 5432)
  --admin-passwd PASS     Odoo admin password (default: admin)
  --extra-addons PATHS    Extra addons paths (comma-separated)
  --odoo-repo-url URL     Odoo Git remote (default: ODOO_REPO_URL or GitHub)
  --force                 Recreate venv/config when present
  --skip-deps             Skip apt dependency install
  --skip-db               Skip PostgreSQL user/db setup
  -h, --help              Show help
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-dir) BASE_DIR="$2"; shift 2;;
    --versions) VERSIONS="$2"; shift 2;;
    --db-user) DB_USER="$2"; shift 2;;
    --db-password) DB_PASSWORD="$2"; shift 2;;
    --db-host) DB_HOST="$2"; shift 2;;
    --db-port) DB_PORT="$2"; shift 2;;
    --admin-passwd) ADMIN_PASSWD="$2"; shift 2;;
    --extra-addons) EXTRA_ADDONS="$2"; shift 2;;
    --odoo-repo-url) ODOO_REPO_URL="$2"; shift 2;;
    --force) FORCE=1; shift;;
    --skip-deps) SKIP_DEPS=1; shift;;
    --skip-db) SKIP_DB=1; shift;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

die() { echo "ERROR: $*"; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing dependency: $1"
}

install_deps() {
  if [[ "$SKIP_DEPS" -eq 1 ]]; then
    echo "Skipping dependency install (--skip-deps)"
    return
  fi

  echo "Installing OS dependencies..."
  sudo apt-get update -y
  
  # Install core dependencies
  sudo apt-get install -y \
    git curl ca-certificates build-essential \
    libxml2-dev libxslt1-dev libldap2-dev libsasl2-dev \
    libssl-dev libjpeg-dev libpq-dev libffi-dev zlib1g-dev \
    libreadline-dev libyaml-dev libzip-dev libmagic1 postgresql postgresql-contrib \
    software-properties-common 2>&1 | tail -20
  
  # Install Python 3.12 from deadsnakes PPA
  echo "Installing Python 3.12..."
  sudo add-apt-repository -y ppa:deadsnakes/ppa 2>&1 | tail -5
  sudo apt-get update -y 2>&1 | tail -5
  sudo apt-get install -y python3.12 python3.12-venv python3.12-dev 2>&1 | tail -20
  command -v python3.12 >/dev/null 2>&1 || die "Python 3.12 installation failed"

  install_wkhtmltopdf
  resolve_uv
}

# "<build> <sha256>" of the official patched-Qt wkhtmltopdf .deb for a distro
# codename + dpkg architecture; empty when no build exists (e.g. focal).
wkhtmltopdf_deb_for() {
  local codename="$1" arch="$2" build
  case "$codename" in
    jammy|noble) build="jammy" ;;
    bookworm|trixie) build="bookworm" ;;
    *) return 0 ;;
  esac
  case "${build}_${arch}" in
    jammy_amd64) echo "jammy_amd64 4f723b2691ad8638a9df960e0421d346d7315083e3583a334f33362280ddba15" ;;
    jammy_arm64) echo "jammy_arm64 2095f20256661ebf0983b9311168596c9d012666e21a94bc24f304db6ac69ec5" ;;
    bookworm_amd64) echo "bookworm_amd64 98ba0d157b50d36f23bd0dedf4c0aa28c7b0c50fcdcdc54aa5b6bbba81a3941d" ;;
    bookworm_arm64) echo "bookworm_arm64 b6606157b27c13e044d0abbe670301f88de4e1782afca4f9c06a5817f3e03a9c" ;;
  esac
}

# Odoo PDF reports need wkhtmltopdf 0.12.6 built with patched Qt (distro packages
# are unpatched: no headers/footers, no multi-document PDFs). Checksum-pinned.
install_wkhtmltopdf() {
  if command -v wkhtmltopdf >/dev/null 2>&1 && wkhtmltopdf --version 2>/dev/null | grep -q "patched qt"; then
    echo "✓ $(wkhtmltopdf --version)"
    return
  fi
  local codename arch sel build sha deb
  codename="$(. /etc/os-release && echo "${VERSION_CODENAME:-}")"
  arch="$(dpkg --print-architecture)"
  sel="$(wkhtmltopdf_deb_for "$codename" "$arch")"
  if [[ -z "$sel" ]]; then
    echo "WARNING: no patched-Qt wkhtmltopdf build for ${codename}/${arch}; PDF reports will not print."
    return
  fi
  read -r build sha <<<"$sel"
  deb="$(mktemp -d)/wkhtmltox_0.12.6.1-3.${build}.deb"
  echo "Installing wkhtmltopdf 0.12.6.1-3 (patched qt, ${build})..."
  curl -fsSL -o "$deb" "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-3/wkhtmltox_0.12.6.1-3.${build}.deb" \
    || die "wkhtmltopdf download failed"
  echo "${sha}  ${deb}" | sha256sum -c --quiet - || die "wkhtmltopdf checksum mismatch"
  chmod 644 "$deb"
  sudo apt-get install -y "$deb" 2>&1 | tail -3
  wkhtmltopdf --version | grep -q "patched qt" || die "wkhtmltopdf installed without patched qt"
  rm -rf "$(dirname "$deb")"
}

# uv as a standalone binary. Ubuntu 23.04+ refuses `pip install` into the system
# Python (PEP 668, "externally-managed-environment"), so uv is never pip-installed.
UV_BIN=""
resolve_uv() {
  if [[ -n "$UV_BIN" ]]; then
    return
  fi
  if command -v uv >/dev/null 2>&1; then
    UV_BIN="$(command -v uv)"
  elif [[ -x "$HOME/.local/bin/uv" ]]; then
    UV_BIN="$HOME/.local/bin/uv"
  else
    echo "Installing uv (standalone installer)..."
    curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh >/dev/null \
      || die "uv installation failed"
    UV_BIN="$HOME/.local/bin/uv"
  fi
  [[ -x "$UV_BIN" ]] || die "uv not found after install"
  echo "✓ uv ready: $("$UV_BIN" --version)"
}

ensure_uv() {
  resolve_uv
}

ensure_pyenv() {
  if command -v pyenv >/dev/null 2>&1; then
    return
  fi
  die "pyenv not found. Install pyenv to manage Python 3.6/3.7 for older Odoo versions."
}

pyenv_python_for_version() {
  local version="$1"
  # Odoo 12-14 prefer older Python. Use 3.6.x for 12, 3.7.x for 13-14.
  if [[ "$version" -le 12 ]]; then
    echo "3.6.15"
    return
  fi
  if [[ "$version" -le 14 ]]; then
    echo "3.7.17"
    return
  fi
  echo ""
}

detect_min_pg_required() {
  local min_pg=""
  for v in ${VERSIONS//,/ }; do
    local repo="$BASE_DIR/${v}_workspace/${v}.0"
    if [[ -d "$repo" ]]; then
      while IFS= read -r line; do
        case "$line" in
          MIN_PG_VERSION=*)
            local pg="${line#MIN_PG_VERSION=}"
            if [[ -z "$min_pg" || "$pg" -gt "$min_pg" ]]; then
              min_pg="$pg"
            fi
            ;;
        esac
      done < <(detect_repo_versions "$repo")
    fi
  done
  echo "$min_pg"
}

get_postgres_version() {
  if command -v psql >/dev/null 2>&1; then
    psql -V | awk '{print $3}' | cut -d. -f1
    return
  fi
  if command -v postgres >/dev/null 2>&1; then
    postgres -V | awk '{print $3}' | cut -d. -f1
    return
  fi
  echo ""
}

setup_postgres() {
  if [[ "$SKIP_DB" -eq 1 ]]; then
    echo "Skipping PostgreSQL setup (--skip-db)"
    return
  fi

  if ! command -v psql >/dev/null 2>&1; then
    echo "PostgreSQL not found, installing..."
    if [[ -n "${REQUIRED_MIN_PG:-}" ]]; then
      sudo apt-get install -y "postgresql-${REQUIRED_MIN_PG}"
    else
      sudo apt-get install -y postgresql
    fi
  fi

  if [[ -n "${REQUIRED_MIN_PG:-}" ]]; then
    local installed_pg
    installed_pg="$(get_postgres_version)"
    if [[ -n "$installed_pg" && "$installed_pg" -lt "$REQUIRED_MIN_PG" ]]; then
      echo "WARNING: PostgreSQL ${installed_pg} detected; Odoo recommends >= ${REQUIRED_MIN_PG}."
    fi
  fi

  # apt starts the server under systemd; containers and WSL need an explicit start.
  if ! pg_isready -q 2>/dev/null; then
    sudo service postgresql start || die "PostgreSQL is not running and could not be started"
  fi

  echo "Ensuring PostgreSQL role and databases exist..."
  sudo -u postgres psql -c "DO \$\$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}') THEN CREATE ROLE ${DB_USER} WITH LOGIN SUPERUSER PASSWORD '${DB_PASSWORD}'; ELSE ALTER ROLE ${DB_USER} WITH LOGIN SUPERUSER PASSWORD '${DB_PASSWORD}'; END IF; END \$\$;"

  for v in ${VERSIONS//,/ }; do
    local db="odoo${v}"
    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${db}'" | grep -q 1 || \
      sudo -u postgres psql -c "CREATE DATABASE ${db} OWNER ${DB_USER};"
  done
}

ensure_odoo_user() {
  echo "Ensuring system user 'odoo' exists with /opt/odoo home..."
  sudo useradd -m -d /opt/odoo -s /bin/bash odoo || true
  sudo mkdir -p /opt/odoo
  sudo chown -R odoo:odoo /opt/odoo
}

clone_repo() {
  local version="$1"
  local target="$2"

  if [[ -d "$target/.git" ]]; then
    if [[ -f "$target/requirements.txt" && -f "$target/odoo-bin" ]]; then
      echo "Repo already exists: $target"
      return
    fi

    if [[ "$FORCE" -eq 1 ]]; then
      echo "Repo exists but looks incomplete. Re-cloning: $target"
      rm -rf "$target"
    else
      die "Repo exists but missing requirements.txt or odoo-bin. Re-run with --force: $target"
    fi
  fi

  echo "Cloning Odoo ${version}.0 into $target..."
  git clone --branch "${version}.0" --single-branch --depth 1 "$ODOO_REPO_URL" "$target"
}

pick_python() {
  if command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
    return
  fi
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  die "Python not found (need python3.12 or python3)"
}

version_to_int() {
  local v="$1"
  local major="${v%%.*}"
  local minor="${v##*.}"
  echo $((major * 100 + minor))
}

detect_repo_versions() {
  local repo="$1"
  local pybin
  pybin="$(pick_python)"
  "$pybin" "$SCRIPT_DIR/bootstrap_odoo_env.py" --detect-versions --repo "$repo"
}

select_python_for_repo() {
  local repo="$1"
  local version="$2"
  local min_py=""
  local max_py=""

  while IFS= read -r line; do
    case "$line" in
      MIN_PY_VERSION=*) min_py="${line#MIN_PY_VERSION=}" ;;
      MAX_PY_VERSION=*) max_py="${line#MAX_PY_VERSION=}" ;;
    esac
  done < <(detect_repo_versions "$repo")

  if [[ -z "$min_py" ]]; then
    min_py="3.6"
  fi

  if [[ "$version" -ge 15 ]]; then
    # Prefer Python 3.12 for modern Odoo versions when available.
    if command -v python3.12 >/dev/null 2>&1; then
      min_py="3.12"
    fi
  fi

  # Odoo 17+ works reliably with Python 3.12 in this setup.
  if [[ "$version" -ge 17 ]] && command -v python3.12 >/dev/null 2>&1; then
    echo "python3.12"
    return
  fi

  local min_i max_i
  min_i="$(version_to_int "$min_py")"
  max_i=""
  if [[ -n "$max_py" ]]; then
    max_i="$(version_to_int "$max_py")"
  fi

  local candidates_desc=(python3.13 python3.12 python3.11 python3.10 python3.9 python3.8 python3.7 python3.6 python3)
  local candidates_asc=(python3.6 python3.7 python3.8 python3.9 python3.10 python3.11 python3.12 python3.13 python3)
  local best=""
  local candidates=("${candidates_desc[@]}")
  if [[ -z "$max_i" ]]; then
    if [[ "$version" -ge 15 ]]; then
      candidates=("${candidates_desc[@]}")
    else
      candidates=("${candidates_asc[@]}")
    fi
  fi

  if [[ "$version" -le 14 ]]; then
    # Force pyenv-managed Python for legacy Odoo
    if command -v pyenv >/dev/null 2>&1; then
      local py_ver
      py_ver="$(pyenv_python_for_version "$version")"
      if [[ -n "$py_ver" ]]; then
        pyenv install -s "$py_ver"
        pyenv shell "$py_ver"
        echo "$(pyenv which python)"
        return
      fi
    fi
    echo "WARNING: pyenv not available; falling back to system Python for Odoo $version.0." >&2
  fi

  for bin in "${candidates[@]}"; do
    if ! command -v "$bin" >/dev/null 2>&1; then
      continue
    fi
    local ver
    ver="$("$bin" - <<'PY'
import sys
print(f"{sys.version_info[0]}.{sys.version_info[1]}")
PY
)"
    local vi
    vi="$(version_to_int "$ver")"
    if (( vi < min_i )); then
      continue
    fi
    if [[ -n "$max_i" ]] && (( vi > max_i )); then
      continue
    fi
    best="$bin"
    break
  done

  if [[ -z "$best" ]]; then
    die "No compatible Python found for repo (min=${min_py}, max=${max_py:-none})"
  fi

  if [[ "$version" -le 14 ]]; then
    echo "WARNING: Using $best for Odoo $version.0. Older deps may require Python 3.6/3.7." >&2
  fi
  echo "$best"
}

setup_venv() {
  local odoo_dir="$1"
  local version="$2"
  local pybin
  pybin="$(select_python_for_repo "$odoo_dir" "$version")"

  if [[ -d "$odoo_dir/.venv" && "$FORCE" -eq 0 ]]; then
    echo "Venv already exists: $odoo_dir/.venv"
    return
  fi

  echo "Creating venv in $odoo_dir/.venv with uv..."
  
  if [[ "$version" -le 14 ]]; then
    # Legacy Odoo: use standard pip approach
    ensure_pyenv
    "$pybin" -m venv "$odoo_dir/.venv"
    source "$odoo_dir/.venv/bin/activate"
    python -m ensurepip
    python -m pip install "pip<21" "setuptools<45" "wheel<0.38"
    PIP_USE_PEP517=0 python -m pip install --no-build-isolation --no-use-pep517 -r "$odoo_dir/requirements.txt"
  else
    # Modern Odoo 15+: use uv for speed
    ensure_uv
    echo "Using uv venv for Odoo ${version}.0..."
    "$UV_BIN" venv --python "$pybin" "$odoo_dir/.venv"
    "$UV_BIN" pip install --python "$odoo_dir/.venv/bin/python" setuptools
    "$UV_BIN" pip install --python "$odoo_dir/.venv/bin/python" -r "$odoo_dir/requirements.txt"
    if [[ "$version" -ge 17 ]]; then
      # Shipped by Odoo's debian/control, absent from requirements.txt off Windows:
      # phone_validation needs phonenumbers; reportlab 4 QR/barcode rendering needs rl-renderPM.
      "$UV_BIN" pip install --python "$odoo_dir/.venv/bin/python" phonenumbers rl-renderPM
    fi
  fi
  
  if declare -f deactivate >/dev/null 2>&1; then
    deactivate || true
  fi
}


write_config() {
  local workspace="$1"
  local version="$2"
  local port="$3"

  local pybin
  pybin="$(select_python_for_repo "$workspace/$version.0" "$version")"

  "$pybin" "$SCRIPT_DIR/bootstrap_odoo_env.py" \
    --workspace "$workspace" \
    --version "$version" \
    --db-user "$DB_USER" \
    --db-password "$DB_PASSWORD" \
    --db-host "$DB_HOST" \
    --db-port "$DB_PORT" \
    --admin-passwd "$ADMIN_PASSWD" \
    --port "$port" \
    --extra-addons "$EXTRA_ADDONS" \
    --write-config
}

copy_manage_modules() {
  local workspace="$1"
  local version="$2"
  local target="$workspace/manage_modules.sh"

  if [[ -f "$target" && "$FORCE" -eq 0 ]]; then
    echo "manage_modules.sh already exists: $target"
  else
    cp "$SCRIPT_DIR/manage_modules.sh" "$target"
    chmod +x "$target"
    echo "Copied manage_modules.sh to $target"
  fi

  # Copy config template with {{WORKSPACE_PATH}} substitution
  local config_dir="$workspace/config"
  mkdir -p "$config_dir"
  local template="$SCRIPT_DIR/config/odoo.conf.${version}"
  local config_file="$config_dir/odoo.conf.${version}"
  if [[ -f "$template" ]]; then
    if [[ ! -f "$config_file" || "$FORCE" -eq 1 ]]; then
      sed -e "s|{{WORKSPACE_PATH}}|${workspace}|g" \
          -e "s|{{DB_USER}}|${DB_USER}|g" \
          -e "s|{{DB_PASSWORD}}|${DB_PASSWORD}|g" "$template" > "$config_file"
      echo "Config copied: $config_file (Port: $((8090 + version)), DB: odoo${version})"
    fi
  fi
}

# Let manage_modules.sh find this kit's MCP launcher (plugin/odoo_mcp).
record_kit_home() {
  local env_file="$1/.env"
  if ! grep -q -E "^[[:space:]]*ODOO_AGENT_PRO_KIT_HOME=" "$env_file" 2>/dev/null; then
    printf 'ODOO_AGENT_PRO_KIT_HOME=%s\n' "$(cd "$SCRIPT_DIR/.." && pwd)" >> "$env_file"
    chmod 600 "$env_file"
  fi
}

main() {
  need_cmd git
  install_deps

  ensure_odoo_user

  mkdir -p "$BASE_DIR"

  for v in ${VERSIONS//,/ }; do
    local ws="$BASE_DIR/${v}_workspace"
    local odoo_dir="$ws/${v}.0"
    local extra_dir="$ws/extra-${v}"
    local config_dir="$ws/config"
    local logs_dir="$ws/logs"
    local data_dir="$ws/data"
    local port=$((8090 + v))

    printf "\n=== Odoo %s.0 workspace: %s ===\n" "$v" "$ws"
    mkdir -p "$ws" "$extra_dir" "$config_dir" "$logs_dir" "$data_dir"

    copy_manage_modules "$ws" "$v"
    record_kit_home "$ws"
    clone_repo "$v" "$odoo_dir"
  done

  REQUIRED_MIN_PG="$(detect_min_pg_required)"
  setup_postgres

  for v in ${VERSIONS//,/ }; do
    local ws="$BASE_DIR/${v}_workspace"
    local odoo_dir="$ws/${v}.0"
    local port=$((8090 + v))

    setup_venv "$odoo_dir" "$v"
    write_config "$ws" "$v" "$port"
  done

  printf "\nBootstrap complete. Next steps:\n"
  for v in ${VERSIONS//,/ }; do
    local ws="$BASE_DIR/${v}_workspace"
    local port=$((8090 + v))
    echo "  Odoo $v: cd $ws && WORKSPACE_PATH=. ODOO_VERSION=$v ./manage_modules.sh start"
    echo "           Access: http://localhost:$port (DB: odoo${v})"
  done
}

main "$@"
