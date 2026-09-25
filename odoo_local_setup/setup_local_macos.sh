#!/bin/bash
# setup_local_macos.sh
# macOS setup for Odoo 17, 18, 19, and 20 workspaces using uv and Python 3.12.
#
# Usage: ./setup_local_macos.sh [--versions 17,18,19] [--base-dir DIR]
#                               [--db-host HOST] [--db-port PORT] [--force] [--dry-run]
#
# Odoo 20.0 needs PostgreSQL >= 16 (odoo/release.py MIN_PG_VERSION). If the local
# server is older, point the 20 workspace at a separate PostgreSQL 16 server with
# --db-port (for example a postgres:16 container published on 127.0.0.1:5436).

set -e

BASE_DIR="${HOME}/odoo-workspaces"
PYTHON_VERSION="3.12"
VERSIONS="17,18,19"
SUPPORTED_VERSIONS="17 18 19 20"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
FORCE=0
DRY_RUN=0

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}SUCCESS:${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

usage() {
    cat <<USAGE
Usage: $0 [options]

Options:
  --versions LIST   Comma list of Odoo versions: ${SUPPORTED_VERSIONS// /,} (default: ${VERSIONS})
  --base-dir DIR    Directory holding <version>_workspace folders (default: ${BASE_DIR})
  --db-host HOST    PostgreSQL host written to the config (default: ${DB_HOST})
  --db-port PORT    PostgreSQL port written to the config (default: ${DB_PORT})
  --force           Overwrite an existing config/odoo.conf.<version>
  --dry-run         Print the plan and change nothing
  -h, --help        Show help
USAGE
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --versions) VERSIONS="$2"; shift 2 ;;
        --base-dir) BASE_DIR="$2"; shift 2 ;;
        --db-host) DB_HOST="$2"; shift 2 ;;
        --db-port) DB_PORT="$2"; shift 2 ;;
        --force) FORCE=1; shift ;;
        --dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) print_error "Unknown argument: $1"; usage; exit 2 ;;
    esac
done

for v in ${VERSIONS//,/ }; do
    case " ${SUPPORTED_VERSIONS} " in
        *" ${v} "*) ;;
        *) print_error "Unsupported Odoo version: ${v} (supported: ${SUPPORTED_VERSIONS})"; exit 2 ;;
    esac
done

check_prerequisites() {
    print_step "Checking prerequisites..."

    # Check for brew
    if ! command -v brew &> /dev/null; then
        print_error "Homebrew not found. Please install Homebrew first."
        exit 1
    fi

    # Check for python3.12
    if ! command -v python3.12 &> /dev/null; then
        print_warning "Python 3.12 not found. Installing via Homebrew..."
        brew install python@3.12
    fi

    # Check for uv
    if ! command -v uv &> /dev/null; then
        print_warning "uv not found. Installing via curl..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        source "$HOME/.cargo/env" || true
    fi

    # Check for git
    if ! command -v git &> /dev/null; then
        print_error "git not found. Please install git."
        exit 1
    fi

    # Check for PostgreSQL (optional check, but good to warn)
    if ! command -v psql &> /dev/null; then
        print_warning "PostgreSQL CLI (psql) not found. Ensure Postgres is installed and running."
    fi
}

# Warn when the PostgreSQL server at DB_HOST:DB_PORT is older than the checkout's
# MIN_PG_VERSION (Odoo refuses to start on an unsupported server).
check_postgres_version() {
    local repo_dir=$1
    local min_pg server_pg
    min_pg="$(sed -n 's/^MIN_PG_VERSION *= *\([0-9]*\).*/\1/p' "${repo_dir}/odoo/release.py" 2>/dev/null)"
    [ -n "${min_pg}" ] || return 0
    command -v psql &> /dev/null || return 0
    server_pg="$(psql -h "${DB_HOST}" -p "${DB_PORT}" -d postgres -Atc 'SHOW server_version_num' 2>/dev/null || true)"
    if [ -z "${server_pg}" ]; then
        print_warning "Could not reach PostgreSQL at ${DB_HOST}:${DB_PORT} to check it is >= ${min_pg}."
    elif [ "$((server_pg / 10000))" -lt "${min_pg}" ]; then
        print_warning "PostgreSQL $((server_pg / 10000)) at ${DB_HOST}:${DB_PORT} is older than the required ${min_pg}; use --db-port for a newer server."
    else
        print_success "PostgreSQL $((server_pg / 10000)) at ${DB_HOST}:${DB_PORT} meets MIN_PG_VERSION ${min_pg}."
    fi
}

# Determine the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

setup_workspace() {
    local version=$1
    local workspace_dir="${BASE_DIR}/${version}_workspace"
    local repo_dir="${workspace_dir}/${version}.0"
    local venv_dir="${repo_dir}/.venv"
    # Source files are expected to be relative to the script location
    local config_src="${SCRIPT_DIR}/config/odoo.conf.${version}"
    local config_dest="${workspace_dir}/config/odoo.conf.${version}"
    local manage_script_src="${SCRIPT_DIR}/manage_modules.sh"

    print_step "Setting up Odoo ${version} workspace at ${workspace_dir}..."

    # 1. Create Directories
    mkdir -p "${workspace_dir}"
    mkdir -p "${workspace_dir}/logs"
    mkdir -p "${workspace_dir}/data"
    mkdir -p "${workspace_dir}/extra-${version}"

    # 2. Clone Repository (Shallow)
    if [ ! -d "${repo_dir}" ]; then
        print_step "Cloning Odoo ${version} (shallow)..."
        git clone --depth 1 --branch "${version}.0" https://github.com/odoo/odoo.git "${repo_dir}"
    else
        print_step "Odoo repo already exists. Pulling latest (fast-forward only)..."
        git -C "${repo_dir}" pull --ff-only || print_warning "git pull failed in ${repo_dir}; continuing with the current checkout."
    fi

    # 3. Create Virtual Environment with uv
    if [ ! -d "${venv_dir}" ]; then
        print_step "Creating virtual environment with uv (Python ${PYTHON_VERSION})..."
        uv venv --python "${PYTHON_VERSION}" "${venv_dir}"
    else
        print_step "Virtual environment already exists."
    fi

    # 4. Install Dependencies
    print_step "Installing dependencies for Odoo ${version}..."

    # Core valid dependencies that always exist
    # Note: Added setuptools/wheel which are sometimes needed for building extensions
    UV_DEPS="psycopg2-binary werkzeug lxml pillow python-dateutil pytz pyyaml requests jinja2 reportlab polib passlib decorator gevent greenlet markupsafe psutil setuptools wheel"

    # Version specific additions
    if [ "$version" -ge 17 ]; then
         UV_DEPS="$UV_DEPS num2words xlwt pypdf"
    fi

    # Use uv pip install for speed
    print_step "Installing core dependencies list..."
    uv pip install --python "${venv_dir}/bin/python" $UV_DEPS

    # Try installing from requirements.txt if it exists
    if [ -f "${repo_dir}/requirements.txt" ]; then
        print_step "Installing remaining requirements from requirements.txt..."
        # uv is fast, so we try it. If it fails on some specific package, we warn but don't stop.
        uv pip install --python "${venv_dir}/bin/python" -r "${repo_dir}/requirements.txt" \
            || print_warning "Some requirements failed to install. This is common on macOS. Ensure core deps are working."
    fi

    # 5. Configure Odoo (never clobber a customised config unless --force)
    print_step "Generating configuration..."
    mkdir -p "$(dirname "${config_dest}")"
    if [ -f "${config_dest}" ] && [ "${FORCE}" -ne 1 ]; then
         print_warning "Keeping existing ${config_dest} (use --force to regenerate it)."
    elif [ -f "${config_src}" ]; then
         local db_user="${DB_USER:-odoo}"
         local db_pass="${DB_PASSWORD:-odoo}"
         sed -e "s|{{WORKSPACE_PATH}}|${workspace_dir}|g" \
             -e "s|{{DB_USER}}|${db_user}|g" \
             -e "s|{{DB_PASSWORD}}|${db_pass}|g" \
             -e "s|{{DB_HOST}}|${DB_HOST}|g" \
             -e "s|{{DB_PORT}}|${DB_PORT}|g" \
             "${config_src}" > "${config_dest}"
         print_success "Configuration created at ${config_dest}"
    else
         print_error "Config template not found at ${config_src}! Configuration step FAILED."
         # We continue, but this is bad
    fi

    # 6. Copy Manager Script (back up a differing copy first)
    if [ -f "${manage_script_src}" ]; then
        local manage_dest="${workspace_dir}/manage_modules.sh"
        if [ -f "${manage_dest}" ] && ! cmp -s "${manage_script_src}" "${manage_dest}"; then
            cp "${manage_dest}" "${manage_dest}.bak"
            print_warning "Existing manage_modules.sh differed; saved it as ${manage_dest}.bak"
        fi
        cp "${manage_script_src}" "${manage_dest}"
        chmod +x "${manage_dest}"
        print_success "manage_modules.sh copied to ${workspace_dir}/"
    else
        print_error "manage_modules.sh not found at ${manage_script_src}! Copy failed."
    fi

    check_postgres_version "${repo_dir}"

    print_success "Odoo ${version} setup complete!"
}

# Main Execution

if [ "${DRY_RUN}" -eq 1 ]; then
    for v in ${VERSIONS//,/ }; do
        echo "Would set up ${BASE_DIR}/${v}_workspace (${v}.0, Python ${PYTHON_VERSION}, db ${DB_HOST}:${DB_PORT}, http port $((8090 + v)))"
    done
    exit 0
fi

check_prerequisites

# Create Base Directory
mkdir -p "${BASE_DIR}"

for v in ${VERSIONS//,/ }; do
    setup_workspace "${v}"
done
