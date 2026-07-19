#!/bin/bash
#
# MCP Server Test Script
# Tests Odoo connections using Python validation
# Dynamically loads from .env file like start_mcp_server.sh
#
# Usage:
#   ./test_mcp_server.sh              # Run all tests
#   ./test_mcp_server.sh --odoo17     # Test only Odoo 17
#   ./test_mcp_server.sh --odoo18     # Test only Odoo 18
#   ./test_mcp_server.sh --odoo19     # Test only Odoo 19
#   ./test_mcp_server.sh --mcp        # Test only MCP server
#   ./test_mcp_server.sh --mcp17      # Test MCP server on port 8765 (Odoo 17)
#   ./test_mcp_server.sh --mcp18      # Test MCP server on port 8766 (Odoo 18)
#   ./test_mcp_server.sh --mcp19      # Test MCP server on port 8767 (Odoo 19)
#   ./test_mcp_server.sh --all        # Test all MCP servers
#   ./test_mcp_server.sh --help        # Show help
#

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="$PROJECT_DIR/.env"

# Base ports for multi-version MCP servers
BASE_PORT=8765

# Load env (same as start_mcp_server.sh)
load_env() {
    if [ -f "$CONFIG_FILE" ]; then
        set -a
        source "$CONFIG_FILE"
        set +a
    fi

    # Resolve URLs dynamically from .env (prefer explicit URL, fallback to HTTP port).
    # This keeps test behavior aligned with AgentSkills/.env.
    local odoo17_port="${ODOO17_HTTP_PORT:-8017}"
    local odoo18_port="${ODOO18_HTTP_PORT:-8018}"
    local odoo19_port="${ODOO_HTTP_PORT:-8090}"

    ODOO17_URL="${ODOO17_URL:-http://localhost:${odoo17_port}}"
    ODOO18_URL="${ODOO18_URL:-http://localhost:${odoo18_port}}"
    ODOO_URL="${ODOO_URL:-http://localhost:${odoo19_port}}"

    # Credentials / DB defaults (only used if missing in .env).
    ODOO17_DB_NAME="${ODOO17_DB_NAME:-odoo17}"
    ODOO17_DB_USER="${ODOO17_DB_USER:-admin}"
    ODOO17_DB_PASSWORD="${ODOO17_DB_PASSWORD:-admin}"

    ODOO18_DB_NAME="${ODOO18_DB_NAME:-odoo18}"
    ODOO18_DB_USER="${ODOO18_DB_USER:-admin}"
    ODOO18_DB_PASSWORD="${ODOO18_DB_PASSWORD:-admin}"

    ODOO_DB_NAME="${ODOO_DB_NAME:-odoo}"
    ODOO_DB_USER="${ODOO_DB_USER:-admin}"
    ODOO_DB_PASSWORD="${ODOO_DB_PASSWORD:-admin}"
}

# Extract port from URL
extract_port() {
    local url="$1"
    if [[ "$url" =~ :([0-9]+)$ ]]; then
        echo "${BASH_REMATCH[1]}"
    else
        echo "8069"
    fi
}

print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

print_status() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

# Test Odoo 17 using Python
test_odoo17() {
    print_header "Testing Odoo 17.0 (XML-RPC)"

    local URL="$ODOO17_URL"
    local PORT=$(extract_port "$URL")
    local DB="${ODOO17_DB_NAME:-odoo17}"
    local USER="${ODOO17_DB_USER:-admin}"
    local PASS="${ODOO17_DB_PASSWORD:-admin}"

    echo "URL: $URL"
    echo "Port: $PORT"
    echo "DB: $DB"

    cd "$PROJECT_DIR"

    # Test with Python
    if python3 -c "
import xmlrpc.client
url = '$URL'
db = '$DB'
user = '$USER'
password = '$PASS'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, user, password, {})

if uid:
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    result = models.execute_kw(db, uid, password, 'ir.model', 'search_read', [[['model', 'like', 'res.partner']]], {'limit': 5, 'fields': ['model', 'name']})
    print(f'Found {len(result)} models')
    if len(result) > 0:
        print('SUCCESS')
    else:
        print('FAIL: No models found')
else:
    print('FAIL: Authentication failed')
" 2>&1 | grep -q "SUCCESS"; then
        print_status "Odoo 17.0 connection successful"
        return 0
    else
        print_error "Odoo 17.0 connection failed"
        return 1
    fi
}

# Test Odoo 18 using Python
test_odoo18() {
    print_header "Testing Odoo 18.0 (XML-RPC)"

    local URL="$ODOO18_URL"
    local PORT=$(extract_port "$URL")
    local DB="${ODOO18_DB_NAME:-llmdb18}"
    local USER="${ODOO18_DB_USER:-admin}"
    local PASS="${ODOO18_DB_PASSWORD:-admin}"

    echo "URL: $URL"
    echo "Port: $PORT"
    echo "DB: $DB"

    cd "$PROJECT_DIR"

    if python3 -c "
import xmlrpc.client
url = '$URL'
db = '$DB'
user = '$USER'
password = '$PASS'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, user, password, {})

if uid:
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    result = models.execute_kw(db, uid, password, 'ir.model', 'search_read', [[['model', 'like', 'res.partner']]], {'limit': 5, 'fields': ['model', 'name']})
    print(f'Found {len(result)} models')
    if len(result) > 0:
        print('SUCCESS')
    else:
        print('FAIL: No models found')
else:
    print('FAIL: Authentication failed')
" 2>&1 | grep -q "SUCCESS"; then
        print_status "Odoo 18.0 connection successful"
        return 0
    else
        print_error "Odoo 18.0 connection failed"
        return 1
    fi
}

# Test Odoo 19 using Python
test_odoo19() {
    print_header "Testing Odoo 19.0 (JSON-RPC 2.0)"

    local URL="$ODOO_URL"
    local PORT=$(extract_port "$URL")
    local DB="${ODOO_DB_NAME:-llmdb19}"
    local USER="${ODOO_DB_USER:-admin}"
    local PASS="${ODOO_DB_PASSWORD:-admin}"

    echo "URL: $URL"
    echo "Port: $PORT"
    echo "DB: $DB"

    cd "$PROJECT_DIR"

    if python3 -c "
import json
import urllib.request

url = '$URL'
db = '$DB'
user = '$USER'
password = '$PASS'

# JSON-RPC 2.0 request
req_data = json.dumps({
    'jsonrpc': '2.0',
    'method': 'call',
    'params': {
        'service': 'common',
        'method': 'authenticate',
        'args': [db, user, password, []]
    },
    'id': 1
})

req = urllib.request.Request(
    f'{url}/jsonrpc',
    data=req_data.encode(),
    headers={'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req) as response:
    result = json.loads(response.read())
    uid = result.get('result', 0)

if uid:
    # Test model search
    req_data2 = json.dumps({
        'jsonrpc': '2.0',
        'method': 'call',
        'params': {
            'service': 'object',
            'method': 'execute_kw',
            'args': [db, uid, password, 'ir.model', 'search_read', [[['model', 'like', 'res.partner']]], {'fields': ['model', 'name'], 'limit': 5}]
        },
        'id': 2
    })
    req2 = urllib.request.Request(
        f'{url}/jsonrpc',
        data=req_data2.encode(),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req2) as response2:
        result2 = json.loads(response2.read())
        models = result2.get('result', [])
        print(f'Found {len(models)} models')
        if len(models) > 0:
            print('SUCCESS')
        else:
            print('FAIL: No models found')
else:
    print('FAIL: Authentication failed')
" 2>&1 | grep -q "SUCCESS"; then
        print_status "Odoo 19.0 connection successful"
        return 0
    else
        print_error "Odoo 19.0 connection failed"
        return 1
    fi
}

# Test MCP Server using validation
test_mcp_server() {
    print_header "Testing MCP Server"

    cd "$PROJECT_DIR"

    echo "Running validation script..."
    if python validate_mcp_phase11.py 2>&1; then
        print_status "MCP Server validation passed"
        return 0
    else
        print_error "MCP Server validation failed"
        return 1
    fi
}

# Test MCP server on specific port (for multi-version mode)
test_mcp_port() {
    local version=$1
    local port=$2

    print_header "Testing MCP Server for Odoo $version (port $port)"

    cd "$PROJECT_DIR"

    # Test with curl to check if server is responding
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/" | grep -q "404"; then
        print_status "MCP Server on port $port is responding (HTTP 404 is expected for root)"
    else
        print_warning "MCP Server on port $port may not be running"
    fi

    # Try to get SSE endpoint
    echo "Testing SSE endpoint..."
    if timeout 5 curl -s -N "http://localhost:$port/sse" 2>&1 | head -5; then
        print_status "SSE endpoint accessible"
        return 0
    else
        print_error "SSE endpoint not accessible"
        return 1
    fi
}

# Test all MCP servers in multi-version mode
test_all_mcp_servers() {
    print_header "Testing all MCP Servers (multi-version mode)"

    local passed=0
    local failed=0

    # Test Odoo 17 MCP (port 8765)
    if test_mcp_port "17.0" 8765; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Test Odoo 18 MCP (port 8766)
    if test_mcp_port "18.0" 8766; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    # Test Odoo 19 MCP (port 8767)
    if test_mcp_port "19.0" 8767; then
        passed=$((passed + 1))
    else
        failed=$((failed + 1))
    fi

    print_header "MCP TEST SUMMARY"
    echo -e "Passed: ${GREEN}$passed${NC}"
    echo -e "Failed: ${RED}$failed${NC}"

    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}ALL MCP TESTS PASSED!${NC}"
        return 0
    else
        echo -e "${RED}SOME MCP TESTS FAILED${NC}"
        return 1
    fi
}

# Run all tests
run_all() {
    load_env

    local PASSED=0
    local FAILED=0

    # Test Odoo 17
    if test_odoo17; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi

    # Test Odoo 18
    if test_odoo18; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi

    # Test Odoo 19
    if test_odoo19; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi

    # Test MCP Server
    if test_mcp_server; then
        PASSED=$((PASSED + 1))
    else
        FAILED=$((FAILED + 1))
    fi

    print_header "TEST SUMMARY"
    echo -e "Passed: ${GREEN}$PASSED${NC}"
    echo -e "Failed: ${RED}$FAILED${NC}"

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}ALL TESTS PASSED!${NC}"
        return 0
    else
        echo -e "${RED}SOME TESTS FAILED${NC}"
        return 1
    fi
}

# Show help
show_help() {
    echo "MCP Server Test Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --all        Run all tests (default)"
    echo "  --odoo17     Test only Odoo 17"
    echo "  --odoo18     Test only Odoo 18"
    echo "  --odoo19     Test only Odoo 19"
    echo "  --mcp        Test MCP server (single version)"
    echo "  --mcp17      Test MCP server for Odoo 17 (port 8765)"
    echo "  --mcp18      Test MCP server for Odoo 18 (port 8766)"
    echo "  --mcp19      Test MCP server for Odoo 19 (port 8767)"
    echo "  --all-mcp    Test all MCP servers (multi-version mode)"
    echo "  --help       Show this help message"
}

# Main
main() {
    local test_all=true

    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h)
                show_help
                exit 0
                ;;
            --all)
                test_all=true
                ;;
            --odoo17)
                test_all=false
                load_env
                test_odoo17
                exit $?
                ;;
            --odoo18)
                test_all=false
                load_env
                test_odoo18
                exit $?
                ;;
            --odoo19)
                test_all=false
                load_env
                test_odoo19
                exit $?
                ;;
            --mcp)
                test_all=false
                test_mcp_server
                exit $?
                ;;
            --mcp17)
                test_all=false
                test_mcp_port "17.0" 8765
                exit $?
                ;;
            --mcp18)
                test_all=false
                test_mcp_port "18.0" 8766
                exit $?
                ;;
            --mcp19)
                test_all=false
                test_mcp_port "19.0" 8767
                exit $?
                ;;
            --all-mcp)
                test_all=false
                test_all_mcp_servers
                exit $?
                ;;
            *)
                echo "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done

    if [ "$test_all" = true ]; then
        run_all
    fi
}

main "$@"
