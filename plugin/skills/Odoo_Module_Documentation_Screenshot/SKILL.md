---
name: odoo_module_documentation
description: Guidelines for documenting Odoo modules with screenshots, user guides, and technical documentation. Use when creating module documentation.
version: 1.0.0
author: VPCS Team
category: documentation
odoo_versions: ["17.0", "18.0", "19.0"]
tags: ["odoo", "documentation", "screenshots", "user-guide", "technical-docs"]
---
# Odoo Module Documentation & Screenshot Management Skill

## Overview
Comprehensive skill for automating screenshot capture, icon/banner generation, and index.html documentation updates for Odoo custom modules. Integrates browser automation, image generation, and HTML templating for professional module documentation.

## Core Components

### 1. Directory Structure
```
{module_name}/
├── static/
│   └── description/
│       ├── index.html          # Module documentation (auto-generated)
│       ├── icon.png            # 180x180 app icon (auto-generated)
│       ├── banner.png          # 1200x320 banner (auto-generated or screenshot)
│       ├── banner.gif          # Optional animated banner
│       ├── 01_feature_name.png # Feature screenshots (numbered)
│       ├── 02_feature_name.png
│       ├── ...
│       ├── company_logo.png    # Company watermark/logo
│       └── README.md           # Screenshot guide (optional)
```

### 2. File Requirements

#### Icon (icon.png)
- **Size**: 180x180 pixels
- **Format**: PNG with transparency
- **Content**: App logo/symbol representing module functionality
- **Generation Methods**:
  1. AI Image Generation (GitHub Copilot + DALL-E/Stable Diffusion)
  2. Screenshot crop from main UI
  3. Template-based icon with module name

#### Banner (banner.png)
- **Size**: 1200x320 pixels (Odoo standard)
- **Format**: PNG or GIF
- **Content**: Module branding with key features
- **Generation Methods**:
  1. AI Image Generation with text overlay
  2. Composite of multiple screenshots
  3. Design template with module info

#### Screenshots (01_*.png, 02_*.png, ...)
- **Naming**: Sequential numbering (01_, 02_, 03_...)
- **Format**: PNG
- **Content**: Live app testing images showing key features
- **Capture Strategy**:
  1. Main menu/dashboard
  2. List views with data
  3. Form views (create/edit)
  4. Settings/configuration
  5. Action results (reports, wizards)
  6. Special features (charts, kanban, calendar)

### 3. Screenshot Capture Workflow

> **This is the verified flow** (agent-browser 0.35.x, Odoo 17/18/19, headless
> Chrome via CDP). `@e1`, `@e2` … refs are assigned fresh by every
> `snapshot -i` and go stale after any navigation — re-snapshot each time.

#### Step 0: One-time setup + own session
```bash
npm i -g agent-browser && agent-browser install     # installs Chrome for CDP
export AGENT_BROWSER_SESSION="$(agent-browser session id --scope worktree --prefix docshots)"
AB(){ agent-browser --session "$AGENT_BROWSER_SESSION" "$@"; }
AB set viewport 1600 1000
```

#### Step 1: Resolve the Odoo URL + credentials
```bash
# --- Local Odoo (odoo_local_setup): port from the ROOT odoo.conf ---
ODOO_PORT=$(grep '^xmlrpc_port' odoo.conf | tail -1 | awk '{print $NF}')
BASE="http://localhost:${ODOO_PORT}"; DB=$(grep '^db_name' odoo.conf | awk '{print $NF}')
PW="admin"          # local dev default

# --- Docker Sandbox session (portless by design): bridge + real password ---
# S=<session>; the odoo container is <compose_project>-odoo-1 on <project>_default
docker run -d --rm --name "${S}-bridge" --network "${S}_default" \
  -p 127.0.0.1:8718:8718 alpine/socat \
  -d -d TCP-LISTEN:8718,fork,reuseaddr TCP:"${S}-odoo-1":8069
BASE="http://127.0.0.1:8718"
DB=$(grep '^db_name' ".sandbox/sessions/${S}/config/odoo.conf" | awk '{print $NF}')
PW=$(grep '^ODOO_API_PASSWORD=' ".sandbox/sessions/${S}/runtime.env" | cut -d= -f2)

curl -s -o /dev/null -w 'health %{http_code}\n' "$BASE/web/health"    # expect 200
```

#### Step 2: Log in
```bash
AB open "$BASE/web/login"
AB snapshot -i          # -> textbox "Email" [ref=e1], "Password" [ref=e2], button "Log in" [ref=e3]
AB fill @e1 "admin"
AB fill @e2 "$PW"
AB click @e3
sleep 4
AB get url              # success -> ".../odoo" ; failure -> still "/web/login"
```

#### Step 3: Navigate to the module (use the action xmlid, not `web#menu_id`)
```bash
AB open "$BASE/odoo/action-{module_name}.{action_xmlid}"   # e.g. action-my_mod.action_my_model
sleep 4
AB snapshot -i
AB errors               # must be empty — fail the run if the client logged JS errors
```

#### Step 4: Capture screenshots (sequential, numbered)
```bash
AB screenshot ./static/description/01_main_menu.png
# list view is the default; open a record for the form view
AB snapshot -i                      # find the row cell ref, e.g. @e14
AB click @e14 ; sleep 3
AB screenshot ./static/description/02_form_view.png
# create + fill
AB click @e3 ; sleep 2              # "New"
AB snapshot -i
AB fill @e13 "Demo Value"           # name field ref from the fresh snapshot
# Odoo binary/file widgets: the visible ref is a <label>; target the hidden input
AB upload "input[type=file]" ./demo.csv ; sleep 2
AB screenshot ./static/description/03_create_form.png
# run an action button and capture the result notification
AB click @e12 ; sleep 3            # e.g. "Sync Data Now" / "Confirm"
AB snapshot -i | grep -iE 'notification|success|error'
AB screenshot ./static/description/04_action_result.png
```

#### Step 5: Cross-check server-side (don't trust pixels alone)
```bash
# authenticate once, then confirm the action actually changed data
curl -s -c /tmp/ck -H 'Content-Type: application/json' \
  -d "{\"jsonrpc\":\"2.0\",\"method\":\"call\",\"params\":{\"db\":\"$DB\",\"login\":\"admin\",\"password\":\"$PW\"}}" \
  "$BASE/web/session/authenticate" >/dev/null
curl -s -b /tmp/ck -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"call","params":{"model":"my.model","method":"search_count","args":[[]],"kwargs":{}}}' \
  "$BASE/web/dataset/call_kw"
```

#### Step 6: Tear down
```bash
AB close --all
docker rm -f "${S}-bridge" 2>/dev/null   # sandbox mode only
rm -f /tmp/ck
```

**Gotchas learned the hard way**
- `wait --load networkidle` never settles on Odoo (long-poll bus) — use `sleep 3-4`.
- The Claude-in-Chrome extension stalls when proxied through the socat bridge;
  `agent-browser` (direct CDP) does not — always use `agent-browser` for sandbox sessions.
- `agent-browser screenshot <path>` takes the viewport; there is no `--full` in 0.35.x.
- Never hard-code `admin/admin` — a sandbox session's password is random and lives
  in `.sandbox/sessions/<s>/runtime.env` (`ODOO_API_PASSWORD`). `.sandbox/` is
  git-ignored; never copy that file or its values into tracked files, logs, or docs.

### 4. Icon & Banner Generation

#### Method 1: AI Image Generation (GitHub Copilot + Model)
```python
# Use GitHub Copilot SDK with image generation model
from copilot import CopilotClient

async def generate_icon(module_name: str, description: str) -> str:
    """Generate app icon using AI."""
    prompt = f"""
Create a professional app icon for an Odoo module:
- Module: {module_name}
- Description: {description}
- Style: Modern, flat design, Odoo purple (#875A7B) accent
- Size: 180x180 pixels
- Format: PNG with transparency
- Icon should be simple, recognizable, professional
"""
    
    client = CopilotClient()
    # Note: Use model that supports image generation (e.g., dall-e-3, stable-diffusion)
    response = await client.generate_image(prompt=prompt, size="180x180")
    return response.image_path

async def generate_banner(module_name: str, features: list) -> str:
    """Generate banner with module info."""
    prompt = f"""
Create a professional banner for an Odoo module:
- Module: {module_name}
- Key Features: {', '.join(features[:3])}
- Style: Modern, gradient background, Odoo branding
- Size: 1200x320 pixels
- Include: Module icon, name, tagline, feature icons
- Colors: Odoo purple (#875A7B), white text, professional gradient
"""
    
    client = CopilotClient()
    response = await client.generate_image(prompt=prompt, size="1200x320")
    return response.image_path
```

#### Method 2: Screenshot-Based Icon
```bash
# Capture the module's app-drawer tile, then crop
AB open "$BASE/odoo/apps"
AB snapshot -i | grep -i "{module_title}"        # find the tile ref
AB screenshot @e<ref> ./icon_temp.png            # element screenshot

# Resize to 180x180 using ImageMagick or PIL
convert ./icon_temp.png -resize 180x180 ./static/description/icon.png
```

#### Method 3: Template-Based Generation
```python
from PIL import Image, ImageDraw, ImageFont

def create_icon_from_template(module_name: str, color: str = "#875A7B") -> str:
    """Create simple icon with module initials."""
    img = Image.new('RGBA', (180, 180), (135, 90, 123, 255))  # Odoo purple
    draw = ImageDraw.Draw(img)
    
    # Get module initials (max 3 chars)
    initials = ''.join([word[0].upper() for word in module_name.split('_')[:3]])
    
    # Draw text
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = ((180 - text_width) / 2, (180 - text_height) / 2)
    
    draw.text(position, initials, fill="white", font=font)
    
    output_path = f"./static/description/icon.png"
    img.save(output_path)
    return output_path
```

### 5. index.html Template Generation

#### Template Structure
```html
<!-- Section 1: Trial/Demo Link -->
<section class="oe_container">
    <div class="oe_row oe_spaced">
        <h2 class="oe_slogan" style="color:#875A7B;">How to access a trial on VPCS cloud platform</h2>
        <h3 class="oe_slogan">Watch this video for a step-by-step guide on the trial process.<br/>You can try out the module on our cloud platform.</h3>
        <a class="text-center" style="font-size: 20px; margin-left: 50%;" target="_blank" href="{trial_video_url}">Trial Guide</a>
    </div>
</section>

<!-- Section 2: Module Overview -->
<section class="oe_container">
    <div class="oe_row oe_spaced">
        <h2 class="oe_slogan" style="color:#875A7B;">{module_title}</h2>
        <h3 class="oe_slogan">{module_description}</h3>
        <div style="margin-left: 20%; width: 60%; font-size: 18px">
            <h2>Key Features</h2>
            <ul style="font-size: 15px;">
                {features_list}
            </ul>
            <h2>Benefits</h2>
            <ul style="font-size: 15px;">
                {benefits_list}
            </ul>
        </div>
    </div>
</section>

<!-- Section 3-N: Screenshots with Descriptions -->
{for each screenshot in screenshots}
<section class="oe_container">
    <div class="oe_row oe_spaced">
        <h2 class="oe_slogan" style="color:#875A7B; margin-top: 100px;">{screenshot.title}</h2>
        <h3 class="oe_slogan">{screenshot.description}</h3>
        <div class="oe_demo oe_picture oe_screenshot mx-auto">
            <img src="{screenshot.filename}" style="max-width: 100%; height: auto;">
        </div>
    </div>
</section>
{end for}

<!-- Section Last: Company Info — replace with your own branding -->
<section class="oe_container oe_dark" style="padding: 30px;">
    <div class="oe_spaced">
        <a href="{{COMPANY_URL}}" target="_blank">
            <h2 class="oe_slogan" style="color:#875A7B;">
                <img src="company_logo.png" width="100%" height="auto">
            </h2>
        </a>
        <h3 class="oe_slogan">{{COMPANY_TAGLINE}}</h3>
    </div>
    <div class="text-center">
        <a href="{{COMPANY_URL}}/aboutus" target="_blank"><h2>About us</h2></a>
        <div>
            <a href="{{COMPANY_URL}}" target="_blank">Website</a> |
            <a href="{{COMPANY_URL}}/blog" target="_blank">Blog</a> |
            <a href="{{COMPANY_URL}}/contactus" target="_blank">Contact us</a> |
            <a href="mailto:{{COMPANY_EMAIL}}" target="_blank">Request New Feature</a>
        </div>
    </div>
</section>
```

#### Python Template Generator
```python
def generate_index_html(module_data: dict) -> str:
    """Generate index.html from module data and screenshots."""
    template = """
<section class="oe_container">
    <div class="oe_row oe_spaced">
        <h2 class="oe_slogan" style="color:#875A7B;">How to access a trial on VPCS cloud platform</h2>
        <h3 class="oe_slogan">Watch this video for a step-by-step guide on the trial process.<br/>You can try out the module on our cloud platform.</h3>
        <a class="text-center" style="font-size: 20px; margin-left: 50%;" target="_blank" href="{trial_url}">Trial Guide</a>
    </div>
</section>

<section class="oe_container">
    <div class="oe_row oe_spaced">
        <h2 class="oe_slogan" style="color:#875A7B;">{module_title}</h2>
        <h3 class="oe_slogan">{module_description}</h3>
        <div style="margin-left: 20%; width: 60%; font-size: 18px">
            <h2>Key Features</h2>
            <ul style="font-size: 15px;">
{features}
            </ul>
        </div>
    </div>
</section>
"""
    
    # Build features list
    features_html = "\n".join([f"                <li>{f}</li>" for f in module_data['features']])
    
    # Build screenshot sections
    screenshots_html = ""
    for i, screenshot in enumerate(module_data['screenshots'], 1):
        screenshots_html += f"""
<section class="oe_container">
    <div class="oe_row oe_spaced">
        <h2 class="oe_slogan" style="color:#875A7B; margin-top: 100px;">{screenshot['title']}</h2>
        <h3 class="oe_slogan">{screenshot['description']}</h3>
        <div class="oe_demo oe_picture oe_screenshot mx-auto">
            <img src="{screenshot['filename']}" style="max-width: 100%; height: auto;">
        </div>
    </div>
</section>
"""
    
    # Company footer
    # Company footer — customize via module_data, or replace entirely with your own branding
    company_name = module_data.get('company_name', 'Your Company')
    company_url = module_data.get('company_url', 'https://example.com')
    company_email = module_data.get('company_email', 'contact@example.com')
    company_tagline = module_data.get('company_tagline', 'Built with the Odoo Agent Pro Kit.')
    footer_html = f"""
<section class="oe_container oe_dark" style="padding: 30px;">
    <div class="oe_spaced">
        <a href="{company_url}" target="_blank">
            <h2 class="oe_slogan" style="color:#875A7B;">
                <img src="company_logo.png" width="100%" height="auto">
            </h2>
        </a>
        <h3 class="oe_slogan">{company_tagline}</h3>
    </div>
    <div class="text-center">
        <a href="{company_url}/aboutus" target="_blank"><h2>About us</h2></a>
        <div>
            <a href="{company_url}" target="_blank">Website</a> |
            <a href="{company_url}/blog" target="_blank">Blog</a> |
            <a href="{company_url}/contactus" target="_blank">Contact us</a> |
            <a href="mailto:{company_email}" target="_blank">Request New Feature</a>
        </div>
    </div>
</section>
"""
    
    # Combine all sections
    html = template.format(
        trial_url=module_data.get('trial_url', 'https://www.youtube.com/watch?v=demo'),
        module_title=module_data['title'],
        module_description=module_data['description'],
        features=features_html
    )
    
    html += screenshots_html + footer_html
    return html
```

### 6. Complete Automation Workflow

#### Task Completion Documentation Update
```python
async def update_module_documentation(
    module_name: str,
    module_path: str,
    base_url: str,          # resolved in Step 1 (local port OR sandbox bridge)
    odoo_password: str,     # resolved in Step 1 — never a literal
    action_xmlid: str,      # the module's main act_window xmlid
    progress_data: dict = None,
) -> dict:
    """
    Complete documentation update on task completion.
    
    Args:
        module_name: Technical name of the module
        module_path: Path to module directory
        base_url: Odoo base URL resolved in Step 1 (local port or sandbox bridge)
        odoo_password: admin password resolved in Step 1 (never a literal)
        action_xmlid: xmlid of the module's main act_window
        progress_data: Progress JSON with completed tasks
    
    Returns:
        dict: Summary of generated files
    """
    import os
    from pathlib import Path
    
    desc_path = Path(module_path) / "static" / "description"
    desc_path.mkdir(parents=True, exist_ok=True)
    
    # Extract module metadata from __manifest__.py
    manifest = read_manifest(module_path)
    module_title = manifest.get('summary', module_name.replace('_', ' ').title())
    module_description = manifest.get('description', '')
    
    # Step 1: Generate icon.png
    print("🎨 Generating icon.png...")
    icon_path = await generate_icon(module_name, module_description)
    # or use template-based: icon_path = create_icon_from_template(module_name)
    
    # Step 2: Capture screenshots with browser automation
    print("📸 Capturing screenshots...")
    screenshots = await capture_module_screenshots(
        module_name=module_name,
        base_url=base_url,
        odoo_password=odoo_password,
        action_xmlid=action_xmlid,
        output_dir=str(desc_path),
        progress_data=progress_data,
    )
    
    # Step 3: Generate banner.png (composite of screenshots or AI)
    print("🎨 Generating banner.png...")
    banner_path = await generate_banner(
        module_name=module_title,
        features=[t['title'] for t in progress_data.get('tasks', [])[:3]]
    )
    
    # Step 4: Generate index.html
    print("📝 Generating index.html...")
    module_data = {
        'title': module_title,
        'description': module_description,
        'features': [task['title'] for task in progress_data.get('tasks', [])],
        'screenshots': screenshots,
        'trial_url': 'https://www.youtube.com/watch?v=demo'  # Customize per module
    }
    
    html_content = generate_index_html(module_data)
    html_path = desc_path / "index.html"
    html_path.write_text(html_content)
    
    # Step 5: Copy company logo if not exists (drop your own logo at templates/company_logo.png)
    logo_src = Path(__file__).parent / "templates" / "company_logo.png"
    logo_dst = desc_path / "company_logo.png"
    if logo_src.exists() and not logo_dst.exists():
        import shutil
        shutil.copy(logo_src, logo_dst)
    
    return {
        "icon": str(desc_path / "icon.png"),
        "banner": str(desc_path / "banner.png"),
        "screenshots": [s['filename'] for s in screenshots],
        "index_html": str(html_path),
        "total_files": len(screenshots) + 3  # icon + banner + index
    }


async def capture_module_screenshots(
    module_name: str,
    base_url: str,
    odoo_password: str,
    action_xmlid: str,
    output_dir: str,
    progress_data: dict,
) -> list:
    """
    Capture screenshots for each completed task/feature.
    
    Returns:
        list: Screenshot metadata [{'filename': '01_*.png', 'title': '...', 'description': '...'}]
    """
    screenshots = []
    sess = os.environ["AGENT_BROWSER_SESSION"]  # set once by the caller
    ab = f'agent-browser --session {sess}'

    # Login — refs come from a fresh snapshot; the login form is always e1/e2/e3
    await run_bash(f'{ab} open "{base_url}/web/login"')
    await run_bash(f'{ab} snapshot -i')            # e1=Email, e2=Password, e3=Log in
    await run_bash(f'{ab} fill @e1 "admin"')
    await run_bash(f'{ab} fill @e2 "{odoo_password}"')   # never a literal — see Step 1
    await run_bash(f'{ab} click @e3')
    await run_bash('sleep 4')

    # Screenshot 1: module landing (action xmlid, NOT web#menu_id)
    await run_bash(f'{ab} open "{base_url}/odoo/action-{module_name}.{action_xmlid}"')
    await run_bash('sleep 4')
    await run_bash(f'{ab} errors')                 # abort the run if non-empty
    screenshot_num = 1
    filename = f"{screenshot_num:02d}_main_menu.png"
    await run_bash(f'{ab} screenshot {output_dir}/{filename}')
    screenshots.append({
        'filename': filename,
        'title': 'Main Menu & Dashboard',
        'description': f'Access all {module_name.replace("_", " ").title()} features from the main menu.'
    })
    
    # Screenshot 2-N: Each completed task
    for task in progress_data.get('tasks', []):
        if task.get('status') == 'done':
            screenshot_num += 1
            filename = f"{screenshot_num:02d}_{task['id']}.png"
            
            # Navigate to the module action, then drill in with refs from a
            # fresh snapshot (Odoo 17+ ignores web#model=/view_type= deep links).
            await run_bash(f'{ab} open "{base_url}/odoo/action-{module_name}.{action_xmlid}"')
            await run_bash('sleep 3')
            if 'form' in task['title'].lower() or 'create' in task['title'].lower():
                await run_bash(f'{ab} snapshot -i')      # then: {ab} click @e<row-or-New>
            await run_bash('sleep 2')

            await run_bash(f'{ab} screenshot {output_dir}/{filename}')
            screenshots.append({
                'filename': filename,
                'title': task['title'],
                'description': task.get('description', f"Implementation of {task['title']}")
            })

    await run_bash(f'{ab} close --all')
    return screenshots


def extract_model_name(task_title: str) -> str:
    """Extract model name from task title (e.g., 'Implement Car model' -> 'car')."""
    words = task_title.lower().split()
    if 'model' in words:
        idx = words.index('model')
        if idx > 0:
            return words[idx - 1]
    return 'unknown'


async def run_bash(command: str) -> dict:
    """Execute bash command (wrapper for agent-browser)."""
    import subprocess
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
```

### 7. Integration with Progress Tracking

#### Update progress JSON to trigger documentation
```json
{
  "module_name": "car_sales",
  "status": "done",
  "tasks": [
    {
      "id": "task_1",
      "title": "Implement Car Registration Model",
      "status": "done",
      "screenshot": "02_car_registration_list.png"
    },
    {
      "id": "task_2",
      "title": "Create Car Form View",
      "status": "done",
      "screenshot": "03_car_form_view.png"
    }
  ],
  "documentation": {
    "icon_generated": true,
    "banner_generated": true,
    "screenshots_captured": 6,
    "index_html_updated": true,
    "last_update": "2026-01-26T12:00:00"
  }
}
```

#### Trigger in Agent Loop
```python
# In agent's task completion handler
if all(task['status'] == 'done' for task in progress_data['tasks']):
    print("\n✅ All tasks complete. Generating documentation...")
    
    doc_result = await update_module_documentation(
        module_name=progress_data['module_name'],
        module_path=config['custom_addons'] + '/' + progress_data['module_name'],
        base_url=base_url,            # from Step 1
        odoo_password=odoo_password,  # from Step 1
        action_xmlid=progress_data['action_xmlid'],
        progress_data=progress_data,
    )
    
    # Update progress with documentation status
    progress_data['documentation'] = {
        'icon_generated': True,
        'banner_generated': True,
        'screenshots_captured': len(doc_result['screenshots']),
        'index_html_updated': True,
        'last_update': datetime.now().isoformat()
    }
    
    print(f"📸 Documentation complete: {doc_result['total_files']} files generated")
```

## Best Practices

### Screenshot Quality
1. **Set the viewport once** (`AB set viewport 1600 1000`) and keep every capture at it
2. **Re-snapshot after every navigation** — refs are stale otherwise
3. **`AB errors` must be empty** before you accept a screenshot as passing
4. **Clean Data**: use demo data that's readable and professional
5. **Cross-check with JSON-RPC** (Step 5) — a screenshot proves rendering, not that the action worked

### Icon/Banner Design
1. **Branding Consistency**: Use Odoo purple (#875A7B) as primary color
2. **Simple Symbols**: Icons should be recognizable at small sizes
3. **Professional**: Avoid clipart, use modern flat design
4. **Readable Text**: Banner text should be large enough to read in app store

### index.html Structure
1. **Trial Link First**: Always include trial/demo access prominently
2. **Features Before Screenshots**: Explain before showing
3. **Progressive Detail**: Start with overview, drill down to specifics
4. **Call to Action**: End with company info and contact links

### Automation Timing
1. **Task Completion**: Generate docs when all tasks marked 'done'
2. **Manual Trigger**: Provide option to regenerate docs anytime
3. **Incremental Updates**: Allow adding screenshots without regenerating all
4. **Version Control**: Commit generated files to git for tracking

## Error Handling

```python
try:
    doc_result = await update_module_documentation(...)
except Exception as e:
    # agent-browser not installed / login failed / bridge unreachable / JS errors
    print(f"⚠️  Screenshot capture failed: {e}")
    # Fallback 1: template icon (no browser needed)
    icon_path = create_icon_from_template(module_name)
    # Fallback 2: build index.html from PRD text only, no screenshot sections
    html = generate_index_html({**module_data, "screenshots": []})
```

Common concrete failures and fixes:

| Symptom | Cause | Fix |
|---------|-------|-----|
| `agent-browser: command not found` | not installed | `npm i -g agent-browser && agent-browser install` |
| stuck on `/web/login` after submit | wrong password | sandbox: read `ODOO_API_PASSWORD` from `runtime.env`, don't assume `admin` |
| blank page after `open .../action-...` | client still booting / JS error | `sleep` longer, then `AB errors`; if errors, the module has a real frontend bug |
| `health 000` / connection refused | sandbox has no published port | start the `alpine/socat` bridge (Step 1) |
| `Node is not a file input element` on `upload @eN` | Odoo binary widget ref is a `<label>` | `AB upload "input[type=file]" <path>` |

## Summary

This skill enables:
- ✅ Screenshot capture via `agent-browser` (headless Chrome/CDP) — the single
  browser path for local Odoo **and** Docker Sandbox sessions (via a socat bridge)
- ✅ Server-side JSON-RPC cross-checks so a passing screenshot also means the action worked
- ✅ AI / screenshot / template icon + banner generation
- ✅ Professional `index.html` generation with configurable branding
- ✅ Secret hygiene: session passwords are read from git-ignored `.sandbox/` at
  run time and never written into tracked files, logs, or the generated docs
- ✅ Version-specific capture (Odoo 17/18/19), progress-tracking integration

**Use this skill when**: module development or migration is complete and ready
for documentation, or when refreshing existing docs with new features.
