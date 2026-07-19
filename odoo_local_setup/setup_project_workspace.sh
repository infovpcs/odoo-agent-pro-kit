#!/bin/bash
# =============================================================================
# setup_project_workspace.sh — Add a Project to an Existing Odoo Workspace
# =============================================================================
# Uses the .autoload_repos + symlink pattern so Odoo's addons_path needs no
# changes when you add a new project.
#
# Pattern:
#   extra-{V}/
#     .autoload_repos/
#       {project_name}/          ← git clone OR symlink to local path
#         module_a/              ← Odoo module (has __manifest__.py)
#         module_b/
#     module_a -> .autoload_repos/{project_name}/module_a  (symlink)
#     module_b -> .autoload_repos/{project_name}/module_b  (symlink)
#
# Enterprise repos are added directly to odoo.conf addons_path (not symlinked
# per-module, since they contain hundreds of modules).
#
# Usage — Mac / local dev (symlink to local project, no git clone):
#   ./setup_project_workspace.sh \
#     --workspace-dir ~/odoo-workspaces/19_workspace \
#     --local-path ~/workspace/MyOdooProject \
#     --project-name MyOdooProject
#
# Usage — VPS / CI (clone from GitHub):
#   ./setup_project_workspace.sh \
#     --workspace-dir ~/odoo-workspaces/19_workspace \
#     --repo-url https://github.com/org/repo.git \
#     --repo-branch Dev-19 \
#     --project-name my_custom_module
#
# Usage — also wire up enterprise:
#   ./setup_project_workspace.sh ... \
#     --ent-repo git@github.com:org/enterprise.git
#
# Options:
#   --workspace-dir DIR   Workspace root  (default: ~/odoo-workspaces/19_workspace)
#   --version VER         Odoo version: 17|18|19  (default: auto-detect)
#   --local-path PATH     Symlink this local directory (Mac/local mode)
#   --repo-url URL        Clone this git repo (VPS/server mode)
#   --repo-branch NAME    Git branch to clone/pull (optional)
#   --project-name NAME   Folder name inside .autoload_repos/
#   --ent-repo URL        Enterprise repo URL (optional)
#   --skip-skills         Skip copying CLAUDE.md and skills
#   --force               Overwrite existing symlinks / re-pull repo
#   -h, --help            Show this help
# =============================================================================

set -euo pipefail

# ─── Colours ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ─── Defaults ────────────────────────────────────────────────────────────────
WORKSPACE_DIR="${HOME}/odoo-workspaces/19_workspace"
VERSION=""
LOCAL_PATH=""
REPO_URL=""
REPO_BRANCH=""
PROJECT_NAME=""
ENT_REPO=""
SKIP_SKILLS=0
FORCE=0

# ─── Helpers ─────────────────────────────────────────────────────────────────
log_info()   { echo -e "${CYAN}ℹ  $*${NC}"; }
log_ok()     { echo -e "${GREEN}✔  $*${NC}"; }
log_warn()   { echo -e "${YELLOW}⚠  $*${NC}"; }
log_error()  { echo -e "${RED}✘  $*${NC}"; }
log_banner() {
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $*${NC}"
    echo -e "${BLUE}══════════════════════════════════════════════════${NC}"
}
die() { log_error "$*"; exit 1; }

detect_version() {
    if   [ -d "${WORKSPACE_DIR}/19.0" ]; then echo "19"
    elif [ -d "${WORKSPACE_DIR}/18.0" ]; then echo "18"
    elif [ -d "${WORKSPACE_DIR}/17.0" ]; then echo "17"
    else echo "19"
    fi
}

# Resolve absolute path (works on macOS without realpath)
abs_path() {
    local p="$1"
    if command -v realpath >/dev/null 2>&1; then
        realpath "$p"
    else
        # macOS fallback
        python3 -c "import os,sys; print(os.path.realpath(sys.argv[1]))" "$p"
    fi
}

# Create/replace a symlink; warn if a real dir/file is in the way
make_link() {
    local target="$1"   # relative or absolute target
    local link="$2"     # path of the symlink to create

    if [ -L "$link" ]; then
        if [ "$FORCE" -eq 1 ]; then
            rm "$link"
        else
            log_warn "Symlink already exists: $(basename "$link")  (use --force to overwrite)"
            return 0
        fi
    elif [ -e "$link" ]; then
        log_warn "Path exists (not a symlink): $link — skipping"
        return 0
    fi
    ln -s "$target" "$link"
    log_ok "Linked: $(basename "$link")"
}

# ─── Step 1: Put project into .autoload_repos/ ───────────────────────────────
setup_autoload_entry() {
    local extra_dir="${WORKSPACE_DIR}/extra-${VERSION}"
    local autoload_dir="${extra_dir}/.autoload_repos"
    local entry="${autoload_dir}/${PROJECT_NAME}"

    mkdir -p "$autoload_dir"

    if [ -n "$LOCAL_PATH" ]; then
        # ── Mac / local mode: symlink the local project directory ──
        local abs_local
        abs_local="$(abs_path "$LOCAL_PATH")"
        [ -d "$abs_local" ] || die "local-path not found: $abs_local"

        if [ -L "$entry" ]; then
            if [ "$FORCE" -eq 1 ]; then
                rm "$entry"
            else
                log_warn ".autoload_repos/${PROJECT_NAME} already linked (use --force to replace)"
                return 0
            fi
        elif [ -d "$entry" ]; then
            log_warn ".autoload_repos/${PROJECT_NAME} directory already exists — skipping link"
            return 0
        fi

        ln -s "$abs_local" "$entry"
        log_ok "Linked project: .autoload_repos/${PROJECT_NAME} → ${abs_local}"

    elif [ -n "$REPO_URL" ]; then
        # ── VPS / server mode: git clone ──
        if [ -d "$entry" ]; then
            if [ "$FORCE" -eq 1 ]; then
                log_info "Updating existing clone: ${PROJECT_NAME}"
                if [ -n "$REPO_BRANCH" ]; then
                    git -C "$entry" fetch origin "$REPO_BRANCH"
                    git -C "$entry" checkout "$REPO_BRANCH"
                    git -C "$entry" pull --ff-only origin "$REPO_BRANCH"
                else
                    git -C "$entry" pull --ff-only
                fi
                log_ok "Updated: ${PROJECT_NAME}"
            else
                log_warn ".autoload_repos/${PROJECT_NAME} already cloned (use --force to pull)"
            fi
        else
            log_info "Cloning ${REPO_URL} → .autoload_repos/${PROJECT_NAME}"
            if [ -n "$REPO_BRANCH" ]; then
                git clone --branch "$REPO_BRANCH" --single-branch "$REPO_URL" "$entry"
            else
                git clone "$REPO_URL" "$entry"
            fi
            log_ok "Cloned: ${PROJECT_NAME}"
        fi
    else
        die "Provide --local-path (Mac) or --repo-url (VPS)"
    fi
}

# ─── Step 2: Symlink each Odoo module into extra-{V}/ ────────────────────────
link_modules() {
    local extra_dir="${WORKSPACE_DIR}/extra-${VERSION}"
    local entry="${extra_dir}/.autoload_repos/${PROJECT_NAME}"

    # Resolve through symlink to find actual modules
    local scan_dir
    if [ -L "$entry" ]; then
        scan_dir="$(abs_path "$entry")"
    else
        scan_dir="$entry"
    fi

    local count=0
    for d in "${scan_dir}"/*/; do
        [ -d "$d" ]                 || continue
        [ -f "${d}__manifest__.py" ] || continue

        local mod_name
        mod_name="$(basename "$d")"
        # Use a relative target so the symlink is portable within the extra dir
        local rel_target=".autoload_repos/${PROJECT_NAME}/${mod_name}"
        make_link "$rel_target" "${extra_dir}/${mod_name}"
        (( count++ )) || true
    done

    if [ "$count" -eq 0 ]; then
        log_warn "No Odoo modules found in ${scan_dir}"
    else
        log_ok "Linked ${count} module(s) from ${PROJECT_NAME} into extra-${VERSION}/"
    fi
}

# ─── Step 3: Clone enterprise and update addons_path ─────────────────────────
setup_enterprise() {
    [ -n "$ENT_REPO" ] || return 0

    local extra_dir="${WORKSPACE_DIR}/extra-${VERSION}"
    local autoload_dir="${extra_dir}/.autoload_repos"
    local ent_dir="${autoload_dir}/ent-${VERSION}"

    if [ -d "$ent_dir" ]; then
        if [ "$FORCE" -eq 1 ]; then
            log_info "Updating enterprise clone..."
            git -C "$ent_dir" pull --ff-only
            log_ok "Enterprise updated"
        else
            log_warn "Enterprise already cloned at ${ent_dir} (use --force to update)"
        fi
    else
        log_info "Cloning enterprise → .autoload_repos/ent-${VERSION}"
        git clone "$ENT_REPO" "$ent_dir"
        log_ok "Enterprise cloned"
    fi

    # Add enterprise dir to odoo.conf addons_path (if not already present)
    local conf
    for candidate in \
        "${WORKSPACE_DIR}/config/odoo.conf.${VERSION}" \
        "${WORKSPACE_DIR}/config/odoo.conf" \
        "${WORKSPACE_DIR}/odoo.conf"; do
        [ -f "$candidate" ] && { conf="$candidate"; break; }
    done

    if [ -z "${conf:-}" ]; then
        log_warn "No odoo.conf found — add ${ent_dir} to addons_path manually"
        return 0
    fi

    if grep -q "ent-${VERSION}" "$conf" 2>/dev/null; then
        log_info "Enterprise path already in ${conf}"
    else
        # Append enterprise path to the existing addons_path line
        local os_type
        os_type="$(uname -s)"
        if [ "$os_type" = "Darwin" ]; then
            sed -i '' "s|^\(addons_path\s*=.*\)|\1,${ent_dir}|" "$conf"
        else
            sed -i "s|^\(addons_path\s*=.*\)|\1,${ent_dir}|" "$conf"
        fi
        log_ok "Added enterprise path to addons_path in $(basename "$conf")"
    fi
}

# ─── Step 4: Copy project context for AI agents ───────────────────────────────
copy_project_context() {
    [ "$SKIP_SKILLS" -eq 1 ] && return 0

    # Determine source dir (local-path has CLAUDE.md / skills; repo is same)
    local src_dir
    if [ -n "$LOCAL_PATH" ]; then
        src_dir="$(abs_path "$LOCAL_PATH")"
    else
        src_dir="${WORKSPACE_DIR}/extra-${VERSION}/.autoload_repos/${PROJECT_NAME}"
    fi

    # ── CLAUDE.md ──
    local claude_dir="${WORKSPACE_DIR}/.claude"
    mkdir -p "$claude_dir"

    local project_claude="${src_dir}/CLAUDE.md"
    local dest_claude="${claude_dir}/CLAUDE.md"

    if [ -f "$project_claude" ]; then
        if [ ! -f "$dest_claude" ] || [ "$FORCE" -eq 1 ]; then
            cp "$project_claude" "$dest_claude"
            log_ok "Copied CLAUDE.md → ${WORKSPACE_DIR}/.claude/CLAUDE.md"
        else
            # Merge: append project section if not already present
            local marker="# ${PROJECT_NAME} project context"
            if ! grep -qF "$marker" "$dest_claude" 2>/dev/null; then
                {
                    echo ""
                    echo "---"
                    echo "$marker"
                    echo ""
                    cat "$project_claude"
                } >> "$dest_claude"
                log_ok "Appended ${PROJECT_NAME} context to existing CLAUDE.md"
            else
                log_info "Project context already in CLAUDE.md — skipping"
            fi
        fi
    else
        log_warn "No CLAUDE.md found in project — skipping"
    fi

    # ── Skills ──
    local src_skills="${src_dir}/skills"
    local dst_skills="${WORKSPACE_DIR}/skills"

    if [ -d "$src_skills" ]; then
        mkdir -p "$dst_skills"
        # Copy skill directories (each sub-dir is one skill)
        local skill_count=0
        for skill_dir in "${src_skills}"/*/; do
            [ -d "$skill_dir" ] || continue
            local skill_name
            skill_name="$(basename "$skill_dir")"
            local dest="${dst_skills}/${skill_name}"
            if [ -d "$dest" ] && [ "$FORCE" -eq 0 ]; then
                log_warn "Skill already exists: ${skill_name} (use --force to overwrite)"
            else
                cp -r "$skill_dir" "$dest"
                log_ok "Copied skill: ${skill_name}"
                (( skill_count++ )) || true
            fi
        done
        # Also copy any top-level skill files
        for skill_file in "${src_skills}"/*.md "${src_skills}"/*.py "${src_skills}"/*.sh; do
            [ -f "$skill_file" ] || continue
            local fname
            fname="$(basename "$skill_file")"
            local dest="${dst_skills}/${fname}"
            if [ -f "$dest" ] && [ "$FORCE" -eq 0 ]; then
                log_warn "Skill file exists: ${fname} (use --force to overwrite)"
            else
                cp "$skill_file" "$dest"
                log_ok "Copied skill file: ${fname}"
                (( skill_count++ )) || true
            fi
        done
        [ "$skill_count" -gt 0 ] && log_ok "Copied ${skill_count} skill(s) to workspace"
    else
        log_info "No skills/ directory in project — skipping skill copy"
    fi

    # ── manage_modules.sh ──
    local dst_manage="${WORKSPACE_DIR}/manage_modules.sh"
    local src_manage="${SCRIPT_DIR}/manage_modules.sh"
    if [ ! -f "$dst_manage" ]; then
        if [ -f "$src_manage" ]; then
            cp "$src_manage" "$dst_manage"
            chmod +x "$dst_manage"
            log_ok "Installed manage_modules.sh"
        else
            log_warn "manage_modules.sh not found in ${SCRIPT_DIR} — skipping"
        fi
    else
        log_info "manage_modules.sh already present in workspace"
    fi
}

# ─── Step 5: Verify odoo.conf addons_path includes extra-{V}/ ────────────────
verify_addons_path() {
    local conf
    for candidate in \
        "${WORKSPACE_DIR}/config/odoo.conf.${VERSION}" \
        "${WORKSPACE_DIR}/config/odoo.conf" \
        "${WORKSPACE_DIR}/odoo.conf"; do
        [ -f "$candidate" ] && { conf="$candidate"; break; }
    done

    if [ -z "${conf:-}" ]; then
        log_warn "No odoo.conf found — ensure extra-${VERSION} is in addons_path"
        return 0
    fi

    local extra_dir="${WORKSPACE_DIR}/extra-${VERSION}"
    if grep -q "extra-${VERSION}" "$conf" 2>/dev/null; then
        log_ok "extra-${VERSION} already in addons_path ($(basename "$conf"))"
    else
        log_warn "extra-${VERSION} not found in addons_path of $(basename "$conf")"
        log_info "Add this to addons_path: ${extra_dir}"
    fi
}

# ─── Argument Parsing ─────────────────────────────────────────────────────────
show_help() {
    sed -n '2,50p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 0
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --workspace-dir) WORKSPACE_DIR="$2"; shift 2 ;;
            --version)       VERSION="$2";       shift 2 ;;
            --local-path)    LOCAL_PATH="$2";    shift 2 ;;
            --repo-url)      REPO_URL="$2";      shift 2 ;;
            --repo-branch)   REPO_BRANCH="$2";   shift 2 ;;
            --project-name)  PROJECT_NAME="$2";  shift 2 ;;
            --ent-repo)      ENT_REPO="$2";      shift 2 ;;
            --skip-skills)   SKIP_SKILLS=1;      shift   ;;
            --force)         FORCE=1;            shift   ;;
            -h|--help)       show_help ;;
            *) die "Unknown option: $1" ;;
        esac
    done
}

# ─── Main ─────────────────────────────────────────────────────────────────────
main() {
    parse_args "$@"

    # Validate workspace
    [ -d "$WORKSPACE_DIR" ] || die "Workspace not found: ${WORKSPACE_DIR}"

    # Auto-detect version
    [ -z "$VERSION" ] && VERSION="$(detect_version)"

    # Default project name
    if [ -z "$PROJECT_NAME" ]; then
        if [ -n "$LOCAL_PATH" ]; then
            PROJECT_NAME="$(basename "$LOCAL_PATH")"
        elif [ -n "$REPO_URL" ]; then
            PROJECT_NAME="$(basename "$REPO_URL" .git)"
        else
            die "Provide --project-name or at least one of --local-path / --repo-url"
        fi
    fi

    log_banner "Odoo ${VERSION} — Project Workspace Setup"
    log_info "Workspace : ${WORKSPACE_DIR}"
    log_info "Version   : ${VERSION}"
    log_info "Project   : ${PROJECT_NAME}"
    [ -n "$LOCAL_PATH" ]  && log_info "Source    : local path → ${LOCAL_PATH}"
    [ -n "$REPO_URL" ]    && log_info "Source    : git clone  → ${REPO_URL}"
    [ -n "$REPO_BRANCH" ] && log_info "Branch    : ${REPO_BRANCH}"
    [ -n "$ENT_REPO" ]    && log_info "Enterprise: ${ENT_REPO}"
    echo ""

    log_banner "Step 1/5 — Register project in .autoload_repos"
    setup_autoload_entry

    log_banner "Step 2/5 — Symlink modules into extra-${VERSION}"
    link_modules

    log_banner "Step 3/5 — Enterprise repository"
    if [ -n "$ENT_REPO" ]; then
        setup_enterprise
    else
        log_info "No --ent-repo provided — skipping enterprise setup"
    fi

    log_banner "Step 4/5 — Copy AI agent context (CLAUDE.md + skills)"
    copy_project_context

    log_banner "Step 5/5 — Verify addons_path"
    verify_addons_path

    echo ""
    log_banner "Done!"
    log_ok "Project ${PROJECT_NAME} is now wired into ${WORKSPACE_DIR}"
    echo ""
    echo "  Odoo module(s) available at:"
    echo "    ${WORKSPACE_DIR}/extra-${VERSION}/<module_name>"
    echo ""
    echo "  Restart Odoo and install/update the module(s) with:"
    echo "    cd ${WORKSPACE_DIR}"
    echo "    WORKSPACE_PATH=. ./manage_modules.sh install <module_name>"
    echo ""
    if [ -n "$ENT_REPO" ]; then
        echo "  Enterprise path added to addons_path in odoo.conf"
        echo "  Restart Odoo to pick up enterprise modules."
        echo ""
    fi
}

main "$@"
