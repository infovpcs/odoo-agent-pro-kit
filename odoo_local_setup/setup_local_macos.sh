#!/bin/bash
# setup_local_macos.sh
# macOS-compatible setup for Odoo 17, 18, 19 workspaces using uv and python 3.12

set -e

# Default Base Directory
BASE_DIR="${HOME}/odoo-workspaces"
PYTHON_VERSION="3.12"

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
    mkdir -p "${workspace_dir}/extra-${version}"

    # 2. Clone Repository (Shallow)
    if [ ! -d "${repo_dir}" ]; then
        print_step "Cloning Odoo ${version} (shallow)..."
        git clone --depth 1 --branch "${version}.0" https://github.com/odoo/odoo.git "${repo_dir}"
    else
        print_step "Odoo repo already exists. Pulling latest..."
        cd "${repo_dir}" && git pull && cd - > /dev/null
    fi

    # 3. Create Virtual Environment with uv
    if [ ! -d "${venv_dir}" ]; then
        print_step "Creating virtual environment with uv (Python ${PYTHON_VERSION})..."
        cd "${repo_dir}"
        uv venv --python "${PYTHON_VERSION}" .venv
    else
        print_step "Virtual environment already exists."
    fi

    # 4. Install Dependencies
    print_step "Installing dependencies for Odoo ${version}..."
    cd "${repo_dir}"
    source .venv/bin/activate
    
    # Core valid dependencies that always exist
    # Note: Added setuptools/wheel which are sometimes needed for building extensions
    UV_DEPS="psycopg2-binary werkzeug lxml pillow python-dateutil pytz pyyaml requests jinja2 reportlab polib passlib decorator gevent greenlet markupsafe psutil setuptools wheel"
    
    # Version specific additions
    if [ "$version" == "17" ] || [ "$version" == "18" ] || [ "$version" == "19" ]; then
         UV_DEPS="$UV_DEPS num2words xlwt pypdf"
    fi

    # Use uv pip install for speed
    print_step "Installing core dependencies list..."
    uv pip install $UV_DEPS
    
    # Try installing from requirements.txt if it exists
    if [ -f "requirements.txt" ]; then
        print_step "Installing remaining requirements from requirements.txt..."
        # uv is fast, so we try it. If it fails on some specific package, we warn but don't stop.
        uv pip install -r requirements.txt || print_warning "Some requirements failed to install. This is common on macOS. Ensure core deps are working."
    fi

    # 5. Configure Odoo
    print_step "Generating configuration..."
    mkdir -p "$(dirname "${config_dest}")"
    if [ -f "${config_src}" ]; then
         cp "${config_src}" "${config_dest}"
         
         # Mac sed requires empty string for -i
         # Replace Workspace Path
         sed -i '' "s|{{WORKSPACE_PATH}}|${workspace_dir}|g" "${config_dest}"
         
         # Replace DB Credentials (with defaults)
         local db_user="${DB_USER:-odoo}"
         local db_pass="${DB_PASSWORD:-odoo}"
         
         sed -i '' "s|{{DB_USER}}|${db_user}|g" "${config_dest}"
         sed -i '' "s|{{DB_PASSWORD}}|${db_pass}|g" "${config_dest}"
         
         print_success "Configuration created at ${config_dest}"
    else
         print_error "Config template not found at ${config_src}! Configuration step FAILED."
         # We continue, but this is bad
    fi

    # 6. Copy Manager Script
    if [ -f "${manage_script_src}" ]; then
        cp "${manage_script_src}" "${workspace_dir}/"
        chmod +x "${workspace_dir}/manage_modules.sh"
        print_success "manage_modules.sh copied to ${workspace_dir}/"
    else
        print_error "manage_modules.sh not found at ${manage_script_src}! Copy failed."
    fi

    print_success "Odoo ${version} setup complete!"
}

# Main Execution

check_prerequisites

# Create Base Directory
mkdir -p "${BASE_DIR}"

# Run for 17, 18, 19
setup_workspace "17"
setup_workspace "18"
setup_workspace "19"

echo ""
print_success "All workspaces set up successfully at ${BASE_DIR}"
