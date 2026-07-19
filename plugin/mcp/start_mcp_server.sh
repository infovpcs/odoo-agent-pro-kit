#!/bin/bash
#
# MCP Server Startup Script
# Starts the Odoo MCP Server for connecting to Odoo 17, 18, and 19 instances
#
# Usage:
#   ./start_mcp_server.sh           # Start with default settings
#   ./start_mcp_server.sh --version 17.0  # Start for specific version only
#   ./start_mcp_server.sh --help          # Show help
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VENV_DIR="$PROJECT_DIR/.venv"
SERVER_SCRIPT="$SCRIPT_DIR/odoo_mcp_server.py"
CONFIG_FILE="$PROJECT_DIR/.env"
LOG_DIR="$SCRIPT_DIR/logs"
PID_FILE="$SCRIPT_DIR/mcp_server.pid"
LOG_FILE="$LOG_DIR/mcp_server.log"

# Default server settings
DEFAULT_PORT=8765
DEFAULT_HOST="localhost"

# Odoo versions to check
ODOO_VERSIONS=("17.0" "18.0" "19.0")

# Base port for multi-version mode
BASE_PORT=8765

get_major_version() {
    local version="${1:-19.0}"
    echo "$version" | cut -d. -f1
}

get_mcp_port_for_version() {
    local version="${1:-19.0}"
    local major
    major=$(get_major_version "$version")
    case "$major" in
        17) echo "8765" ;;
        18) echo "8766" ;;
        *) echo "8767" ;;
    esac
}

get_pid_file_for_version() {
    local version="${1:-19.0}"
    echo "$SCRIPT_DIR/mcp_server_${version/./_}.pid"
}

get_log_file_for_version() {
    local version="${1:-19.0}"
    echo "$LOG_DIR/mcp_server_${version/./_}.log"
}

# Print colored message
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[MCP Server]${NC} $1"
}

# Extract port from URL (e.g., http://localhost:8107 -> 8107)
extract_port_from_url() {
    local url="$1"
    if [[ "$url" =~ :([0-9]+)$ ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "8069"  # default
    fi
}

is_port_open() {
    local port="$1"
    nc -z localhost "$port" 2>/dev/null
}

ensure_odoo_running_for_version() {
    local version="$1"
    local major
    local url
    local port
    local manage_script
    local cwd
    local odoo_log
    local autostart_wait
    local manage_pid

    major=$(echo "$version" | cut -d. -f1)
    if [ "$major" == "19" ]; then
        url="${ODOO_URL:-http://localhost:8090}"
        manage_script="${ODOO_MANAGE_SCRIPT:-}"
    elif [ "$major" == "18" ]; then
        url="${ODOO18_URL:-http://localhost:8018}"
        manage_script="${ODOO18_MANAGE_SCRIPT:-}"
    else
        url="${ODOO17_URL:-http://localhost:8017}"
        manage_script="${ODOO17_MANAGE_SCRIPT:-}"
    fi

    port=$(extract_port_from_url "$url")
    if is_port_open "$port"; then
        print_status "Odoo $version is running on port $port (URL: $url)"
        return 0
    fi

    if [ -n "$manage_script" ] && [ -f "$manage_script" ]; then
        cwd="$(dirname "$manage_script")"
        local manage_name
        manage_name="$(basename "$manage_script")"
        odoo_log="$LOG_DIR/odoo_${version/./_}_autostart.log"
        autostart_wait="${MCP_ODOO_AUTOSTART_WAIT:-180}"
        print_warning "Odoo $version not running on port $port. Auto-starting via $manage_script ..."
        touch "$odoo_log" 2>/dev/null || true
        nohup bash -lc "cd \"$cwd\" && exec \"./$manage_name\" start" >"$odoo_log" 2>&1 &
        manage_pid=$!
        print_status "Auto-start process launched for Odoo $version (PID: $manage_pid)"
        print_status "Auto-start log: $odoo_log"

        local i=0
        while [ "$i" -lt "$autostart_wait" ]; do
            sleep 1
            i=$((i + 1))
            if is_port_open "$port"; then
                print_status "Odoo $version is now running on port $port"
                return 0
            fi
            if ! kill -0 "$manage_pid" 2>/dev/null; then
                print_warning "Auto-start process for Odoo $version exited before port $port became ready."
                break
            fi
        done
        print_warning "Auto-start timed out for Odoo $version after ${autostart_wait}s"
        print_warning "Recent auto-start log ($odoo_log):"
        tail -30 "$odoo_log" 2>/dev/null || true
    fi

    print_warning "Odoo $version still not detected on port $port (URL: $url)"
    return 1
}

# Setup Python virtual environment with uv
setup_venv() {
    if [ -d "$VENV_DIR" ]; then
        print_status "Using existing virtual environment at $VENV_DIR"
    else
        print_status "Creating new virtual environment with uv..."
        cd "$PROJECT_DIR"
        uv venv "$VENV_DIR"
        print_status "Virtual environment created"
    fi

    # Install requirements
    print_status "Installing/updating packages from requirements.txt..."
    cd "$PROJECT_DIR"
    uv pip install -r requirements.txt --python "$VENV_DIR/bin/python" 2>/dev/null || true
    print_status "Packages installed"
}

# Get Python from venv
get_python() {
    echo "$VENV_DIR/bin/python"
}

# Check if Odoo servers are running
check_odoo_servers() {
    print_header "Checking Odoo servers..."

    # Load env first
    load_env

    local odoo_running=0

    for version in "${ODOO_VERSIONS[@]}"; do
        # Get URL from env based on version
        # Odoo 19 uses ODOO_URL, Odoo 18 uses ODOO18_URL, Odoo 17 uses ODOO17_URL
        local url_var="ODOO_URL"
        if [ "$version" == "17.0" ]; then
            url_var="ODOO17_URL"
        elif [ "$version" == "18.0" ]; then
            url_var="ODOO18_URL"
        fi

        local url="${!url_var:-http://localhost:8069}"
        local port=$(extract_port_from_url "$url")

        if nc -z localhost "$port" 2>/dev/null; then
            print_status "Odoo $version is running on port $port (URL: $url)"
            odoo_running=$((odoo_running + 1))
        else
            print_warning "Odoo $version not found on port $port (URL: $url)"
        fi
    done

    if [ $odoo_running -eq 0 ]; then
        print_warning "No Odoo servers are running. Please start Odoo first."
        return 1
    fi

    return 0
}

# Create log directory
setup_logging() {
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        print_status "Created log directory: $LOG_DIR"
    fi
}

# Load environment variables
load_env() {
    if [ -f "$CONFIG_FILE" ]; then
        # Use source to load .env properly
        set -a
        source "$CONFIG_FILE"
        set +a
        print_status "Loaded configuration from $CONFIG_FILE"
    else
        print_warning "No .env file found at $CONFIG_FILE"
        print_warning "Using default configuration"
    fi
}

# Check if server is already running
check_running() {
    local version="${1:-19.0}"
    local port
    local pid_file
    local version_pid

    CHECK_RUNNING_RESULT="start"
    port=$(get_mcp_port_for_version "$version")
    pid_file=$(get_pid_file_for_version "$version")
    version_pid=$(pgrep -f "odoo_mcp.odoo_mcp_server.*--version $version" | head -n1 || true)

    if [ -n "$version_pid" ]; then
        # Ensure the discovered process is really listening on the expected port.
        local listening_pid
        listening_pid=$(lsof -nP -a -p "$version_pid" -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | head -n1 || true)
        if [ -n "$listening_pid" ]; then
            print_status "MCP Server for Odoo $version is already running (PID: $version_pid, Port: $port)"
            CHECK_RUNNING_RESULT="already_running"
            return 0
        fi
        print_warning "Found MCP process for Odoo $version (PID: $version_pid) but not listening on port $port. Restarting it."
        kill "$version_pid" 2>/dev/null || true
        sleep 1
    fi

    # If pid file exists but process is stale, remove it.
    if [ -f "$pid_file" ]; then
        local pid
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Stopping stale Odoo $version MCP process from PID file: $pid"
            kill "$pid" 2>/dev/null || true
            sleep 1
        fi
        rm -f "$pid_file"
    fi

    # If target port has a LISTEN process, handle carefully.
    # Never kill arbitrary client processes (ESTABLISHED) because that can terminate the test runner.
    local port_pid
    port_pid=$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null | head -n1 || true)
    if [ -n "$port_pid" ]; then
        local port_cmd
        port_cmd=$(ps -p "$port_pid" -o command= 2>/dev/null || true)
        if echo "$port_cmd" | grep -q "odoo_mcp.odoo_mcp_server"; then
            print_warning "Port $port is already used by stale MCP PID $port_pid; stopping it"
            kill "$port_pid" 2>/dev/null || true
            sleep 1
        else
            print_warning "Port $port is in use by non-MCP process (PID: $port_pid)."
            print_warning "Leaving it untouched. Please free port $port manually if startup fails."
        fi
    fi

    return 0
}

# Start the MCP server
start_server() {
    local version="${1:-19.0}"
    local python_bin=$(get_python)
    local port
    local major_version
    local pid_file
    local log_file

    # Load .env so all ODOO* vars are available
    load_env

    print_header "Starting MCP Server..."

    # Setup venv and install dependencies
    setup_venv

    # Add project directory to PYTHONPATH for imports
    export PYTHONPATH="$PROJECT_DIR:$PYTHONPATH"
    cd "$PROJECT_DIR"

    # Determine version-specific MCP port (17→8765, 18→8766, 19→8767)
    major_version=$(get_major_version "$version")
    port=$(get_mcp_port_for_version "$version")
    pid_file=$(get_pid_file_for_version "$version")
    log_file=$(get_log_file_for_version "$version")

    if [ "$major_version" == "19" ] || [ -z "$major_version" ]; then
        local odoo_url="${ODOO_URL:-http://localhost:8069}"
        local odoo_db="${ODOO_DB_NAME:-odoo}"
        local odoo_user="${ODOO_DB_USER:-admin}"
        local odoo_pass="${ODOO_DB_PASSWORD:-admin}"
    elif [ "$major_version" == "18" ]; then
        local odoo_url="${ODOO18_URL:-http://localhost:8018}"
        local odoo_db="${ODOO18_DB_NAME:-odoo18}"
        local odoo_user="${ODOO18_DB_USER:-admin}"
        local odoo_pass="${ODOO18_DB_PASSWORD:-admin}"
    else
        local odoo_url="${ODOO17_URL:-http://localhost:8017}"
        local odoo_db="${ODOO17_DB_NAME:-odoo17}"
        local odoo_user="${ODOO17_DB_USER:-admin}"
        local odoo_pass="${ODOO17_DB_PASSWORD:-admin}"
    fi

    print_status "Starting MCP for Odoo ${version}: URL=$odoo_url DB=$odoo_db Port=$port"

    # Start server — pass version-specific Odoo credentials via env overrides
    # so the MCP server always connects to the RIGHT Odoo instance
    nohup env \
        PYTHONPATH="$PROJECT_DIR:$PYTHONPATH" \
        ODOO_URL="$odoo_url" \
        ODOO_DB_NAME="$odoo_db" \
        ODOO_DB_USER="$odoo_user" \
        ODOO_DB_PASSWORD="$odoo_pass" \
        DEFAULT_ODOO_VERSION="${version}" \
        "$python_bin" -m odoo_mcp.odoo_mcp_server \
            --version "${version}" \
            --transport sse \
            --port "$port" \
        > "$log_file" 2>&1 &

    local pid=$!
    echo $pid > "$pid_file"

    # Wait a moment for server to start
    sleep 3

    if pgrep -f "odoo_mcp.odoo_mcp_server.*--version $version" > /dev/null 2>&1; then
        print_status "MCP Server started successfully!"
        print_status "PID: $(pgrep -f "odoo_mcp.odoo_mcp_server.*--version $version" | head -n1)"
        print_status "Log file: $log_file"
        echo ""
        print_status "Server endpoints:"
        echo "  - MCP Server (SSE): http://localhost:$port/sse"
        return 0
    else
        print_error "Failed to start MCP Server"
        print_error "Check log file: $log_file"
        echo ""
        print_error "Recent log output:"
        tail -30 "$log_file" 2>/dev/null || true
        return 1
    fi
}

# Stop the MCP server
stop_server() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Stopping MCP Server (PID: $pid)..."
            kill "$pid"
            rm -f "$PID_FILE"
            print_status "MCP Server stopped"
        else
            print_warning "MCP Server is not running"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "No PID file found. Server may not be running."
    fi
}

# Stop all MCP server instances
stop_all_servers() {
    print_header "Stopping all MCP Server instances..."

    # Kill by process pattern
    if pkill -f "odoo_mcp.odoo_mcp_server" 2>/dev/null; then
        print_status "Killed all MCP server processes"
    else
        print_warning "No MCP server processes found"
    fi

    # Remove PID files
    for version in "${ODOO_VERSIONS[@]}"; do
        local pid_file="$SCRIPT_DIR/mcp_server_${version/./_}.pid"
        if [ -f "$pid_file" ]; then
            rm -f "$pid_file"
        fi
    done

    # Remove main PID file
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"

    print_status "All MCP Servers stopped"
}

# Start all MCP servers (one per Odoo version)
start_all_servers() {
    print_header "Starting MCP Servers for all Odoo versions..."

    # Load .env first so all ODOO* vars are available
    load_env

    # Setup venv and install dependencies first
    setup_venv
    setup_logging

    local python_bin=$(get_python)

    # Kill any existing instances
    if pkill -f "odoo_mcp.odoo_mcp_server" 2>/dev/null; then
        print_warning "Killed existing MCP server processes"
        sleep 1
    fi

    local started=0
    local failed=0

    for version in "${ODOO_VERSIONS[@]}"; do
        local major=$(echo "$version" | cut -d. -f1)
        local port=$((BASE_PORT + major - 17))   # 17→8765, 18→8766, 19→8767
        local pid_file="$SCRIPT_DIR/mcp_server_${version/./_}.pid"
        local log_file="$LOG_DIR/mcp_server_${version/./_}.log"

        # Pick version-specific Odoo credentials from .env
        if [ "$major" == "19" ]; then
            local odoo_url="${ODOO_URL:-http://localhost:8069}"
            local odoo_db="${ODOO_DB_NAME:-odoo}"
            local odoo_user="${ODOO_DB_USER:-admin}"
            local odoo_pass="${ODOO_DB_PASSWORD:-admin}"
        elif [ "$major" == "18" ]; then
            local odoo_url="${ODOO18_URL:-http://localhost:8018}"
            local odoo_db="${ODOO18_DB_NAME:-odoo18}"
            local odoo_user="${ODOO18_DB_USER:-admin}"
            local odoo_pass="${ODOO18_DB_PASSWORD:-admin}"
        else
            local odoo_url="${ODOO17_URL:-http://localhost:8017}"
            local odoo_db="${ODOO17_DB_NAME:-odoo17}"
            local odoo_user="${ODOO17_DB_USER:-admin}"
            local odoo_pass="${ODOO17_DB_PASSWORD:-admin}"
        fi

        # Ensure matching Odoo instance is up before MCP start.
        ensure_odoo_running_for_version "$version" || true

        print_status "Starting Odoo $version MCP on port $port (URL: $odoo_url, DB: $odoo_db)..."

        cd "$PROJECT_DIR"
        nohup env \
            PYTHONPATH="$PROJECT_DIR:$PYTHONPATH" \
            ODOO_URL="$odoo_url" \
            ODOO_DB_NAME="$odoo_db" \
            ODOO_DB_USER="$odoo_user" \
            ODOO_DB_PASSWORD="$odoo_pass" \
            DEFAULT_ODOO_VERSION="$version" \
            "$python_bin" -m odoo_mcp.odoo_mcp_server \
                --version "$version" \
                --transport sse \
                --port "$port" \
            > "$log_file" 2>&1 &

        local pid=$!
        echo $pid > "$pid_file"

        sleep 2

        if pgrep -f "odoo_mcp.odoo_mcp_server.*--version $version" > /dev/null 2>&1; then
            print_status "Odoo $version MCP Server started (PID: $pid, Port: $port)"
            started=$((started + 1))
        else
            print_error "Failed to start Odoo $version MCP Server"
            print_error "Check log: $log_file"
            failed=$((failed + 1))
        fi
    done

    echo ""
    if [ $failed -eq 0 ]; then
        print_status "All $started MCP Servers started successfully!"
        echo ""
        print_status "Server endpoints (SSE):"
        echo "  - Odoo 17.0: http://localhost:8765/sse"
        echo "  - Odoo 18.0: http://localhost:8766/sse"
        echo "  - Odoo 19.0: http://localhost:8767/sse"
    else
        print_error "$failed servers failed to start"
    fi
}

# Show server status
show_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "MCP Server is running (PID: $pid)"
            print_status "Log file: $LOG_FILE"

            # Show recent log output
            if [ -f "$LOG_FILE" ]; then
                echo ""
                print_status "Recent log entries:"
                tail -10 "$LOG_FILE" 2>/dev/null | sed 's/^/  /'
            fi
        else
            print_warning "MCP Server is not running (stale PID file)"
        fi
    else
        print_warning "MCP Server is not running"
    fi

    # Check for multi-version instances
    echo ""
    print_header "Checking for multi-version instances..."
    for version in "${ODOO_VERSIONS[@]}"; do
        local port=$((BASE_PORT + $(echo "$version" | cut -d. -f1) - 17))
        if pgrep -f "odoo_mcp.odoo_mcp_server.*--version $version" > /dev/null 2>&1; then
            print_status "Odoo $version MCP Server running on port $port (PID: $(pgrep -f "odoo_mcp.odoo_mcp_server.*--version $version"))"
        else
            print_warning "Odoo $version MCP Server not running"
        fi
    done
}

# Show help
show_help() {
    echo "MCP Server Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help           Show this help message"
    echo "  --start          Start the MCP Server"
    echo "  --stop           Stop the MCP Server"
    echo "  --restart        Restart the MCP Server (restarts all if multiple running)"
    echo "  --restart-all    Restart all MCP Servers (all 3 versions)"
    echo "  --status         Show server status"
    echo "  --all            Start all MCP Servers (17, 18, 19)"
    echo "  --stop-all       Stop all MCP Server instances"
    echo "  --version VERSION  Connect to specific Odoo version (17.0, 18.0, or 19.0)"
    echo ""
    echo "Configuration:"
    echo "  - Reads from .env file in project root"
    echo "  - Uses ODOO_URL for Odoo 19, ODOO18_URL for Odoo 18, ODOO17_URL for Odoo 17"
    echo ""
    echo "Multi-Version Mode:"
    echo "  - Starting with --all runs 3 separate MCP servers on ports 8765, 8766, 8767"
    echo "  - Odoo 17.0: port 8765"
    echo "  - Odoo 18.0: port 8766"
    echo "  - Odoo 19.0: port 8767"
    echo ""
    echo "Examples:"
    echo "  $0 --start                    # Start server (default: Odoo 19)"
    echo "  $0 --start --version 17.0    # Start for Odoo 17 only"
    echo "  $0 --all                      # Start all 3 versions at once"
    echo "  $0 --stop-all                 # Stop all running instances"
    echo "  $0 --status                   # Show status"
}

# Main script
main() {
    local action=""
    local start_all=false

    # Parse arguments
    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --start)
                action="start"
                ;;
            --stop)
                action="stop"
                ;;
            --restart)
                action="restart"
                ;;
            --restart-all)
                action="restart_all"
                ;;
            --restart-all)
                action="restart_all"
                ;;
            --status)
                action="status"
                ;;
            --all)
                start_all=true
                ;;
            --stop-all)
                action="stop_all"
                ;;
            --version)
                shift
                if [ -n "$1" ]; then
                    export SPECIFIC_VERSION="$1"
                fi
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done

    # Default action is to show status
    if [ -z "$action" ] && [ "$start_all" = false ]; then
        action="status"
    fi

    # Check if restart should restart all servers
    # If --all was used before, or if multiple servers are running, restart all
    if [ "$action" = "restart" ]; then
        local running_count=0
        for version in "${ODOO_VERSIONS[@]}"; do
            if pgrep -f "odoo_mcp.odoo_mcp_server.*--version $version" > /dev/null 2>&1; then
                running_count=$((running_count + 1))
            fi
        done
        # If multiple versions running, restart all. Also restart all if --all flag was passed
        if [ $running_count -gt 1 ] || [ "$start_all" = true ]; then
            action="restart_all"
        fi
    fi

    # Execute action
    case "$action" in
        start)
            setup_logging
            check_running "${SPECIFIC_VERSION:-19.0}"
            if [ "$CHECK_RUNNING_RESULT" = "already_running" ]; then
                return 0
            fi
            if check_odoo_servers; then
                start_server "${SPECIFIC_VERSION:-}"
            else
                print_warning "Starting MCP Server anyway (Odoo may connect later)..."
                start_server "${SPECIFIC_VERSION:-}"
            fi
            ;;
        stop)
            stop_server
            ;;
        restart)
            stop_server
            sleep 1
            setup_logging
            check_running
            start_server "${SPECIFIC_VERSION:-}"
            ;;
        restart_all)
            print_header "Restarting all MCP Servers..."
            stop_all_servers
            sleep 1
            setup_logging
            setup_venv
            start_all_servers
            ;;
        status)
            show_status
            ;;
        stop_all)
            stop_all_servers
            ;;
    esac

    # Handle --all flag separately (can be combined with start)
    if [ "$start_all" = true ] && [ "$action" != "restart_all" ]; then
        # start_all_servers now auto-starts missing Odoo versions using manage scripts.
        start_all_servers
    fi
}

main "$@"
