# Odoo Multi-Version Setup Guide for Linux

Complete guide for setting up **Odoo 17, 18, 19** with **AI Agent Integration** on Linux/Ubuntu.

## System Requirements

### Tested Environment
- **OS**: Ubuntu 22.04 LTS (jammy)
- **Kernel**: Linux 5.15+
- **Architecture**: x86_64

### Required Software
- **Python**: 3.12.12 (installed via deadsnakes PPA)
- **PostgreSQL**: 14+ (auto-installed)
- **Package Manager**: uv 0.10.0+ (for virtual environments)
- **Processor**: 2+ cores recommended
- **Disk Space**: 30GB+ (10GB per Odoo version + dependencies)
- **RAM**: 4GB+ (2GB per Odoo instance)

## Quick Start (5-10 minutes)

### Step 1: One-Command Setup

```bash
cd /root/AgentOdooPersona/odoo_local_setup
chmod +x setup_complete.sh
./setup_complete.sh --base-dir /root/AgentOdooPersona --versions 17,18,19
```

This single command:
1. ✅ Installs Python 3.12.12 from deadsnakes PPA
2. ✅ Installs PostgreSQL 14
3. ✅ Clones Odoo repositories (17, 18, 19)
4. ✅ Creates virtual environments with uv
5. ✅ Installs 22 AI agent skills per version
6. ✅ Deploys Copilot agents with configuration

**Expected Output:**
```
✅ Step 1/3: Bootstrap (Python 3.12, PostgreSQL, Odoo repos)
  └─ ✅ Python 3.12.12 installed
  └─ ✅ PostgreSQL 14 running
  └─ ✅ Odoo 17, 18, 19 cloned
  └─ ✅ Virtual environments created with uv

✅ Step 2/3: Agent Skills (GitHub Copilot + Gemini)
  └─ ✅ 22 skills deployed to each version
  └─ ✅ Configuration files generated

✅ Step 3/3: Deploy Agents
  └─ ✅ 7 agent files deployed per version
  └─ ✅ All validations passed
```

### Step 2: Verify Installation

```bash
# Check Python version
python3.12 --version     # Should show: Python 3.12.12

# Check uv installation
python3.12 -m pip show uv

# Check PostgreSQL
psql --version          # Should show: psql (PostgreSQL) 14.x

# Check Odoo directories
ls -la /root/AgentOdooPersona/17_workspace/
ls -la /root/AgentOdooPersona/18_workspace/
ls -la /root/AgentOdooPersona/19_workspace/
```

### Step 3: Start Odoo Services

```bash
# Start Odoo 17 (http://localhost:8107)
cd /root/AgentOdooPersona/17_workspace
source .venv/bin/activate
python odoo-bin -c config/odoo.conf.17

# In another terminal - Start Odoo 18 (http://localhost:8108)
cd /root/AgentOdooPersona/18_workspace
source .venv/bin/activate
python odoo-bin -c config/odoo.conf.18

# In another terminal - Start Odoo 19 (http://localhost:8109)
cd /root/AgentOdooPersona/19_workspace
source .venv/bin/activate
python odoo-bin -c config/odoo.conf.19
```

## Detailed Setup Steps

### Linux Dependency Installation

The `setup_complete.sh` script automatically handles this via `bootstrap_odoo_env.sh`:

```bash
# This happens automatically in setup_complete.sh:
# 1. Add deadsnakes PPA for Python 3.12
sudo add-apt-repository ppa:deadsnakes/ppa

# 2. Update package lists
sudo apt-get update

# 3. Install base dependencies
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev \
  postgresql postgresql-contrib build-essential libxml2-dev \
  libxslt1-dev zlib1g-dev libsasl2-dev libldap2-dev ssl-cert \
  libjpeg-dev git curl

# 4. Install pip via bootstrap (for Python 3.12)
curl -fsSL https://bootstrap.pypa.io/get-pip.py | python3.12

# 5. Install uv (fast package manager)
python3.12 -m pip install uv==0.10.0
```

### Python 3.12 From Deadsnakes PPA

The deadsnakes PPA provides the latest Python versions for Ubuntu:

```bash
# Add the PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update

# Install Python 3.12 with development tools
sudo apt-get install -y python3.12 python3.12-venv python3.12-dev python3.12-doc

# Verify installation
python3.12 --version     # Python 3.12.12
python3.12 -m pip --version

# Set as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100
```

**Why deadsnakes PPA?**
- Ubuntu 22.04 default repos only have Python up to 3.11
- Odoo 19 recommends Python 3.12
- deadsnakes maintains up-to-date Python 3.12 packages with security updates
- Works reliably across Ubuntu LTS versions

### PostgreSQL Setup

PostgreSQL 14 is installed and configured by `setup_complete.sh`:

```bash
# PostgreSQL automatically:
# 1. Installed via apt-get
# 2. Started as system service
# 3. Created databases: odoo17, odoo18, odoo19
# 4. Created odoo user (if custom DB user specified)

# Check PostgreSQL status
sudo systemctl status postgresql    # Should show: active (running)

# List databases
sudo -u postgres psql -l

# Connect to odoo19 database
sudo -u postgres psql -d odoo19 -c "SELECT 1"

# Change odoo user password (if needed)
sudo -u postgres psql -c "ALTER USER odoo WITH PASSWORD 'newpassword';"
```

**Default Configuration:**
- **Host**: localhost
- **Port**: 5432
- **User**: odoo
- **Password**: odoo (set by --db-password flag)
- **Databases**: odoo17, odoo18, odoo19

### Virtual Environment with uv

The `uv` package manager significantly speeds up virtual environment creation:

```bash
# Manual creation (if not using setup_complete.sh):
python3.12 -m uv venv /root/AgentOdooPersona/17_workspace/venv --python=3.12

# Activate
source /root/AgentOdooPersona/17_workspace/.venv/bin/activate

# Install requirements using uv (much faster than pip)
cd /root/AgentOdooPersona/17_workspace
uv pip install -r 17.0/requirements.txt

# Compare speeds:
# uv:   ~5-10 seconds
# pip:  ~30-60 seconds
```

**Why uv?**
- Written in Rust, 10-100x faster than pip
- Resolves dependencies quicker
- Uses same API as pip (`uv pip install`)
- Automatically installed in setup_complete.sh
- Recommended by Python packaging community

## Agent Skills & Copilot Integration

### What Gets Deployed

1. **Agent Skills** (22 per version):
   - `.github/AgentSkills/` - GitHub Copilot for VS Code
   - `.gemini/AgentSkills/` - Gemini CLI skills
   - Includes: browser automation, REST API, module validation, etc.

2. **Copilot Agents** (7 files per version):
   - `copilot_odoo_agent.py` - Main agent logic
   - `skill_loader.py` - Dynamic skill loading
   - `skill_tools.py` - Skill definitions
   - `model_selector.py` - LLM provider selection
   - `odoo_agent_prompts.py` - AI prompts
   - `cost_tracker.py` - API cost tracking
   - `github_copilot_sdk_main.py` - SDK integration

### Configuration Files Generated

For each version, these are automatically created:

```bash
# .env.agent - Agent configuration
WORKSPACE_DIR=/root/AgentOdooPersona/17_workspace
ODOO_VERSION=17
ODOO_PATH=/root/AgentOdooPersona/17_workspace/17.0
ODOO_BIN_PATH=/root/AgentOdooPersona/17_workspace/17.0/odoo-bin
PYTHON_BIN=/root/AgentOdooPersona/17_workspace/.venv/bin/python3

# agent_config.json - Feature flags
{
  "enable_browser_automation": true,
  "enable_cost_tracking": true,
  "enable_skill_loading": true,
  "max_retries": 3,
  "timeout_seconds": 300
}

# agent_dependencies.json - Version compatibility
{
  "odoo_version": 17,
  "python_version": "3.12",
  "required_skills": 22,
  "deployed_files": 7
}
```

### Using the Agents

#### With GitHub Copilot (VS Code)

1. Install Copilot extension in VS Code
2. Configure in workspace settings:
   ```json
   {
     "github.copilot.ai.modelSelector": "claude-3-5-sonnet",
     "odoo.agent.workspace": "/root/AgentOdooPersona/19_workspace"
   }
   ```
3. Ask Copilot to develop Odoo features:
   - "Create a new Odoo module for inventory management"
   - "Add a wizard dialog to the Sale Order view"
   - "Implement a custom report for RFQ analysis"

#### With Gemini CLI (Free)

```bash
cd /root/AgentOdooPersona/19_workspace

# Initialize agent
gemini init --config agent_config.json

# Ask questions
gemini ask "Create a new Odoo 19 module for accounting"
gemini ask "Debug the error in the sale module"

# Multi-step conversations
gemini chat                # Interactive mode
```

## Troubleshooting

### Python 3.12 Not Found

```bash
# If setup_complete.sh says Python 3.12 is missing:

# 1. Verify deadsnakes PPA is added
sudo grep -r "deadsnakes" /etc/apt/sources.list.d/

# 2. Add it if missing
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update

# 3. Install Python 3.12
sudo apt-get install python3.12 python3.12-venv python3.12-dev

# 4. Verify
python3.12 --version
```

### PostgreSQL Connection Refused

```bash
# 1. Check if PostgreSQL is running
sudo systemctl status postgresql

# 2. Start if not running
sudo systemctl start postgresql

# 3. Check if odoo user exists
sudo -u postgres psql -c "SELECT usename FROM pg_user WHERE usename='odoo';"

# 4. Create odoo user if missing
sudo -u postgres createuser -w odoo

# 5. Set password
sudo -u postgres psql -c "ALTER USER odoo WITH PASSWORD 'odoo';"

# 6. Grant privileges
sudo -u postgres psql -c "ALTER USER odoo CREATEDB;"
```

### uv Not Installing

```bash
# 1. Verify pip is available
python3.12 -m pip --version

# 2. Install uv manually
python3.12 -m pip install uv==0.10.0

# 3. Verify
python3.12 -m pip show uv
python3.12 -m uv --version
```

### Virtual Environment Creation Fails

```bash
# 1. Ensure Python 3.12-venv is installed
sudo apt-get install python3.12-venv

# 2. Remove old venv and recreate
rm -rf /root/AgentOdooPersona/19_workspace/venv
python3.12 -m uv venv /root/AgentOdooPersona/19_workspace/venv --python=3.12

# 3. Verify
source /root/AgentOdooPersona/19_workspace/.venv/bin/activate
python --version
```

### Odoo Startup Issues

```bash
# 1. Activate virtual environment
cd /root/AgentOdooPersona/19_workspace
source .venv/bin/activate

# 2. Check required dependencies
pip list | grep -E "werkzeug|jinja2|requests|lxml"

# 3. If missing, reinstall from requirements
pip install -r 19.0/requirements.txt

# 4. Check configuration file
cat config/odoo.conf.19

# 5. Test Odoo startup
python 19.0/odoo-bin --help

# 6. Start with debug output
python 19.0/odoo-bin -c config/odoo.conf.19 -d odoo19 --log-level=debug
```

## File Structure After Setup

```
/root/AgentOdooPersona/
├── 17_workspace/
│   ├── 17.0/                       # Odoo 17 source code
│   ├── extra-17/                   # Custom modules
│   ├── .venv/                       # Virtual environment
│   │   ├── bin/
│   │   │   ├── python3.12
│   │   │   ├── activate
│   │   │   └── ...
│   │   ├── lib/python3.12/site-packages/
│   │   └── ...
│   ├── config/
│   │   ├── odoo.conf.17            # Configuration
│   │   └── odoo.conf.18, odoo.conf.19
│   ├── logs/
│   │   ├── odoo.log
│   │   └── errors.log
│   ├── Agents/
│   │   ├── copilot_odoo_agent.py
│   │   ├── skill_loader.py
│   │   ├── skill_tools.py
│   │   ├── model_selector.py
│   │   ├── odoo_agent_prompts.py
│   │   ├── cost_tracker.py
│   │   ├── github_copilot_sdk_main.py
│   │   ├── agent_config.json
│   │   └── agent_dependencies.json
│   ├── .github/
│   │   └── AgentSkills/            # GitHub Copilot skills (22 files)
│   ├── .gemini/
│   │   └── AgentSkills/            # Gemini CLI skills (22 files)
│   ├── .env                        # Workspace configuration
│   ├── .env.agent                  # Agent configuration
│   └── manage_modules.sh
│
├── 18_workspace/                   # Similar structure for Odoo 18
│   └── ... (venv, config, agents)
│
└── 19_workspace/                   # Similar structure for Odoo 19
    └── ... (venv, config, agents)
```

## Next Steps

### 1. Access Odoo Web Interface

After starting services, open in browser:
- **Odoo 17**: http://localhost:8107
- **Odoo 18**: http://localhost:8108
- **Odoo 19**: http://localhost:8109

**Default Credentials:**
- **Username**: admin
- **Password**: admin

### 2. Install Additional Modules

```bash
cd /root/AgentOdooPersona/19_workspace
source .venv/bin/activate
python 19.0/odoo-bin -d odoo19 -i sale_management,account,mrp --without-demo
```

### 3. Test Agent Skills

```bash
cd /root/AgentOdooPersona/19_workspace
source .venv/bin/activate

# Test GitHub Copilot integration
python Agents/cli_agent.py --test --module sale

# Test Gemini integration (if configured)
python Agents/skill_loader.py --provider gemini --test
```

### 4. Enable AI Development Features

In VS Code, install and configure:
- **GitHub Copilot** extension
- **Odoo Extension** (optional)
- **Python extension** with Pylance

Then use natural language to:
- Generate Odoo modules
- Create custom views and fields
- Write validation rules
- Debug existing issues

## Performance Benchmarks

### Installation Time

Using `setup_complete.sh` on Ubuntu 22.04 with 4GB RAM and 50Mbps internet:

| Component | Time |
|-----------|------|
| System dependencies | 2-3 min |
| Python 3.12 installation | 1-2 min |
| PostgreSQL setup | 1-2 min |
| Odoo 17 clone + setup | 3-5 min |
| Odoo 18 clone + setup | 3-5 min |
| Odoo 19 clone + setup | 3-5 min |
| Agent skills deployment | 2-3 min |
| Total | **15-25 minutes** |

### Comparison: uv vs pip

Creating virtual environment + installing Odoo 19 requirements:

```
uv:   ~5-10 seconds
pip:  ~30-60 seconds
Time saved: ~80-85%
```

## For macOS Users

This guide is optimized for **Linux/Ubuntu**. For macOS:

1. Use Homebrew for Python:
   ```bash
   brew install python@3.12
   ```

2. Modify `setup_complete.sh`:
   - Remove `sudo add-apt-repository ppa:deadsnakes/ppa`
   - Use `brew install postgresql@14` instead of apt-get
   - Adjust paths as needed

3. Or use the legacy single-instance bootstrap:
   ```bash
   chmod +x bootstrap_odoo_env.sh
   ./bootstrap_odoo_env.sh --base-dir /Users/yourname/odoo
   ```

## Support & Documentation

- **Odoo Official**: https://docs.odoo.com
- **Odoo Development**: https://www.odoo.com/documentation/17.0/developer
- **GitHub Copilot**: https://github.com/features/copilot
- **uv Documentation**: https://docs.astral.sh/uv/
- **PostgreSQL**: https://www.postgresql.org/docs/14/

## License & Acknowledgments

This setup guide is part of the AgentOdooPersona project featuring:
- Odoo multi-version development environment
- GitHub Copilot integration for VS Code
- Gemini CLI agent support
- 22 pre-configured AI agent skills
- Automated setup and validation

Built for developers who want to leverage AI for faster Odoo development.
