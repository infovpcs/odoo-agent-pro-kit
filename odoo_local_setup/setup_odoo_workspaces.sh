#!/bin/bash
# =============================================================================
# Odoo Multi-Version Setup Script (MacBook/Ubuntu Friendly)
# =============================================================================
# This script sets up Odoo 17, 18, and 19 development environments
# with AI Agent Skills and MCP Server integration.
#
# Usage:
#   ./setup_odoo_workspaces.sh --base-dir ~/odoo-workspaces --versions 17,18,19
#   ./setup_odoo_workspaces.sh --skip-db --versions 17,18
#
# Options:
#   --base-dir DIR     Base directory for workspaces (default: ~/odoo-workspaces)
#   --versions LIST   Comma-separated: 17,18,19 (default: all)
#   --skip-db         Skip PostgreSQL setup (use existing)
#   --skip-odoo      Skip Odoo repository clone
#   --force           Overwrite existing files
#   -h, --help       Show help
#
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="${HOME}/odoo-workspaces"
VERSIONS="17,18,19"
SKIP_DB=0
SKIP_ODOO=0
FORCE=0
COPY_SKILLS=0
INSTALL_HARNESS=0
WORKSPACE_PATH=""
DB_USER="${DB_USER:-odoo}"
DB_PASSWORD="${DB_PASSWORD:-odoo}"

# =============================================================================
# Helper Functions
# =============================================================================

print_banner() {
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Darwin*)  echo "macos" ;;
        Linux*)  echo "linux" ;;
        *)       echo "unknown" ;;
    esac
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# =============================================================================
# Prerequisites Check
# =============================================================================

check_prerequisites() {
    print_banner "Checking Prerequisites"

    local os_type
    os_type=$(detect_os)
    print_info "Operating System: $os_type"

    # Check required commands
    local missing=()

    for cmd in git curl python3; do
        if command_exists "$cmd"; then
            print_success "$cmd found"
        else
            missing+=("$cmd")
            print_error "$cmd not found"
        fi
    done

    # Check Python version
    local python_version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_info "Python version: $python_version"

    # Check for uv (recommended for macOS)
    if command_exists uv; then
        print_success "uv package manager found"
    else
        print_warning "uv not found (recommended for macOS)"
        if [ "$os_type" = "macos" ]; then
            print_info "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        fi
    fi

    # Check for PostgreSQL (optional)
    if command_exists psql; then
        print_success "PostgreSQL found"
        SKIP_DB=1  # Default to skip for existing setup
    else
        print_warning "PostgreSQL not found"
        print_info "Install PostgreSQL or use --skip-db if already running"
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing required commands: ${missing[*]}"
        exit 1
    fi

    print_success "Prerequisites check complete!"
    echo ""
}

# =============================================================================
# Setup Functions
# =============================================================================

setup_workspace() {
    local version="$1"
    local workspace_dir="${BASE_DIR}/${version}_workspace"

    print_banner "Setting up Odoo ${version} Workspace"

    # Create workspace directory
    mkdir -p "$workspace_dir"
    mkdir -p "$workspace_dir/config"
    mkdir -p "$workspace_dir/logs"
    mkdir -p "$workspace_dir/data"

    print_info "Workspace: $workspace_dir"

    # Clone Odoo repository if not skipped
    if [ $SKIP_ODOO -eq 0 ]; then
        local odoo_dir="${workspace_dir}/${version}.0"
        if [ -d "$odoo_dir" ] && [ $FORCE -eq 0 ]; then
            print_warning "Odoo ${version} already exists, skipping clone"
        else
            print_info "Cloning Odoo ${version}..."
            # Use official Odoo repository
            if [ "$version" = "17" ]; then
                git clone --depth 1 --branch ${version}.0 https://github.com/odoo/odoo.git "$odoo_dir" 2>/dev/null || \
                git clone --depth 1 --branch ${version}.0 https://github.com/odoo/odoo.git "$odoo_dir"
            elif [ "$version" = "18" ]; then
                git clone --depth 1 --branch ${version}.0 https://github.com/odoo/odoo.git "$odoo_dir"
            else
                git clone --depth 1 --branch ${version}.0 https://github.com/odoo/odoo.git "$odoo_dir"
            fi
            print_success "Odoo ${version} cloned"
        fi
    fi

    # Create virtual environment
    local venv_dir="${workspace_dir}/${version}.0/.venv"
    if [ -d "$venv_dir" ] && [ $FORCE -eq 0 ]; then
        print_info "Virtual environment already exists"
    else
        print_info "Creating virtual environment..."
        python3 -m venv "$venv_dir"
        source "$venv_dir/bin/activate"

        # Install dependencies
        pip install --upgrade pip wheel setuptools

        print_success "Virtual environment created"
    fi

    # Copy Agent Skills
    print_info "Copying Agent Skills..."
    local agents_src="${SCRIPT_DIR}/../AgentSkills"

    if [ -d "$agents_src" ]; then
        local agents_dst="${workspace_dir}/skills"
        mkdir -p "$agents_dst"
        cp -r "${agents_src}/." "$agents_dst/" 2>/dev/null || true
        print_success "Agent Skills copied to ${agents_dst}"
    else
        print_warning "AgentSkills source not found at ${agents_src} — skipping skill copy"
    fi

    # Copy manage_modules.sh
    if [ -f "${SCRIPT_DIR}/manage_modules.sh" ]; then
        cp "${SCRIPT_DIR}/manage_modules.sh" "${workspace_dir}/"
        chmod +x "${workspace_dir}/manage_modules.sh"
        print_success "manage_modules.sh installed"
    else
        print_warning "manage_modules.sh not found in ${SCRIPT_DIR}"
    fi

    # Create .env file
    if [ ! -f "${workspace_dir}/.env" ] || [ $FORCE -eq 1 ]; then
        local port=$((8090 + version))
        local database="odoo${version}"
        local mcp_port=$((8765 + version - 17))
        cat > "${workspace_dir}/.env" << EOF
# Odoo ${version} Configuration
ODOO_VERSION=${version}
ODOO_PORT=${port}
ODOO_DB_NAME=${database}
ODOO_DB_USER=${DB_USER}
ODOO_DB_PASSWORD=${DB_PASSWORD}
ODOO_ADMIN_PASSWD=admin

# Paths
ODOO${version}_ADDONS=${workspace_dir}/${version}.0/addons
WORKSPACE_PATH=${workspace_dir}

# MCP Server (Phase 11-12)
MCP_ENABLED=true
MCP_SERVER_PORT=${mcp_port}

# Model Routing
MODEL_DEFAULT_ANALYSIS=claude-haiku-4-5-20251001
MODEL_DEFAULT_CODING=claude-sonnet-4-6

# Agent
AGENT_AUTONOMOUS_MODE=false
COPILOT_MODEL=claude-sonnet-4-6
EOF
        print_success ".env created (Port: ${port}, DB: ${database})"
    fi

    # Copy and configure odoo.conf from template (substitutes {{WORKSPACE_PATH}})
    local config_dir="${workspace_dir}/config"
    mkdir -p "$config_dir"
    local config_file="${config_dir}/odoo.conf.${version}"
    local template_file="${SCRIPT_DIR}/config/odoo.conf.${version}"
    if [ ! -f "$config_file" ] || [ $FORCE -eq 1 ]; then
        if [ -f "$template_file" ]; then
            # Copy template and substitute placeholders
            sed -e "s|{{WORKSPACE_PATH}}|${workspace_dir}|g" \
                -e "s|{{DB_USER}}|${DB_USER}|g" \
                -e "s|{{DB_PASSWORD}}|${DB_PASSWORD}|g" "$template_file" > "$config_file"
            local port=$((8090 + version))
            local database="odoo${version}"
            print_success "odoo.conf.${version} copied from template (Port: ${port}, DB: ${database})"
        else
            print_warning "Template not found: ${template_file}, generating minimal config"
            local port=$((8090 + version))
            local database="odoo${version}"
            cat > "$config_file" << CONFEOF
[options]
db_host = localhost
db_port = 5432
db_user = ${DB_USER}
db_password = ${DB_PASSWORD}
db_name = ${database}
dbfilter = ^${database}\$
http_port = ${port}
xmlrpc_port = ${port}
addons_path = ${workspace_dir}/${version}.0/addons,${workspace_dir}/extra-${version}
data_dir = ${workspace_dir}/data
logfile = ${workspace_dir}/logs/odoo.log
admin_passwd = admin
list_db = True
workers = 0
demo = False
CONFEOF
            print_success "odoo.conf.${version} generated (Port: ${port}, DB: ${database})"
        fi
    fi

    print_success "Odoo ${version} workspace setup complete!"
    echo ""
}

# =============================================================================
# PostgreSQL Setup (Optional)
# =============================================================================

setup_postgresql() {
    if [ $SKIP_DB -eq 1 ]; then
        print_info "Skipping PostgreSQL setup"
        return 0
    fi

    print_banner "Setting up PostgreSQL"

    local os_type
    os_type=$(detect_os)

    if [ "$os_type" = "macos" ]; then
        # macOS: Use Homebrew or Postgres.app
        if command_exists brew; then
            print_info "Installing PostgreSQL via Homebrew..."
            brew install postgresql@15
            brew services start postgresql@15
        else
            print_warning "Install PostgreSQL from https://postgresapp.com"
        fi
    elif [ "$os_type" = "linux" ]; then
        # Ubuntu/Debian
        print_info "Installing PostgreSQL..."
        sudo apt-get update
        sudo apt-get install -y postgresql postgresql-contrib
        sudo systemctl start postgresql
    fi

    # Create user and databases
    print_info "Creating PostgreSQL user and databases..."
    sudo -u postgres psql -c "CREATE USER odoo WITH PASSWORD 'odoo' SUPERUSER;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE odoo17 OWNER odoo;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE odoo18 OWNER odoo;" 2>/dev/null || true
    sudo -u postgres psql -c "CREATE DATABASE odoo19 OWNER odoo;" 2>/dev/null || true

    print_success "PostgreSQL setup complete!"
    echo ""
}

# =============================================================================
# Phase 25: Harness Tools Setup
# =============================================================================

setup_harness_tools() {
    local workspace_dir="$1"
    local version="$2"
    local venv_dir="${workspace_dir}/${version}.0/.venv"

    print_banner "Installing Phase 25 Harness Tools (Odoo ${version})"

    if [ -f "${venv_dir}/bin/pip" ]; then
        print_info "Installing requests (required for Odoo 19 JSON-RPC 2.0 test runner)..."
        "${venv_dir}/bin/pip" install requests --quiet
        print_success "requests installed in ${venv_dir}"
    else
        print_warning "venv not found at ${venv_dir} — install requests manually: pip install requests"
    fi

    # Copy auto_test/ to workspace skills
    local auto_test_src="${SCRIPT_DIR}/../AgentSkills/auto_test"
    local auto_test_dst="${workspace_dir}/skills/auto_test"
    if [ -d "$auto_test_src" ]; then
        rm -rf "$auto_test_dst"
        cp -R "$auto_test_src" "$auto_test_dst"
        print_success "auto_test/ harness copied to ${auto_test_dst}"
    else
        print_warning "auto_test/ not found at ${auto_test_src}"
    fi

    print_success "Phase 25 harness tools ready for Odoo ${version}"
    echo ""
}

# =============================================================================
# MCP Server Setup
# =============================================================================

setup_mcp_servers() {
    print_banner "Setting up MCP Servers (Phase 11-12)"

    for v in ${VERSIONS//,/ }; do
        local workspace_dir="${BASE_DIR}/${v}_workspace"
        local manage_script="${workspace_dir}/manage_modules.sh"

        if [ -f "$manage_script" ]; then
            print_info "Starting MCP server for Odoo ${v} via manage_modules.sh..."
            WORKSPACE_PATH="$workspace_dir" ODOO_VERSION="$v" bash "$manage_script" mcp-start 2>/dev/null || \
            print_warning "MCP server for Odoo ${v} may already be running or needs manual start"
        else
            print_warning "manage_modules.sh not found at $workspace_dir, skipping MCP for Odoo ${v}"
        fi
    done

    print_success "MCP server setup complete!"
    echo ""
}

# =============================================================================
# Main Setup
# =============================================================================

main() {
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --base-dir)
                BASE_DIR="$2"
                shift 2
                ;;
            --versions)
                VERSIONS="$2"
                shift 2
                ;;
            --skip-db)
                SKIP_DB=1
                shift
                ;;
            --skip-odoo)
                SKIP_ODOO=1
                shift
                ;;
            --force)
                FORCE=1
                shift
                ;;
            --copy-skills)
                COPY_SKILLS=1
                shift
                ;;
            --install-harness)
                INSTALL_HARNESS=1
                shift
                ;;
            -h|--help)
                echo "Odoo Multi-Version Setup Script"
                echo "Usage: $0 [options]"
                echo ""
                echo "Options:"
                echo "  --base-dir DIR     Base directory (default: ~/odoo-workspaces)"
                echo "  --versions LIST    Versions: 17,18,19 (default: all)"
                echo "  --skip-db         Skip PostgreSQL setup"
                echo "  --skip-odoo       Skip Odoo clone"
                echo "  --force           Overwrite existing"
                echo "  --copy-skills        Copy AgentSkills to workspace platforms after setup"
                echo "  --install-harness    Install Phase 25 harness tools (requests pip package)"
                echo "  -h, --help       Show this help"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    print_banner "Odoo Multi-Version Setup (MacBook/Ubuntu Friendly)"
    echo ""
    echo "Base Directory: $BASE_DIR"
    echo "Versions: $VERSIONS"
    echo "Skip DB: $SKIP_DB"
    echo "Skip Odoo: $SKIP_ODOO"
    echo ""

    # Check prerequisites
    check_prerequisites

    # Setup PostgreSQL
    if [ $SKIP_DB -eq 0 ]; then
        setup_postgresql
    fi

    # Setup each version
    for v in ${VERSIONS//,/ }; do
        setup_workspace "$v"
    done

    # Phase 25: Install harness tools if requested
    if [ $INSTALL_HARNESS -eq 1 ]; then
        for v in ${VERSIONS//,/ }; do
            setup_harness_tools "${BASE_DIR}/${v}_workspace" "$v"
        done
    fi

    # Copy skills to workspace platforms if requested
    if [ $COPY_SKILLS -eq 1 ]; then
        local copy_script="${SCRIPT_DIR}/../AgentSkills/copy_skills_to_workspace.py"
        if [ -f "$copy_script" ]; then
            for v in ${VERSIONS//,/ }; do
                local ws="${BASE_DIR}/${v}_workspace"
                print_info "Copying skills to Odoo ${v} workspace..."
                python3 "$copy_script" "$ws" --platform all --force
                print_success "Skills copied to ${ws}"
            done
        else
            print_warning "copy_skills_to_workspace.py not found — skipping"
        fi
    fi

    # Setup MCP servers
    setup_mcp_servers

    # Summary
    print_banner "Setup Complete!"
    echo ""
    echo "📁 Workspaces created at: $BASE_DIR"
    echo ""
    echo "To start Odoo:"
    for v in ${VERSIONS//,/ }; do
        local port=$((8090 + v))
        echo "   Odoo $v: cd $BASE_DIR/${v}_workspace && WORKSPACE_PATH=. ODOO_VERSION=$v ./manage_modules.sh start"
        echo "   Access: http://localhost:$port"
        echo ""
    done

    echo "To start MCP servers:"
    for v in ${VERSIONS//,/ }; do
        echo "   Odoo $v MCP: cd $BASE_DIR/${v}_workspace && WORKSPACE_PATH=. ODOO_VERSION=$v ./manage_modules.sh mcp-start"
    done
    echo ""
    echo "To start Control Center:"
    echo "   cd $BASE_DIR/17_workspace/AgentSkills && ./start_copilot_agent.sh"
    echo "   Access: http://127.0.0.1:8000/static/index.html"
    echo ""
    echo "Phase 25 Harness commands:"
    echo "  Start fresh + harness: $0 --versions 19 --skip-odoo --install-harness --copy-skills"
    echo "  Auto-test a task:      python3 skills/auto_test/auto_test_runner.py --version 19 --module MODULE --task TASK"
    echo "  Write context:         python3 skills/auto_test/context_writer.py write --module MODULE --module-dir PATH --version 19 --command start-coding --summary TEXT"
    echo ""
}

# Run main
main "$@"
