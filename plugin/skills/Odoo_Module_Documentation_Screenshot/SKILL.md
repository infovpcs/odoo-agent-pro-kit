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

#### Step 1: Initialize Browser Session
```bash
# Start browser with Odoo login
agent-browser open "http://localhost:8069"
agent-browser snapshot -i
agent-browser fill @login "admin"
agent-browser fill @password "admin"
agent-browser click @submit_button
```

#### Step 2: Navigate to Module
```bash
# Open Apps menu
agent-browser click @apps_menu
agent-browser fill @search_apps "{module_name}"
agent-browser click @module_card

# If already installed, navigate to module features
agent-browser click @main_menu
agent-browser click @{module_menu_item}
```

#### Step 3: Capture Screenshots (Sequential)
```bash
# Capture main menu/dashboard
agent-browser screenshot --full ./static/description/01_main_menu.png

# Navigate to list view
agent-browser click @{model_menu}
agent-browser screenshot --full ./static/description/02_{model}_list.png

# Open form view (create new)
agent-browser click @create_button
agent-browser screenshot --full ./static/description/03_create_{model}.png

# Fill form with demo data
agent-browser fill @{field1} "Demo Value"
agent-browser fill @{field2} "Test Data"
agent-browser screenshot --full ./static/description/04_{model}_form_filled.png

# Capture special views (if applicable)
agent-browser click @kanban_view
agent-browser screenshot --full ./static/description/05_{model}_kanban.png

# Settings page
agent-browser open "http://localhost:{http_port}/web#action={settings_action_id}"
agent-browser screenshot "docs/settings_view.png"
```

#### Step 4: Close Browser
```bash
agent-browser close
```

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
# Capture module icon from UI
agent-browser open "http://localhost:{http_port}/web#menu_id={module_menu_id}"
agent-browser get box @module_icon  # Get icon element position
agent-browser screenshot --clip {x},{y},{width},{height} ./icon_temp.png

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
    odoo_url: str = "http://localhost:{http_port}",
    progress_data: dict = None,
    module_menu_id: int = None,
    settings_action_id: int = None
) -> dict:
    """
    Complete documentation update on task completion.
    
    Args:
        module_name: Technical name of the module
        module_path: Path to module directory
        odoo_url: Odoo instance URL
        progress_data: Progress JSON with completed tasks
        module_menu_id: The menu ID for the module's main entry point in Odoo.
        settings_action_id: The action ID for the module's settings page in Odoo.
    
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
        odoo_url=odoo_url,
        output_dir=str(desc_path),
        progress_data=progress_data
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
    odoo_url: str,
    output_dir: str,
    progress_data: dict
) -> list:
    """
    Capture screenshots for each completed task/feature.
    
    Returns:
        list: Screenshot metadata [{'filename': '01_*.png', 'title': '...', 'description': '...'}]
    """
    screenshots = []
    
    # Initialize browser
    await run_bash(f'agent-browser open "{odoo_url}"')
    
    # Login
    await run_bash('agent-browser snapshot -i')
    await run_bash('agent-browser fill @login "admin"')
    await run_bash('agent-browser fill @password "admin"')
    await run_bash('agent-browser click @submit')
    
    # Screenshot 1: Main menu/dashboard
    await run_bash(f'agent-browser open "{odoo_url}/web#menu_id={module_name}"')
    screenshot_num = 1
    filename = f"{screenshot_num:02d}_main_menu.png"
    await run_bash(f'agent-browser screenshot --full {output_dir}/{filename}')
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
            
            # Navigate to relevant view (infer from task title)
            if 'list' in task['title'].lower() or 'view' in task['title'].lower():
                # Capture list view
                model_name = extract_model_name(task['title'])
                await run_bash(f'agent-browser open "{odoo_url}/web#model={model_name}&view_type=list"')
            elif 'form' in task['title'].lower() or 'create' in task['title'].lower():
                # Capture form view
                model_name = extract_model_name(task['title'])
                await run_bash(f'agent-browser open "{odoo_url}/web#model={model_name}&view_type=form"')
            elif 'settings' in task['title'].lower():
                # Capture settings
                await run_bash(f'agent-browser open "{odoo_url}/web#action=base.action_res_config_settings"')
            
            await run_bash(f'agent-browser screenshot --full {output_dir}/{filename}')
            screenshots.append({
                'filename': filename,
                'title': task['title'],
                'description': task.get('description', f"Implementation of {task['title']}")
            })
    
    # Close browser
    await run_bash('agent-browser close')
    
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
        odoo_url='http://localhost:8069',
        progress_data=progress_data
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
1. **Full Page Captures**: Use `--full` flag for complete context
2. **Hide Dev Tools**: Close browser dev tools before capturing
3. **Clean Data**: Use demo data that's readable and professional
4. **Consistent Resolution**: Capture all screenshots at same viewport size (1920x1080 recommended)

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
except BrowserNotStartedError:
    print("⚠️  Browser automation failed. Ensure agent-browser is installed.")
    # Fallback: Generate icon from template only
    icon_path = create_icon_from_template(module_name)
except ImageGenerationError as e:
    print(f"⚠️  AI image generation failed: {e}")
    # Fallback: Use screenshot-based icon
    icon_path = generate_icon_from_screenshot(module_name)
except Exception as e:
    print(f"❌ Documentation generation failed: {e}")
    # Log error and continue without documentation
    log_error(module_name, str(e))
```

## Summary

This skill enables:
- ✅ Automatic screenshot capture on task completion
- ✅ AI-powered icon and banner generation
- ✅ Professional index.html generation with company branding
- ✅ Integration with browser automation (agent-browser)
- ✅ Integration with GitHub Copilot image generation
- ✅ Fallback strategies for offline/failed generation
- ✅ Version-specific screenshot capture (Odoo 17/18/19)
- ✅ Progress tracking integration

**Use this skill when**: Module development is complete and ready for documentation, or when updating existing module documentation with new features.
