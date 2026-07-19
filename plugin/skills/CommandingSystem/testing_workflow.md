# /testing Workflow

Complete step-by-step execution guide for the `/testing (17|18|19)` command.

---

## STEP 1: Parse & Pre-Flight Gate Check

```
User runs: /testing 19
→ version = 19
→ Ask for module name if not provided
```

**Check 1 — All tasks complete:**
```python
tasks_content = read_file(f"{module_name}/docs/tasks.md")
incomplete = [line for line in tasks_content.split("\n") if "- [ ]" in line]

if incomplete:
    print("⚠️ /testing prerequisites not ready — incomplete tasks found:")
    for task in incomplete:
        print(f"  {task}")
    print(f"\nAuto-bootstrapping: routing to /start-coding {version} to complete tasks first.")
    # If coding context is also missing, start-coding will auto-route to /plan-analysis.
    run(f"/start-coding {version} {module_name}")
    # Resume testing after coding loop completes
```

**Check 2 — Backend tests passed (from progress.json):**
```python
progress = json.load(open(f"sessions/{module_name}_progress.json"))
if not progress.get("backend_tests_passed"):
    print("⚠️ Backend tests not confirmed as passed.")
    print(f"Auto-bootstrapping: routing to /start-coding {version} for backend test completion.")
    run(f"/start-coding {version} {module_name}")
    # Resume testing after backend tests pass
```

**Gate success:**
```
✅ All prerequisites met:
  • All tasks: COMPLETE ✅
  • Backend tests: PASSED ✅
  • Starting frontend testing and documentation...
```

---

## STEP 2: Detect Odoo Port & Workspace

**Always detect port dynamically from root `odoo.conf` (not from `config/odoo.conf.{version}`):**

```bash
# Workspace root: resolve from env var first, then fall back to $HOME/odoo-workspaces
# macOS default: $HOME = /Users/<name>   Linux default: $HOME = /home/<name> or /root
ODOO_WORKSPACES_ROOT="${ODOO_WORKSPACES_ROOT:-$HOME/odoo-workspaces}"
WORKSPACE_PATH="${WORKSPACE_PATH:-$ODOO_WORKSPACES_ROOT/${version}_workspace}"

ODOO_PORT=$(grep "^xmlrpc_port" "$WORKSPACE_PATH/odoo.conf" | awk '{print $NF}')
DB_NAME=$(grep "^db_name" "$WORKSPACE_PATH/odoo.conf" | awk '{print $NF}')

echo "✅ Odoo ${version} → http://localhost:${ODOO_PORT} (db: ${DB_NAME})"

# Verify Odoo is actually running
curl -o /dev/null -s -w "%{http_code}" "http://localhost:${ODOO_PORT}/web/login" | grep -q "200" || {
    echo "⚠️ Odoo not running — starting..."

    # Start PostgreSQL — cross-platform
    if command -v systemctl &>/dev/null && systemctl list-units --type=service 2>/dev/null | grep -q postgresql; then
        # Linux (Ubuntu/Debian) — systemd-managed PostgreSQL
        sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null || true
    elif command -v pg_isready &>/dev/null; then
        # pg_ctl fallback (macOS Homebrew or compiled-from-source postgres)
        pg_isready -h localhost -p 5432 || {
            PGDATA="${PGDATA:-$(find /usr/local/var /var/lib/postgresql -maxdepth 2 -name "PG_VERSION" 2>/dev/null | head -1 | xargs dirname 2>/dev/null)}"
            [ -n "$PGDATA" ] && pg_ctl -D "$PGDATA" start || echo "⚠️ Cannot auto-start PostgreSQL — start it manually"
        }
    fi

    WORKSPACE_PATH="$WORKSPACE_PATH" bash "$WORKSPACE_PATH/manage_modules.sh" start \
        > /tmp/odoo${version}_server.log 2>&1 &
    sleep 18
}
```

---

## STEP 2.5: Dynamic JS Detection (Skip OWL tests for pure-backend modules)

```bash
# Check if module has any JS code in static/src/
JS_FILES=$(find "${WORKSPACE_PATH}/extra-${version}/${module_name}" -name "*.js" 2>/dev/null | wc -l)
WEB_DEPS=$(grep -E '"web"|"website"|"point_of_sale"' "${WORKSPACE_PATH}/extra-${version}/${module_name}/__manifest__.py" 2>/dev/null | wc -l)

if [ "$JS_FILES" -eq 0 ] && [ "$WEB_DEPS" -eq 0 ]; then
    echo "ℹ️  No JS/OWL code detected — skipping JavaScript-specific tests"
    SKIP_JS_TESTS=true
else
    echo "⚡ JS code detected ($JS_FILES files) — OWL component testing ENABLED"
    SKIP_JS_TESTS=false
fi
```

**Decision table:**

| Condition | JS Tests | OWL Error Check | console.log Scan |
|-----------|----------|-----------------|-----------------|
| No `*.js`, no web deps | SKIP | SKIP | SKIP |
| Has `static/src/*.js` | RUN | RUN | RUN |
| Depends on `web`/`website`/`point_of_sale` | RUN | RUN | RUN |

---

## STEP 3: Load Required Skills

```python
# Load browser skill (Level 2)
read_skill("Agent-browser-skill/SKILL.md")

# Load documentation screenshot skill (Level 2)
read_skill("AgentSkills/Odoo_Module_Documentation_Screenshot/SKILL.md")
```

**Level 3 — Load Agentic Memory (Phase 20.G):**
```python
# Restore test context or module structure facts from memory pool
memories = retrieve_memory_tool()
if memories.get("result"):
    prepend_to_system_prompt("Cross-Session Memory Context:\\n" + str(memories["result"]))
```

---

## STEP 4: System Dependency Check

Check and install required tools:

```bash
# Detect OS once — used throughout this block
OS_TYPE="$(uname -s)"  # Darwin = macOS, Linux = Linux

# Check Node.js
if ! command -v node &>/dev/null; then
    echo "📦 Installing Node.js 20.x..."
    if [ "$OS_TYPE" = "Darwin" ]; then
        brew install node
    elif command -v apt-get &>/dev/null; then
        # Ubuntu/Debian
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif command -v dnf &>/dev/null; then
        # RHEL/Fedora
        sudo dnf install -y nodejs
    else
        echo "⚠️ Cannot auto-install Node.js — install manually: https://nodejs.org"
    fi
fi

# Check agent-browser
if ! command -v agent-browser &>/dev/null; then
    echo "📦 Installing agent-browser globally..."
    sudo npm install -g agent-browser
    agent-browser --version
fi

# Check ffmpeg (for GIF conversion)
if ! command -v ffmpeg &>/dev/null; then
    echo "📦 Installing ffmpeg..."
    if [ "$OS_TYPE" = "Darwin" ]; then
        brew install ffmpeg
    elif command -v apt-get &>/dev/null; then
        sudo apt-get install -y ffmpeg
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y ffmpeg
    else
        echo "⚠️ Cannot auto-install ffmpeg — install manually"
    fi
fi

echo "✅ All system dependencies ready"
```

---

## STEP 5: Install / Update Module

```bash
# ALWAYS invoke via `bash` with WORKSPACE_PATH set explicitly.
# macOS default shell is zsh (which lacks bash 4+ features used in manage_modules.sh).
# On Linux, bash is the default BUT explicit `bash` invocation is safer and portable.
# Rule: always use `bash manage_modules.sh`, never `./manage_modules.sh`.
cd "$WORKSPACE_PATH"
WORKSPACE_PATH=$(pwd) bash manage_modules.sh update {module_name}

# manage_modules.sh STOPS Odoo during update — restart after:
sleep 5
curl -o /dev/null -s -w "%{http_code}" "http://localhost:${ODOO_PORT}/web/login" | grep -q "200" || {
    WORKSPACE_PATH=$(pwd) bash manage_modules.sh start > /tmp/odoo${version}_server.log 2>&1 &
    sleep 18
}
echo "✅ Module updated and Odoo running on port ${ODOO_PORT}"
```

---

## STEP 6: Frontend Test Execution Loop

### 6a. Login to Odoo backend

```bash
# Use /web/login — Odoo 19 backend login path
agent-browser open "http://localhost:${ODOO_PORT}/web/login"
sleep 2
agent-browser snapshot -i

# NOTE: Odoo 19 /web/login may show both a website header AND the login form.
# Find textboxes for Email and Password — they are usually NOT @e1/@e2.
# Always re-snapshot and look for:  textbox "Email" [ref=eN], textbox "Password" [ref=eM], button "Log in" [ref=eX]
# If you see "Administrator" button — the session exists, fill fresh credentials anyway.

agent-browser fill @e<email_ref> "admin"
agent-browser fill @e<password_ref> "admin"
agent-browser click @e<login_btn_ref>
sleep 4

# Verify login succeeded (URL should NOT still be /web/login)
agent-browser get url  # expect /odoo/... or /web#...

# Screenshot 00 — home after login
MODULE_DESC="${WORKSPACE_PATH}/extra-${version}/${module_name}/static/description"
mkdir -p "${MODULE_DESC}/screenshots" "${MODULE_DESC}/gifs"
agent-browser screenshot --full "${MODULE_DESC}/screenshots/00_odoo_home.png"
```

### 6b. Navigate to module via hamburger menu

```bash
# Open nav hamburger (usually first button [ref=e1])
agent-browser snapshot -i | head -5
agent-browser click @e<hamburger_ref>
sleep 2

# Find module menu entry
agent-browser snapshot -i | grep -i "{module_display_name}"
# e.g., "- menuitem \"Investment\" [ref=e26]"
agent-browser click @e<module_menu_ref>
sleep 3

# Screenshot 01 — module landing
agent-browser screenshot --full "${MODULE_DESC}/screenshots/01_{module_name}_home.png"
```

### 6c. Screenshot all key views

```bash
# List View
agent-browser screenshot --full "${MODULE_DESC}/screenshots/02_{model}_list.png"

# Open an existing record for Form View
agent-browser snapshot -i | grep -E "cell|row" | head -3
agent-browser click @e<first_row_ref>
sleep 3
agent-browser screenshot --full "${MODULE_DESC}/screenshots/03_{model}_form.png"

# Check for frontend errors after each navigation (always)
agent-browser errors 2>&1 | grep -v "^$" | head -5 || echo "✅ No errors"

# Create New Record
agent-browser find role button click --name "New"
sleep 2
agent-browser screenshot --full "${MODULE_DESC}/screenshots/04_create_{model}.png"
# Fill fields, save, screenshot result
agent-browser find role button click --name "Save manually"
sleep 2
agent-browser screenshot --full "${MODULE_DESC}/screenshots/05_{model}_saved.png"

# Back to list
agent-browser find text "{Model Name}" click
sleep 2
agent-browser screenshot --full "${MODULE_DESC}/screenshots/06_{model}_list_final.png"
```

### 6d. Handle frontend errors — auto-fix loop

```python
errors = run("agent-browser errors")
if errors.strip():
    print("❌ Frontend error detected:")
    print(errors)

    # Save error to progress.json for /start-coding to pick up
    progress["frontend_errors_to_fix"] = errors
    progress["frontend_test_failed_at"] = screenshot_name
    write_json(progress_file, progress)

    # Write error log
    write_file(
        f"{module_name}/docs/frontend_error_log.md",
        f"## Frontend Error — {datetime.now()}\n\n```\n{errors}\n```\n\nFailed at: {screenshot_name}"
    )

    print(f"\n🔧 Error logged to docs/frontend_error_log.md")
    print(f"   Triggering fix: /start-coding {version} {module_name}")
    print(f"   (progress.json carries the error context)")
    print(f"   After fixing, re-run: /testing {version} {module_name}")
    exit(1)
```

**Key: /start-coding checks `frontend_errors_to_fix` on load and auto-patches before continuing.**

### 6e. Record GIF of key workflow

```bash
# Start recording from the current logged-in state
agent-browser record start "${MODULE_DESC}/gifs/${module_name}_workflow.webm"

# Perform the key workflow (example: create → activate → close)
agent-browser find role button click --name "New"
sleep 2
# ... fill and save ...
agent-browser find role button click --name "Activate"
sleep 2

# Stop recording
agent-browser record stop

# Convert to GIF (ffmpeg required — auto-installed in STEP 4)
ffmpeg -i "${MODULE_DESC}/gifs/${module_name}_workflow.webm" \
    -vf "fps=8,scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
    -loop 0 \
    "${MODULE_DESC}/gifs/${module_name}_workflow.gif"
echo "✅ GIF created: ${module_name}_workflow.gif"
```

---

## STEP 7: Documentation Asset Generation

### 7a. Generate module icon (180×180 PNG)

**AI generation is preferred but use Pillow fallback when unavailable:**

```bash
# Detect a Python interpreter that has Pillow — cross-platform
# Checks: system python3, conda in common locations, workspace venv
find_python_with_pil() {
    for py in \
        python3 \
        "$HOME/miniconda3/bin/python3" \
        "$HOME/anaconda3/bin/python3" \
        "/opt/conda/bin/python3" \
        "/opt/miniconda3/bin/python3" \
        "$WORKSPACE_PATH/.venv/bin/python3"; do
        if command -v "$py" &>/dev/null && "$py" -c "from PIL import Image" 2>/dev/null; then
            echo "$py"; return 0
        fi
    done
    # Pillow not found — install into system python3
    python3 -m pip install --user Pillow --quiet 2>/dev/null && echo "python3" && return 0
    echo "python3"  # last resort
}
PYTHON_BIN=$(find_python_with_pil)
echo "✅ Using Python for icon generation: $PYTHON_BIN"
```

```python
# Icon generator — cross-platform, no macOS-specific paths
from PIL import Image, ImageDraw, ImageFont
import os, sys

ODOO_PURPLE = (113, 75, 103)   # #714B67
WHITE = (255, 255, 255)
MODULE_DESC = f"{os.environ.get('WORKSPACE_PATH', '.')}/extra-{version}/{module_name}/static/description"

def get_font(size):
    # Font search order: macOS → Ubuntu/Debian → RHEL → generic DejaVu → default
    candidates = [
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        # Ubuntu/Debian
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
        # RHEL/CentOS
        "/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
        # Alpine / minimal Linux
        "/usr/share/fonts/ttf-dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try: return ImageFont.truetype(path, size)
            except: pass
    return ImageFont.load_default()  # built-in fallback — always works

# 180×180 icon — circular background + initials
img = Image.new("RGBA", (180, 180), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.ellipse([0, 0, 180, 180], fill=ODOO_PURPLE)
initials = ''.join(w[0].upper() for w in module_name.split('_')[:3])
font = get_font(60)
bbox = d.textbbox((0, 0), initials, font=font)
tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
d.text(((180-tw)/2, (180-th)/2), initials, fill=WHITE, font=font)
img.save(f"{MODULE_DESC}/icon.png")
print("✅ icon.png (180×180)")
```

### 7b. Generate app banner (1200×320 PNG)

```python
# 1200×320 branded banner with gradient + module name
banner = Image.new("RGB", (1200, 320), ODOO_PURPLE)
b = ImageDraw.Draw(banner)
# Gradient: dark top → purple bottom
for y in range(320):
    r = int(80 + (113-80)*(y/320)); g = int(50+(75-50)*(y/320)); bl = int(75+(103-75)*(y/320))
    b.line([(0,y),(1200,y)], fill=(r,g,bl))
# Title + tagline
b.text((60, 80),  module_display_name, fill=WHITE, font=get_font(64))
b.text((60, 165), module_short_description[:60], fill=(220,200,230), font=get_font(32))
b.rectangle([60, 230, 500, 235], fill=(212,175,55))  # gold accent line
b.rounded_rectangle([60, 250, 210, 285], radius=8, fill=(212,175,55))
b.text((75, 255), f"Odoo {version}.0", fill=(80,50,75), font=get_font(24))
banner.save(f"{MODULE_DESC}/banner.png")
print("✅ banner.png (1200×320)")
```

### 7c. Copy company logo

```bash
# Search for company_logo.png anywhere under ODOO_WORKSPACES_ROOT (resolves on both macOS and Linux)
# Customize this with your own company/brand logo — see Odoo_Module_Documentation_Screenshot skill.
ODOO_WORKSPACES_ROOT="${ODOO_WORKSPACES_ROOT:-$HOME/odoo-workspaces}"
COMPANY_LOGO=$(find "$ODOO_WORKSPACES_ROOT" -name "company_logo.png" 2>/dev/null | head -1)
if [ -n "$COMPANY_LOGO" ]; then
    cp "$COMPANY_LOGO" "${MODULE_DESC}/company_logo.png"
    echo "✅ company_logo.png copied from: $COMPANY_LOGO"
else
    echo "⚠️  company_logo.png not found — add your own brand logo to static/description/"
fi
```

### 7d. Verify all assets exist

```bash
echo "=== Static/description contents ==="
ls -lh "${MODULE_DESC}/"
ls -lh "${MODULE_DESC}/screenshots/" 2>/dev/null
ls -lh "${MODULE_DESC}/gifs/" 2>/dev/null

# Required files checklist
for f in icon.png banner.png index.html company_logo.png; do
    [ -f "${MODULE_DESC}/$f" ] && echo "✅ $f" || echo "❌ MISSING: $f"
done
```

---

## STEP 8: Generate Responsive index.html

Build a professional, responsive documentation page:

```html
<!-- {module_name}/static/description/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{Module Display Name} — Odoo {version}.0</title>
    <style>
        /* Modern, responsive styles mirroring apps.odoo.com */
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 960px; margin: 0 auto; padding: 20px;
            color: #333; line-height: 1.6;
        }
        .hero { text-align: center; padding: 40px 0; }
        .hero img.banner { width: 100%; border-radius: 8px; margin-bottom: 20px; }
        .hero img.icon { width: 80px; height: 80px; margin-bottom: 16px; }
        h1 { font-size: 2em; color: #714B67; }
        .features { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; margin: 40px 0; }
        .feature-card { padding: 24px; border: 1px solid #eee; border-radius: 8px; }
        .feature-card h3 { color: #714B67; margin-top: 0; }
        .screenshots { margin: 40px 0; }
        .screenshots img { width: 100%; border-radius: 8px; margin-bottom: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .gif-section { margin: 40px 0; }
        .gif-section img { max-width: 100%; border-radius: 8px; border: 1px solid #eee; }
        .install { background: #f8f4ff; padding: 24px; border-radius: 8px; margin: 40px 0; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; margin: 4px; }
        .badge-version { background: #714B67; color: white; }
        .badge-license { background: #28a745; color: white; }
        @media (max-width: 600px) { .features { grid-template-columns: 1fr; } }
    </style>
</head>
<body>

<div class="hero">
    <img class="icon" src="icon.png" alt="{Module Name} Icon">
    <img class="banner" src="banner.png" alt="{Module Name} Banner">
    <h1>{Module Display Name}</h1>
    <p class="lead">{module_short_description}</p>
    <span class="badge badge-version">Odoo {version}.0</span>
    <span class="badge badge-license">{license}</span>
</div>

<!-- Architecture Diagram (if generated during /plan-analysis) -->
{architecture_section}

<!-- Feature sections from requirements.md headings -->
<section class="features">
{feature_cards}
</section>

<!-- Workflow GIFs -->
<section class="gif-section">
    <h2>🎬 See It In Action</h2>
{gif_embeds}
</section>

<!-- Screenshots -->
<section class="screenshots">
    <h2>📸 Screenshots</h2>
{screenshot_embeds}
</section>

<!-- Installation -->
<section class="install">
    <h2>⚙️ Installation</h2>
    <ol>
        <li>Download and place the module in your custom addons path</li>
        <li>Update apps list: Settings → Apps → Update Apps List</li>
        <li>Search for <strong>{display_name}</strong> and click Install</li>
    </ol>
    <p><strong>Dependencies:</strong> {depends_list}</p>
</section>

</body>
</html>
```

**Generator logic:**
```python
# Build architecture diagram section (if diagram was generated during /plan-analysis)
arch_png = f"{module_name}/docs/architecture.png"
if os.path.exists(arch_png):
    shutil.copy2(arch_png, f"{module_name}/static/description/architecture.png")
    architecture_html = """<section class="architecture">
    <h2>🏛️ Module Architecture</h2>
    <img src="architecture.png" alt="Architecture Diagram" style="max-width:100%; border-radius:8px; border:1px solid #eee;">
</section>"""
else:
    architecture_html = ""  # no diagram generated, skip section

# Build feature cards from requirements.md sections
requirements = read_file(f"{module_name}/docs/requirements.md")
feature_sections = parse_h2_sections(requirements)

feature_cards_html = ""
for section in feature_sections:
    feature_cards_html += f"""
    <div class="feature-card">
        <h3>{section.title}</h3>
        <p>{section.summary}</p>
    </div>"""

# Build GIF embeds
gif_embeds_html = ""
for gif in list_files(f"{module_name}/static/description/gifs/"):
    gif_embeds_html += f'<img src="gifs/{gif}" alt="{gif}" loading="lazy">\n'

# Build screenshot embeds  
screenshot_embeds_html = ""
for shot in list_files(f"{module_name}/static/description/screenshots/"):
    screenshot_embeds_html += f'<img src="screenshots/{shot}" alt="{shot}" loading="lazy">\n'
    
# Write final index.html
write_file(
    f"{module_name}/static/description/index.html",
    index_template
        .replace("{architecture_section}", architecture_html)
        .replace("{feature_cards}", feature_cards_html)
        .replace("{gif_embeds}", gif_embeds_html)
        .replace("{screenshot_embeds}", screenshot_embeds_html)
)
```

---

## STEP 9: Final Verification & Summary

```
🎉 Testing & Documentation Complete!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Frontend UI tests:       PASSED ✅ (0 JS errors)
Screenshots captured:    {N} screenshots
GIF animations created:  {N} GIFs
Documentation generated:

{module_name}/static/description/
  ├── icon.png              ← AI-generated module icon
  ├── banner.png            ← AI-generated app banner
  ├── index.html            ← Responsive documentation page
  ├── screenshots/          ← {N} UI screenshots
  └── gifs/                 ← {N} workflow animations

📋 Module ready for distribution!
   • View docs: open {module_name}/static/description/index.html
   • Install the module and see it in the Odoo app store format
```

---

## Error Recovery Map

| Error Type | Auto-fix | Manual fallback |
|------------|----------|----------------|
| JS TypeError | Inject into progress.json, trigger /start-coding fix | Paste error to user |
| Frontend error (agent-browser errors) | Write to docs/frontend_error_log.md + progress.json, trigger /start-coding | Paste error to user |
| Module install error | Check dependencies, auto-fix __manifest__.py | Ask user to check addons path |
| agent-browser not found | `sudo npm install -g agent-browser` | Show manual install steps |
| ffmpeg not found | macOS: `brew install ffmpeg` · Linux: `sudo apt-get install -y ffmpeg` | Manual install |
| Screenshot blank | sleep 5, retry snapshot | Ask user to check Odoo is running |
| Odoo not running | Linux: `sudo systemctl start postgresql && bash manage_modules.sh start` · macOS: `pg_ctl -D $PGDATA start && bash manage_modules.sh start` | Ask user to start manually |
| manage_modules.sh fails | Invoke via `bash` with `WORKSPACE_PATH=$(pwd)` prefix — never `./manage_modules.sh` | Check script permissions |
| PIL import error | Run `find_python_with_pil` helper to locate conda/venv python with Pillow, or `pip3 install --user Pillow` | `python3 -m pip install Pillow` |
| Port not found in config | Read root `odoo.conf` (not `config/odoo.conf.{V}`) | Ask user for port |
| Login loop after filling form | Session already exists — snapshot first, look for "Log in" button ref | Re-open /web/login |

---

## Phase 25 Lessons Learned — Embedded in This Workflow

The following hard-won patterns from the vpcs_investment_lifecycle development are now standard:

```
1.  Port detection: ALWAYS read from root odoo.conf, not config/odoo.conf.{V}
2.  manage_modules.sh: ALWAYS invoke via `bash` explicitly — macOS default shell is zsh (lacks bash 4+
    features); on Linux bash is default but explicit `bash` invocation is still safer and portable
3.  Workspace path: use ODOO_WORKSPACES_ROOT env var or fall back to $HOME/odoo-workspaces
    → macOS: /Users/<name>/odoo-workspaces   Linux: /home/<name>/odoo-workspaces or /opt/odoo-workspaces
4.  Update restarts server: after manage_modules.sh update, wait + check health before testing
5.  Dynamic JS detection: check for *.js in static/src/ before running OWL tests
6.  Login form refs: NEVER hardcode @e1/@e2 — always snapshot first and grep for "textbox"
7.  PIL for icons: system python3 may lack PIL — use find_python_with_pil() helper to check
    multiple conda/venv paths before falling back to pip install
8.  Font paths: always probe macOS + Ubuntu + RHEL paths in order; fall back to ImageFont.load_default()
9.  PostgreSQL start (Linux): use `systemctl start postgresql`; NOT pg_ctl -D /usr/local/var/postgres
    (that Homebrew path does not exist on Linux)
10. company_logo.png: search $ODOO_WORKSPACES_ROOT with find, not a hardcoded absolute path
11. Action return values (Odoo 19): action methods must return True (not None) for xmlrpc
12. execute_kw args: args=[] and kw={} must be SEPARATE positional params in Odoo 19
13. Session handoff: write ODOO_PORT, WORKSPACE_PATH, python_bin to progress.json
```
