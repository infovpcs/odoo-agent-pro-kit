#!/bin/bash

# ============================================================================
# ODOO Module Management Script - Universal Multi-Version Support
# Supports: Odoo 17.0, 18.0, 19.0
# Features: Module installation, updates, testing, error filtering for AI agents
# ============================================================================

set -e  # Exit on any error

# ============================================================================
# CONFIGURATION
# ============================================================================

# Version detection (can be overridden via environment or argument)
WORKSPACE_PATH="${WORKSPACE_PATH:-.}"
ODOO_EXECUTOR="${ODOO_EXECUTOR:-local}"
if [ -z "${ODOO_VERSION:-}" ]; then
    if [ -d "$WORKSPACE_PATH/19.0" ]; then
        ODOO_VERSION="19"
    elif [ -d "$WORKSPACE_PATH/18.0" ]; then
        ODOO_VERSION="18"
    elif [ -d "$WORKSPACE_PATH/17.0" ]; then
        ODOO_VERSION="17"
    elif [ -d "$WORKSPACE_PATH/16.0" ]; then
        ODOO_VERSION="16"
    elif [ -d "$WORKSPACE_PATH/15.0" ]; then
        ODOO_VERSION="15"
    elif [ -d "$WORKSPACE_PATH/14.0" ]; then
        ODOO_VERSION="14"
    elif [ -d "$WORKSPACE_PATH/13.0" ]; then
        ODOO_VERSION="13"
    elif [ -d "$WORKSPACE_PATH/12.0" ]; then
        ODOO_VERSION="12"
    else
        ODOO_VERSION="19"
    fi
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Dynamic configuration based on version
PROJECT_DIR="$WORKSPACE_PATH"
ODOO_DIR="$PROJECT_DIR/${ODOO_VERSION}.0"
# Try config file in multiple locations for maximum robustness (root or config/)
if [ -f "$SCRIPT_DIR/config/odoo.conf.${ODOO_VERSION}" ]; then
    CONFIG_FILE="$SCRIPT_DIR/config/odoo.conf.${ODOO_VERSION}"
elif [ -f "$PROJECT_DIR/config/odoo.conf.${ODOO_VERSION}" ]; then
    CONFIG_FILE="$PROJECT_DIR/config/odoo.conf.${ODOO_VERSION}"
elif [ -f "$SCRIPT_DIR/odoo.conf.${ODOO_VERSION}" ]; then
    CONFIG_FILE="$SCRIPT_DIR/odoo.conf.${ODOO_VERSION}"
elif [ -f "$PROJECT_DIR/odoo.conf.${ODOO_VERSION}" ]; then
    CONFIG_FILE="$PROJECT_DIR/odoo.conf.${ODOO_VERSION}"
elif [ -f "$SCRIPT_DIR/config/odoo.conf" ]; then
    CONFIG_FILE="$SCRIPT_DIR/config/odoo.conf"
elif [ -f "$PROJECT_DIR/config/odoo.conf" ]; then
    CONFIG_FILE="$PROJECT_DIR/config/odoo.conf"
elif [ -f "$SCRIPT_DIR/odoo.conf" ]; then
    CONFIG_FILE="$SCRIPT_DIR/odoo.conf"
elif [ -f "$PROJECT_DIR/odoo.conf" ]; then
    CONFIG_FILE="$PROJECT_DIR/odoo.conf"
else
    # Fallback to standard template path
CONFIG_FILE="$PROJECT_DIR/config/odoo.conf.${ODOO_VERSION}"
fi
# Use script directory for logs and other output if PROJECT_DIR is just "."
if [ "$PROJECT_DIR" = "." ] || [ "$PROJECT_DIR" = "" ]; then
    LOG_DIR="$SCRIPT_DIR/logs"
else
    LOG_DIR="$PROJECT_DIR/logs"
fi
CONFIG_FILE="${ODOO_EXEC_CONFIG_FILE:-${ODOO_CONFIG_FILE:-$CONFIG_FILE}}"
LOG_DIR="${ODOO_LOG_DIR:-$LOG_DIR}"
LOG_FILE="${ODOO_LOG_FILE:-$LOG_DIR/odoo.log}"
TEST_LOG_DIR="$LOG_DIR/test_results"
ERROR_REPORT_FILE="$TEST_LOG_DIR/error_report.json"
CUSTOM_ADDONS_DIR="${ODOO_CUSTOM_ADDONS:-$PROJECT_DIR/extra-${ODOO_VERSION}}"
ALT_CUSTOM_ADDONS_DIR="$PROJECT_DIR/custom_addons"

get_config_value() {
    local key="$1"
    local file="$2"
    if [ -f "$file" ]; then
        awk -F '=' -v key="$key" '
            $1 ~ "^[[:space:]]*" key "[[:space:]]*$" {
                value=$2
                sub(/^[[:space:]]+/, "", value)
                sub(/[[:space:]]+$/, "", value)
                print value
                exit
            }
        ' "$file"
    fi
}

# Version-specific defaults
DATABASE="${ODOO_DB_NAME:-${DATABASE:-odoo${ODOO_VERSION}}}"
DEFAULT_PORT=$((8090 + ODOO_VERSION))  # 8107, 8108, 8109
PORT_FROM_CONFIG="$(get_config_value "http_port" "$CONFIG_FILE")"
PORT_FROM_XMLRPC="$(get_config_value "xmlrpc_port" "$CONFIG_FILE")"
PORT="${ODOO_PORT:-${PORT_FROM_CONFIG:-${PORT_FROM_XMLRPC:-$DEFAULT_PORT}}}"

# Standard Odoo modules for each version (production-ready apps)
case $ODOO_VERSION in
    12)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 12.0 (Standard Enterprise Apps)"
        ;;
    13)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 13.0 (Standard Enterprise Apps)"
        ;;
    14)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 14.0 (Standard Enterprise Apps)"
        ;;
    15)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 15.0 (Standard Enterprise Apps)"
        ;;
    16)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 16.0 (Standard Enterprise Apps)"
        ;;
    17)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 17.0 (Standard Enterprise Apps)"
        ;;
    18)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 18.0 (Standard Enterprise Apps)"
        ;;
    19)
        DEFAULT_MODULES="sale,purchase,stock,account,crm,project,website"
        VERSION_LABEL="Odoo 19.0 (Standard Enterprise Apps)"
        ;;
    *)
        DEFAULT_MODULES="sale,purchase,stock"
        VERSION_LABEL="Odoo (Default Modules)"
        ;;
esac

# Create necessary directories
mkdir -p "$LOG_DIR" "$TEST_LOG_DIR"

# Compose executor contract. These values are supplied by sandboxctl and may
# also be used directly by automation in an existing session.
COMPOSE_FILE="${COMPOSE_FILE:-}"
COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-odoo}"
COMPOSE_DB_SERVICE="${COMPOSE_DB_SERVICE:-db}"
SESSION_ID="${SESSION_ID:-local-${ODOO_VERSION}-session}"
RESULTS_DIR="${ODOO_RESULTS_DIR:-$TEST_LOG_DIR}"
PROGRESS_FILE="${ODOO_PROGRESS_FILE:-$RESULTS_DIR/module-progress.json}"
mkdir -p "$RESULTS_DIR"

# ============================================================================
# STARTUP & VALIDATION
# ============================================================================

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                   ODOO Module Management System                           ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${CYAN}Configuration:${NC}"
echo -e "  ${CYAN}Version:${NC} $VERSION_LABEL"
echo -e "  ${CYAN}Workspace:${NC} $PROJECT_DIR"
echo -e "  ${CYAN}Database:${NC} $DATABASE"
echo -e "  ${CYAN}Port:${NC} $PORT"
echo -e "  ${CYAN}Config:${NC} $CONFIG_FILE"
echo ""

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

validate_setup() {
    local errors=0
    
    echo -e "${YELLOW}🔍 Validating environment...${NC}"
    
    if [ "$ODOO_EXECUTOR" = "compose" ]; then
        if [ -z "$COMPOSE_FILE" ] || [ -z "$COMPOSE_ENV_FILE" ]; then
            echo -e "${RED}❌ Compose executor requires COMPOSE_FILE and COMPOSE_ENV_FILE${NC}"
            return 1
        fi
        if [ ! -f "$COMPOSE_FILE" ] || [ ! -f "$COMPOSE_ENV_FILE" ]; then
            echo -e "${RED}❌ Compose configuration is missing${NC}"
            return 1
        fi
        docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" ps >/dev/null
        return $?
    fi

    if [ ! -d "$ODOO_DIR" ]; then
        echo -e "${RED}❌ Odoo directory not found: $ODOO_DIR${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ Odoo directory found${NC}"
    fi
    
    if [ ! -f "$CONFIG_FILE" ]; then
        echo -e "${RED}❌ Config file not found: $CONFIG_FILE${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ Config file found${NC}"
    fi
    
    if [ ! -f "$ODOO_DIR/odoo-bin" ]; then
        echo -e "${RED}❌ Odoo binary not found: $ODOO_DIR/odoo-bin${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ Odoo binary found${NC}"
    fi
    
    if [ ! -d "$ODOO_DIR/.venv" ]; then
        echo -e "${RED}❌ Virtual environment not found: $ODOO_DIR/.venv${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✓ Virtual environment found${NC}"
    fi
    
    if [ $errors -gt 0 ]; then
        echo -e "${RED}❌ Validation failed with $errors error(s)${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✓ All validations passed${NC}"
    echo ""
    return 0
}

# ============================================================================
# ERROR EXTRACTION FOR AI AGENTS
# ============================================================================

extract_errors_for_agent() {
    local log_file="$1"
    local error_output="$2"
    local modules="$3"
    local operation="$4"
    
    cat > "$error_output" << EOFHEADER
╔═══════════════════════════════════════════════════════════════════════════╗
║                  ODOO MODULE ${operation^^} ERROR REPORT                    ║
║                    (AI AGENT CONTEXT - AUTO-PARSED)                        ║
╚═══════════════════════════════════════════════════════════════════════════╝

📊 OPERATION METADATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
Operation: $operation
Modules: $modules
Odoo Version: ${ODOO_VERSION}.0
Database: $DATABASE
Port: $PORT
Config: $CONFIG_FILE
Log File: $log_file

🔍 ERROR CATEGORIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOFHEADER

    local has_errors=false
    
    # 1. Critical Errors
    if grep -q "CRITICAL\|FATAL\|Failed to initialize\|Failed to load registry" "$log_file"; then
        has_errors=true
        echo "🔴 CRITICAL ERRORS:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        grep -B 5 -A 15 "CRITICAL\|FATAL\|Failed to initialize\|Failed to load registry" "$log_file" 2>/dev/null | head -150 >> "$error_output" || true
        echo "" >> "$error_output"
    fi
    
    # 2. Parse/XML Errors
    if grep -q "ParseError.*while parsing\|Error while validating view\|view error" "$log_file"; then
        has_errors=true
        echo "📄 VIEW/XML PARSE ERRORS:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        grep -B 3 -A 10 "ParseError.*while parsing\|Error while validating view" "$log_file" 2>/dev/null | head -100 >> "$error_output" || true
        echo "" >> "$error_output"
        
        # Field/Model Errors
        if grep -q "Field.*does not exist\|Model.*not found" "$log_file"; then
            echo "🏗️  FIELD/MODEL ERRORS:" >> "$error_output"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
            grep "Field.*does not exist\|Model.*not found" "$log_file" 2>/dev/null >> "$error_output" || true
            echo "" >> "$error_output"
        fi
    fi
    
    # 3. Python Traceback
    if grep -q "Traceback (most recent call last)" "$log_file"; then
        has_errors=true
        echo "📋 PYTHON TRACEBACKS:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        awk '/Traceback \(most recent call last\)/{flag=1; count++} flag{print} /^[^ ]/ && flag && !/Traceback/{flag=0} count>=3{exit}' "$log_file" >> "$error_output" 2>/dev/null || true
        echo "" >> "$error_output"
    fi
    
    # 4. Syntax Errors
    if grep -q "SyntaxError\|IndentationError" "$log_file"; then
        has_errors=true
        echo "🐍 PYTHON SYNTAX ERRORS:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        grep -B 3 -A 5 "SyntaxError\|IndentationError" "$log_file" 2>/dev/null | head -50 >> "$error_output" || true
        echo "" >> "$error_output"
    fi
    
    # 5. Import Errors
    if grep -q "ImportError\|ModuleNotFoundError" "$log_file"; then
        has_errors=true
        echo "📦 IMPORT ERRORS:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        grep -B 2 -A 3 "ImportError\|ModuleNotFoundError" "$log_file" 2>/dev/null | head -50 >> "$error_output" || true
        echo "" >> "$error_output"
    fi
    
    # 6. Database Errors
    if grep -q "DatabaseError\|IntegrityError\|OperationalError" "$log_file"; then
        has_errors=true
        echo "🗄️  DATABASE ERRORS:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        grep -B 3 -A 5 "DatabaseError\|IntegrityError\|OperationalError" "$log_file" 2>/dev/null | head -50 >> "$error_output" || true
        echo "" >> "$error_output"
    fi
    
    # 7. Dependency Errors
    if grep -q "dependency.*not found\|depends.*not found" "$log_file"; then
        has_errors=true
        echo "🔗 DEPENDENCY ERRORS:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        grep -B 2 -A 3 "dependency.*not found\|depends.*not found" "$log_file" 2>/dev/null >> "$error_output" || true
        echo "" >> "$error_output"
    fi
    
    # 8. Warnings
    if grep -q "WARNING" "$log_file"; then
        echo "⚠️  WARNINGS (Last 20):" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        grep "WARNING" "$log_file" 2>/dev/null | tail -20 >> "$error_output" || true
        echo "" >> "$error_output"
    fi
    
    # 9. Fallback
    if [ "$has_errors" = false ]; then
        echo "📋 LAST 50 LINES OF LOG:" >> "$error_output"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$error_output"
        tail -50 "$log_file" >> "$error_output" 2>/dev/null || true
        echo "" >> "$error_output"
    fi
    
    # Troubleshooting section
    add_troubleshooting_section "$error_output" "$ODOO_VERSION"
}

add_troubleshooting_section() {
    local error_output="$1"
    local version="$2"
    
    cat >> "$error_output" << 'EOFTRBL'

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 TROUBLESHOOTING & RECOVERY STEPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. 📖 REVIEW ERRORS (Priority Order):
   → CRITICAL ERRORS (immediate issue)
   → FIELD/MODEL ERRORS (data model issues)
   → SYNTAX ERRORS (code issues)
   → IMPORT ERRORS (dependency issues)
   → DATABASE ERRORS (data issues)

2. 💡 QUICK FIX COMMANDS:

   # Show full error context
   tail -200 $LOG_FILE | grep -A 30 'ERROR\|CRITICAL'

   # Clear cache and retry
   rm -rf ~/.local/share/Odoo/*
   
   # Check database exists
   psql -l | grep $DATABASE

   # View config file
   cat $CONFIG_FILE

3. 🔄 RETRY PROCEDURE:
   a) Apply fix based on error type
   b) Save file changes
   c) Run installation again
   d) Check error log for new errors

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ ERROR EXTRACTION COMPLETE - Ready for AI Agent Analysis
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EOFTRBL
}

# ============================================================================
# CORE FUNCTIONS
# ============================================================================

compose_run() {
    docker compose --env-file "$COMPOSE_ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

module_is_installed() {
    local module="$1"
    if [ "$ODOO_EXECUTOR" = "compose" ]; then
        compose_run exec -T "$COMPOSE_DB_SERVICE" psql -U "${POSTGRES_USER:-odoo_runtime}" -d "$DATABASE" -Atqc \
            "SELECT 1 FROM ir_module_module WHERE name = '$module' AND state = 'installed' LIMIT 1" 2>/dev/null | grep -qx 1
    else
        psql -d "$DATABASE" -Atqc \
            "SELECT 1 FROM ir_module_module WHERE name = '$module' AND state = 'installed' LIMIT 1" 2>/dev/null | grep -qx 1
    fi
}

write_progress_state() {
    local module="$1" operation="$2" status="$3" result_file="$4"
    python3 - "$PROGRESS_FILE" "$SESSION_ID" "$module" "$operation" "$status" "$result_file" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
data = {}
if path.exists():
    try: data = json.loads(path.read_text())
    except json.JSONDecodeError: data = {}
data.update({"session_id": sys.argv[2], "module": sys.argv[3], "last_operation": sys.argv[4],
             "last_status": sys.argv[5], "last_result": sys.argv[6]})
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(data, indent=2) + "\n")
PY
}

emit_operation_result() {
    local operation="$1"
    local module="$2" started_epoch="$3" exit_code="$4" operation_log="$5"
    local status="succeeded" error_code="" result_file
    [ "$exit_code" -eq 0 ] || { status="failed"; error_code="${operation}_failed"; }
    result_file="$RESULTS_DIR/${operation}-$(date +%s)-$$.json"
    python3 - "$result_file" "$SESSION_ID" "$operation" "$module" "$started_epoch" "$exit_code" "$operation_log" "$status" "$error_code" <<'PY'
import datetime, json, pathlib, sys, time
target, session, operation, module, started, code, log, status, error_code = sys.argv[1:]
started = int(started)
now = datetime.datetime.now(datetime.timezone.utc)
data = {"schema_version":"1.0.0", "session_id":session, "operation_id":pathlib.Path(target).stem,
        "operation":operation, "module":module, "attempt":1, "status":status,
        "started_at":datetime.datetime.fromtimestamp(started, datetime.timezone.utc).isoformat().replace("+00:00","Z"),
        "finished_at":now.isoformat().replace("+00:00","Z"), "duration_ms":max(0, int((time.time()-started)*1000)),
        "exit_code":int(code), "message":None, "logs":[log], "artifacts":[], "error":None}
if error_code:
    data["error"]={"code":error_code, "summary":f"{operation} failed; inspect {log}", "diagnostic_bundle":None}
pathlib.Path(target).write_text(json.dumps(data, indent=2)+"\n")
PY
    write_progress_state "$module" "$operation" "$status" "$result_file"
    echo "RESULT_FILE=$result_file"
}

compose_module_operation() {
    local requested="$1" modules="$2"
    local operation="$requested" flag="--update" rc=0
    local test_args=() http_args=(--no-http)
    local started operation_log module
    started=$(date +%s)
    operation_log="$TEST_LOG_DIR/${requested}_$(date '+%Y%m%d_%H%M%S').log"
    module="${modules%%,*}"

    validate_setup || rc=$?
    if [ "$rc" -eq 0 ] && [ "$requested" = "install" ] && module_is_installed "$module"; then
        operation="update"
        echo "Module $module is already installed in $DATABASE; resolving install request to update."
    fi
    [ "$operation" = "install" ] && flag="--init"
    if [ "$operation" = "test" ]; then
        test_args=(--test-enable)
        # QWeb PDF rendering fetches report assets from Odoo itself.  Disabling
        # HTTP makes wkhtmltopdf emit unstyled output or hang on localhost.
        http_args=()
    fi

    if [ "$rc" -eq 0 ]; then
        compose_run stop "$COMPOSE_SERVICE" >>"$operation_log" 2>&1 || rc=$?
    fi
    if [ "$rc" -eq 0 ]; then
        compose_run run --rm -T "$COMPOSE_SERVICE" odoo --config "$CONFIG_FILE" --database "$DATABASE" \
            "$flag" "$modules" "${test_args[@]}" --stop-after-init "${http_args[@]}" >>"$operation_log" 2>&1 || rc=$?
    fi
    compose_run up -d --wait --wait-timeout "${ODOO_READY_TIMEOUT:-180}" "$COMPOSE_SERVICE" >>"$operation_log" 2>&1 || [ "$rc" -ne 0 ] || rc=$?
    # Odoo's -i/-u CLI path treats an unresolvable module dependency as a
    # skip-with-warning, not a hard error, so a clean exit code alone does
    # not prove the requested module actually reached the "installed"
    # state (e.g. a missing Enterprise dependency leaves it stuck at
    # "to install" while the CLI still exits 0). Verify the true database
    # state for install/update operations before reporting success.
    if [ "$rc" -eq 0 ] && { [ "$operation" = "install" ] || [ "$operation" = "update" ]; }; then
        if ! module_is_installed "$module"; then
            rc=1
            echo "Module $module did not reach 'installed' state after $operation (check for missing/uninstallable dependencies)" >>"$operation_log"
        fi
    fi
    emit_operation_result "$operation" "$module" "$started" "$rc" "$operation_log"
    return "$rc"
}

show_usage() {
    echo -e "${CYAN}Usage: $0 <command> [modules] [options]${NC}"
    echo ""
    echo -e "${CYAN}Commands:${NC}"
    echo -e "  ${YELLOW}install [modules]     ${NC}Install modules (default: standard apps)"
    echo -e "  ${YELLOW}update [modules]      ${NC}Update modules"
    echo -e "  ${YELLOW}test [modules]        ${NC}Run tests"
    echo -e "  ${YELLOW}start                 ${NC}Start Odoo server"
    echo -e "  ${YELLOW}stop                  ${NC}Stop Odoo server"
    echo -e "  ${YELLOW}restart               ${NC}Restart Odoo server"
    echo -e "  ${YELLOW}status                ${NC}Check system status"
    echo -e "  ${YELLOW}logs                  ${NC}Show recent logs"
    echo -e "  ${YELLOW}clean                 ${NC}Clean logs and cache"
    echo ""
    echo -e "${CYAN}Environment Variables:${NC}"
    echo -e "  ${YELLOW}ODOO_VERSION          ${NC}Version: 12-19 (default: auto-detect)"
    echo -e "  ${YELLOW}WORKSPACE_PATH        ${NC}Workspace path (default: current dir)"
    echo -e "  ${YELLOW}DATABASE              ${NC}Database name (default: odoo${ODOO_VERSION})"
    echo ""
    echo -e "${CYAN}Examples:${NC}"
    echo -e "  ./manage_modules.sh install                    # Install standard modules"
    echo -e "  ./manage_modules.sh install sale,purchase      # Install specific modules"
    echo -e "  ODOO_VERSION=17 ./manage_modules.sh install    # Use Odoo 17"
    echo -e "  WORKSPACE_PATH=/path/to/ws ./manage_modules.sh start"
    echo ""
    echo -e "${CYAN}Default Modules (per version):${NC}"
    echo -e "  All versions: ${DEFAULT_MODULES}"
}

kill_odoo_processes() {
    echo -e "${YELLOW}🔄 Checking for processes on port $PORT...${NC}"
    
    local PIDS=$(lsof -t -i:$PORT 2>/dev/null || true)
    
    if [ -n "$PIDS" ]; then
        echo -e "${YELLOW}🛑 Terminating processes on port $PORT...${NC}"
        for pid in $PIDS; do
            kill -TERM $pid 2>/dev/null || true
            sleep 2
            if kill -0 $pid 2>/dev/null; then
                kill -KILL $pid 2>/dev/null || true
            fi
        done
        sleep 3
    fi
}

setup_environment() {
    cd "$ODOO_DIR" || return 1
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        ensure_python_runtime_deps || return 1
    else
        echo -e "${RED}❌ Virtual environment not found${NC}"
        return 1
    fi
}

ensure_python_runtime_deps() {
    local py_bin=".venv/bin/python"

    # Odoo 17 imports pkg_resources from setuptools. Newer setuptools releases
    # may not provide it, so keep an explicit compatibility guard.
    if ! "$py_bin" -c "import pkg_resources" >/dev/null 2>&1; then
        echo -e "${YELLOW}📦 Missing pkg_resources, bootstrapping venv tooling...${NC}"

        "$py_bin" -m ensurepip --upgrade >/dev/null 2>&1 || true

        if ! "$py_bin" -m pip --version >/dev/null 2>&1; then
            echo -e "${RED}❌ pip is unavailable in $ODOO_DIR/.venv${NC}"
            return 1
        fi

        if ! "$py_bin" -m pip install --disable-pip-version-check "setuptools<81" >/dev/null 2>&1; then
            echo -e "${RED}❌ Failed to install setuptools compatibility package${NC}"
            return 1
        fi

        if ! "$py_bin" -c "import pkg_resources" >/dev/null 2>&1; then
            echo -e "${RED}❌ pkg_resources still missing after repair${NC}"
            return 1
        fi

        echo -e "${GREEN}✅ Python runtime dependencies repaired${NC}"
    fi
}

install_module_requirements() {
    # Install module-specific Python dependencies from requirements.txt if present
    local modules_list=$(echo "$1" | tr ',' ' ')
    for module in $modules_list; do
        local req_path=""
        for candidate in "$CUSTOM_ADDONS_DIR/$module" "$ALT_CUSTOM_ADDONS_DIR/$module" "$ODOO_DIR/addons/$module"; do
            if [ -f "$candidate/requirements.txt" ]; then
                req_path="$candidate/requirements.txt"
                break
            fi
        done
        if [ -n "$req_path" ]; then
            echo -e "${YELLOW}📦 Installing Python deps for $module (requirements.txt)${NC}"
            pip install -r "$req_path"
        fi
    done
}

install_modules() {
    local modules="${1:-$DEFAULT_MODULES}"
    if [ "$ODOO_EXECUTOR" = "compose" ]; then
        compose_module_operation install "$modules"
        return $?
    fi
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local install_log="$TEST_LOG_DIR/install_${timestamp}.log"
    local error_log="$LOG_DIR/install_errors_${timestamp}.log"
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}INSTALLING MODULES (Odoo ${ODOO_VERSION})${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${CYAN}Modules: $modules${NC}"
    echo -e "${CYAN}Install Log: $install_log${NC}"
    echo ""
    
    validate_setup || return 1
    kill_odoo_processes
    setup_environment || return 1
    install_module_requirements "$modules"
    
    echo -e "${YELLOW}🚀 Starting installation...${NC}"
    
    : > "$LOG_FILE" 2>/dev/null || true
    
    local install_exit_code=0
    ./odoo-bin -c "$CONFIG_FILE" -d "$DATABASE" -i "$modules" --test-enable --stop-after-init --log-level=info &> "$install_log" || install_exit_code=$?
    
    if grep -q "Modules loaded\|Registry loaded" "$install_log" 2>/dev/null || grep -q "Modules loaded\|Registry loaded" "$LOG_FILE" 2>/dev/null; then
        echo -e "${GREEN}✅ Installation successful!${NC}"
        echo -e "${CYAN}Log: $install_log${NC}"
        return 0
    else
        echo -e "${RED}❌ Installation failed${NC}"
        extract_errors_for_agent "$LOG_FILE" "$error_log" "$modules" "install"
        echo -e "${CYAN}Error log: $error_log${NC}"
        return 1
    fi
}

update_modules() {
    local modules="${1:-$DEFAULT_MODULES}"
    if [ "$ODOO_EXECUTOR" = "compose" ]; then
        compose_module_operation update "$modules"
        return $?
    fi
    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local update_log="$TEST_LOG_DIR/update_${timestamp}.log"
    local error_log="$LOG_DIR/update_errors_${timestamp}.log"
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}UPDATING MODULES (Odoo ${ODOO_VERSION})${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${CYAN}Modules: $modules${NC}"
    echo ""
    
    validate_setup || return 1
    kill_odoo_processes
    setup_environment || return 1
    
    echo -e "${YELLOW}🔄 Starting update...${NC}"
    
    : > "$LOG_FILE" 2>/dev/null || true
    
    local update_exit_code=0
    ./odoo-bin -c "$CONFIG_FILE" -d "$DATABASE" -u "$modules" --stop-after-init --log-level=info &> "$update_log" || update_exit_code=$?
    
    if grep -q "Modules loaded\|Registry loaded\|update completed" "$update_log" 2>/dev/null || grep -q "Modules loaded\|Registry loaded" "$LOG_FILE" 2>/dev/null; then
        echo -e "${GREEN}✅ Update successful!${NC}"
        return 0
    else
        echo -e "${RED}❌ Update failed${NC}"
        extract_errors_for_agent "$LOG_FILE" "$error_log" "$modules" "update"
        echo -e "${CYAN}Error log: $error_log${NC}"
        return 1
    fi
}

run_tests() {
    local modules="${1:-$DEFAULT_MODULES}"
    if [ "$ODOO_EXECUTOR" = "compose" ]; then
        compose_module_operation test "$modules"
        return $?
    fi
    
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}RUNNING TESTS (Odoo ${ODOO_VERSION})${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${CYAN}Modules: $modules${NC}"
    echo ""
    
    validate_setup || return 1
    kill_odoo_processes
    setup_environment || return 1
    
    echo -e "${YELLOW}🧪 Running tests...${NC}"
    ./odoo-bin -c "$CONFIG_FILE" -d "$DATABASE" -i "$modules" --test-enable --stop-after-init --log-level=test
}

start_server() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}STARTING ODOO ${ODOO_VERSION} SERVER${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    validate_setup || return 1
    kill_odoo_processes
    setup_environment || return 1
    
    # Start MCP server dynamically
    local version="${ODOO_VERSION}.0"
    local mcp_script
    mcp_script="$(resolve_mcp_script || true)"
    
    if [ -n "$mcp_script" ]; then
        echo -e "${YELLOW}📡 Starting MCP Server for Odoo $version...${NC}"
        bash "$mcp_script" --start --version "$version" || echo -e "${RED}⚠️ Failed to start MCP Server${NC}"
    else
        echo -e "${YELLOW}⚠️ MCP Server script not found, skipping automation.${NC}"
    fi

    echo -e "${YELLOW}🚀 Starting server on port $PORT...${NC}"
    echo -e "${GREEN}Access at: http://localhost:$PORT${NC}"
    echo ""
    
    # Run Odoo as appropriate user if we are root
    if [ "$EUID" -eq 0 ]; then
        echo -e "${YELLOW}Running as user 'root' is a security risk.${NC}"
        # We will still run it, but usually this is discouraged. 
    fi
    ./odoo-bin -c "$CONFIG_FILE" -d "$DATABASE" --log-level=info
}

stop_server() {
    echo -e "${BLUE}Stopping Odoo server...${NC}"
    kill_odoo_processes
    
    # Stop MCP server dynamically
    local mcp_script
    mcp_script="$(resolve_mcp_script || true)"

    if [ -n "$mcp_script" ]; then
        echo -e "${YELLOW}📡 Stopping MCP Server...${NC}"
        bash "$mcp_script" --stop --version "${ODOO_VERSION}.0" || true
    fi

    echo -e "${GREEN}✅ Server stopped${NC}"
}

restart_server() {
    stop_server
    sleep 2
    start_server
}

check_status() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}SYSTEM STATUS (Odoo ${ODOO_VERSION})${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    
    echo -e "${CYAN}Configuration:${NC}"
    echo -e "  Workspace: $([ -d "$PROJECT_DIR" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}") $PROJECT_DIR"
    echo -e "  Odoo Dir: $([ -d "$ODOO_DIR" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}") $ODOO_DIR"
    echo -e "  Config: $([ -f "$CONFIG_FILE" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}") $CONFIG_FILE"
    echo -e "  Database: $DATABASE (Port: $PORT)"
    echo ""
    
    echo -e "${CYAN}Running Processes:${NC}"
    if lsof -i :$PORT 2>/dev/null | grep -q LISTEN; then
        echo -e "  ${GREEN}✓ Odoo server running on port $PORT${NC}"
    else
        echo -e "  ${YELLOW}○ No process on port $PORT${NC}"
    fi
    echo ""

    # Check MCP server status
    local mcp_script
    mcp_script="$(resolve_mcp_script || true)"

    if [ -n "$mcp_script" ]; then
        echo -e "${CYAN}📡 MCP Server status:${NC}"
        bash "$mcp_script" --status || echo -e "${RED}❌ Failed to get MCP status${NC}"
    fi
     echo ""
    
    echo -e "${CYAN}Recent Log Activity:${NC}"
    if [ -f "$LOG_FILE" ]; then
        tail -5 "$LOG_FILE" | sed 's/^/  /'
    else
        echo -e "  ${YELLOW}No logs found${NC}"
    fi
}

show_logs() {
    echo -e "${BLUE}Recent Logs (Odoo ${ODOO_VERSION}):${NC}"
    [ -f "$LOG_FILE" ] && tail -100 "$LOG_FILE" || echo "No logs found"
}

clean_environment() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}CLEANING ENVIRONMENT${NC}"
    echo -e "${BLUE}========================================${NC}"
    
    kill_odoo_processes
    
    echo -e "${YELLOW}Removing cache and temporary files...${NC}"
    rm -rf "$LOG_DIR"/*.log 2>/dev/null || true
    rm -rf "$LOG_DIR/test_results"/*.log 2>/dev/null || true
    rm -rf ~/.local/share/Odoo/* 2>/dev/null || true
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

resolve_mcp_script() {
    local possible_paths=(
        "$PROJECT_DIR/Agents/odoo_mcp/start_mcp_server.sh"
        "$PROJECT_DIR/.gemini/AgentSkills/odoo_mcp/start_mcp_server.sh"
        "$PROJECT_DIR/.github/AgentSkills/odoo_mcp/start_mcp_server.sh"
        "$PROJECT_DIR/.cursor/AgentSkills/odoo_mcp/start_mcp_server.sh"
        "$WORKSPACE_PATH/AgentSkills/odoo_mcp/start_mcp_server.sh"
        "${ODOO_AGENT_PRO_KIT_HOME:-}/plugin/odoo_mcp/start_mcp_server.sh"
    )

    local path
    for path in "${possible_paths[@]}"; do
        if [ -f "$path" ]; then
            echo "$path"
            return 0
        fi
    done
    return 1
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

main() {
    local command="${1:-help}"
    local modules="$2"
    
    case "$command" in
        "install")
            install_modules "$modules"
            ;;
        "update")
            update_modules "$modules"
            ;;
        "test")
            run_tests "$modules"
            ;;
        "start")
            start_server
            ;;
        "stop")
            stop_server
            ;;
        "restart")
            restart_server
            ;;
        "status")
            check_status
            ;;
        "logs")
            show_logs
            ;;
        "clean")
            clean_environment
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        "test-all")
            run_all_tests
            ;;
        "mcp-start")
            echo -e "${YELLOW}🚀 Starting MCP server for Odoo $ODOO_VERSION...${NC}"
            mcp_script="$(resolve_mcp_script || true)"
            if [ -n "$mcp_script" ]; then
                bash "$mcp_script" --start --version "${ODOO_VERSION}.0"
            else
                echo -e "${RED}❌ MCP start script not found${NC}"
                exit 1
            fi
            ;;
        "mcp-stop")
            echo -e "${YELLOW}🛑 Stopping MCP server for Odoo $ODOO_VERSION...${NC}"
            mcp_script="$(resolve_mcp_script || true)"
            if [ -n "$mcp_script" ]; then
                bash "$mcp_script" --stop --version "${ODOO_VERSION}.0"
            else
                echo -e "${RED}❌ MCP start script not found${NC}"
                exit 1
            fi
            ;;
        "mcp-status")
            mcp_script="$(resolve_mcp_script || true)"
            if [ -n "$mcp_script" ]; then
                bash "$mcp_script" --status
            else
                echo -e "${RED}❌ MCP start script not found${NC}"
                exit 1
            fi
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $command${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

trap "echo -e '\n${YELLOW}⚠️  Operation interrupted${NC}'; exit 130" INT

main "$@"
