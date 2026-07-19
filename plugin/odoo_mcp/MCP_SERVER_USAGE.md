# Odoo MCP Server - Usage Guide

This guide explains how to set up and use the Odoo MCP Server with Claude Code, VS Code, and other MCP-compatible editors.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Starting the MCP Server](#starting-the-mcp-server)
4. [Testing the Server](#testing-the-server)
5. [Configuration](#configuration)
6. [Connecting from Claude Code](#connecting-from-claude-code)
7. [Connecting from VS Code](#connecting-from-vs-code)
8. [Available Tools and Resources](#available-tools-and-resources)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

Before using the MCP Server, ensure you have:

- **Python 3.8+** installed
- **uv** package manager (for venv management)
- **Odoo 17, 18, or 19** instances running
- **Environment variables** configured in `.env` file
- Required Python packages (automatically installed by start script)

## Quick Start

1. **Check Odoo servers are running** (the start script will verify this):
   ```bash
   # Odoo servers should already be running based on .env configuration:
   # - Odoo 17: ODOO17_URL (default: http://localhost:8107)
   # - Odoo 18: ODOO18_URL (default: http://localhost:8090)
   # - Odoo 19: ODOO_URL (default: http://localhost:8090)
   ```

2. **Start the MCP Server**:
   ```bash
   cd <path-to-odoo-agent-pro-kit>/plugin/odoo_mcp
   chmod +x start_mcp_server.sh
   ./start_mcp_server.sh --start
   ```

3. **Verify it's running**:
   ```bash
   ./start_mcp_server.sh --status
   ```

4. **Test with curl commands**:
   ```bash
   # Run all tests
   chmod +x test_mcp_server.sh
   ./test_mcp_server.sh
   ```

5. **Or use the validation script**:
   ```bash
   python ../validate_mcp_phase11.py
   ```

## Starting the MCP Server

### Single Version Mode

```bash
# Start with default settings (Odoo 19)
./start_mcp_server.sh --start

# Start for a specific Odoo version
./start_mcp_server.sh --start --version 17.0
./start_mcp_server.sh --start --version 18.0
./start_mcp_server.sh --start --version 19.0

# Stop the server
./start_mcp_server.sh --stop

# Check status
./start_mcp_server.sh --status

# Restart
./start_mcp_server.sh --restart
```

### Multi-Version Mode (All 3 Odoo Versions at Once)

```bash
# Start MCP servers for all Odoo versions at once
./start_mcp_server.sh --all

# This starts 3 separate MCP servers:
# - Odoo 17.0: http://localhost:8765/sse
# - Odoo 18.0: http://localhost:8766/sse
# - Odoo 19.0: http://localhost:8767/sse

# Stop all MCP servers
./start_mcp_server.sh --stop-all

# Check status of all
./start_mcp_server.sh --status
```

### Server Details

- **Default Port**: 8765 (single version mode)
- **Multi-Version Ports**: 8765 (Odoo 17), 8766 (Odoo 18), 8767 (Odoo 19)
- **Transport**: SSE (Server-Sent Events) for HTTP
- **Protocol**: stdio for Claude Code, SSE for HTTP clients

## Testing the Server

### Using the Test Script (Recommended)

```bash
# Run all tests
chmod +x test_mcp_server.sh
./test_mcp_server.sh

# Test all MCP servers in multi-version mode
./test_mcp_server.sh --all-mcp

# Test specific version
./test_mcp_server.sh --odoo17
./test_mcp_server.sh --odoo18
./test_mcp_server.sh --odoo19

# Test specific MCP server port
./test_mcp_server.sh --mcp17    # Test port 8765
./test_mcp_server.sh --mcp18    # Test port 8766
./test_mcp_server.sh --mcp19    # Test port 8767
```

This will test:
- Odoo 17 connection via XML-RPC
- Odoo 18 connection via XML-RPC
- Odoo 19 connection via JSON-RPC 2.0
- MCP server(s) connectivity
- Model discovery
- Field extraction
- Relationship mapping

### Using the Validation Script

```bash
# Run full validation
python ../validate_mcp_phase11.py
```

Expected output:
```
Odoo 17.0 (xml-rpc): ✅ PASS
Odoo 18.0 (xml-rpc): ✅ PASS
Odoo 19.0 (json-rpc-2.0): ✅ PASS
RESULT: 3/3 versions connected successfully
```

### Manual Curl Commands

```bash
# Check server status
curl -s http://localhost:8765/ | head

# Test Odoo 17 connection
curl -s -X POST http://localhost:8765/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"execute","params":{"db":"odoo17","uid":1,"password":"admin","model":"res.partner","method":"search_read","args":[[],["name","email"]],"kwargs":{"limit":5}}}' | jq .

# Test Odoo 18 connection
curl -s -X POST http://localhost:8765/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"execute","params":{"db":"llmdb18","uid":1,"password":"admin","model":"res.partner","method":"search_read","args":[[],["name","email"]],"kwargs":{"limit":5}}}' | jq .

# Test Odoo 19 connection (JSON-RPC 2.0)
curl -s -X POST http://localhost:8765/messages/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"execute","params":{"service":"object","method":"execute_kw","args":["llmdb19",1,"admin","res.partner","search_read",[[],["name","email"]],{"limit":5}]}}' | jq .
```

## Configuration

### .env File Configuration

The MCP server automatically reads from the main `.env` file in the project root:

```env
# Odoo 17 Configuration
ODOO17_URL=http://localhost:8107
ODOO17_DB_NAME=odoo17
ODOO17_DB_USER=admin
ODOO17_DB_PASSWORD=admin

# Odoo 18 Configuration
ODOO18_URL=http://localhost:8090
ODOO18_DB_NAME=llmdb18
ODOO18_DB_USER=admin
ODOO18_DB_PASSWORD=admin

# Odoo 19 Configuration (default)
ODOO_URL=http://localhost:8090
ODOO_DB_NAME=llmdb19
ODOO_DB_USER=admin
ODOO_DB_PASSWORD=admin
```

### MCP Server Settings

Optional environment variables in `.env`:

```env
# MCP Server network settings
MCP_SERVER_HOST=localhost
MCP_SERVER_PORT=8765

# Cache settings (in seconds)
MCP_CONTEXT_CACHE_TTL=3600

# Connection pool size
MCP_CONNECTION_POOL_SIZE=10

# Request timeout (seconds)
MCP_REQUEST_TIMEOUT=30

# Retry attempts for failed requests
MCP_RETRY_ATTEMPTS=3

# Lazy loading: load models on demand
MCP_LAZY_LOADING=true

# Auto-refresh: refresh context when switching versions
MCP_AUTO_REFRESH=true
```

## Connecting from Claude Code

### Option 1: Using MCP Configuration File

1. Create or edit your MCP settings file:
   - **macOS**: `~/Library/Application Support/Claude/claude_code_settings.json`
   - **Linux**: `~/.config/Claude/claude_code_settings.json`

2. Add the Odoo MCP Server configuration:

```json
{
  "mcpServers": {
    "odoo-mcp": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp.odoo_mcp_server"
      ],
      "env": {
        "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin"
      }
    }
  }
}
```

3. Restart Claude Code. The MCP tools will be available automatically.

## Connecting from VS Code

### Option 1: Using VS Code MCP Extension (stdio mode)

This option runs the MCP server as a subprocess - best for local development.

1. **Install the MCP extension** for VS Code:
   - Search for "MCP" in VS Code Extensions
   - Install "MCP (Model Context Protocol)" by Microsoft or similar

2. **Configure MCP in VS Code settings** (`settings.json`):

```json
{
  "mcp.servers": {
    "odoo-mcp-17": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp.odoo_mcp_server",
        "--version", "17.0"
      ],
      "env": {
        "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin"
      }
    },
    "odoo-mcp-18": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp.odoo_mcp_server",
        "--version", "18.0"
      ],
      "env": {
        "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin"
      }
    },
    "odoo-mcp-19": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp.odoo_mcp_server",
        "--version", "19.0"
      ],
      "env": {
        "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin"
      }
    }
  }
}
```

### Option 1c: Full Configuration with Environment Variables

Pass explicit database credentials for each Odoo version:

```json
{
  "mcp.servers": {
    "odoo-mcp-17": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp.odoo_mcp_server",
        "--version", "17.0"
      ],
      "env": {
        "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin",
        "ODOO17_URL": "http://localhost:8107",
        "ODOO17_DB_NAME": "odoo17",
        "ODOO17_DB_USER": "admin",
        "ODOO17_DB_PASSWORD": "admin"
      }
    },
    "odoo-mcp-18": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp.odoo_mcp_server",
        "--version", "18.0"
      ],
      "env": {
        "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin",
        "ODOO18_URL": "http://localhost:8090",
        "ODOO18_DB_NAME": "llmdb18",
        "ODOO18_DB_USER": "admin",
        "ODOO18_DB_PASSWORD": "admin"
      }
    },
    "odoo-mcp-19": {
      "command": "python",
      "args": [
        "-m",
        "odoo_mcp.odoo_mcp_server",
        "--version", "19.0"
      ],
      "env": {
        "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin",
        "ODOO_URL": "http://localhost:8090",
        "ODOO_DB_NAME": "llmdb19",
        "ODOO_DB_USER": "admin",
        "ODOO_DB_PASSWORD": "admin"
      }
    }
  }
}
```

### Option 2: Using HTTP SSE Transport (Recommended for Remote)

This option connects to already-running MCP servers via HTTP - best when servers are started separately.

**First, start the MCP servers:**
```bash
cd <path-to-odoo-agent-pro-kit>/plugin/odoo_mcp
./start_mcp_server.sh --all
```

**Then configure VS Code to connect via HTTP:**

```json
{
  "mcp.servers": {
    "odoo-mcp-17": {
      "url": "http://localhost:8765/sse"
    },
    "odoo-mcp-18": {
      "url": "http://localhost:8766/sse"
    },
    "odoo-mcp-19": {
      "url": "http://localhost:8767/sse"
    }
  }
}
```

### Option 3: Using Claude Code with HTTP

For Claude Code or other MCP clients that support HTTP transport:

```json
{
  "mcpServers": {
    "odoo-mcp-17": {
      "url": "http://localhost:8765/sse"
    },
    "odoo-mcp-18": {
      "url": "http://localhost:8766/sse"
    },
    "odoo-mcp-19": {
      "url": "http://localhost:8767/sse"
    }
  }
}
```

### Option 4: Using Cursor Editor

Cursor supports MCP servers viastdio or HTTP:

```json
{
  "mcp": {
    "servers": {
      "odoo-mcp-19": {
        "command": "python",
        "args": [
          "-m",
          "odoo_mcp.odoo_mcp_server",
          "--version", "19.0",
          "--transport", "sse"
        ],
        "env": {
          "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin"
        }
      }
    }
  }
}
```

### Option 5: Using Zed Editor

```json
{
  "mcp": {
    "servers": {
      "odoo-mcp": {
        "command": "python",
        "args": [
          "-m",
          "odoo_mcp.odoo_mcp_server",
          "--version", "19.0"
        ],
        "env": {
          "PYTHONPATH": "<path-to-odoo-agent-pro-kit>/plugin"
        }
      }
    }
  }
}
```

### Server Port Reference

| Odoo Version | Port | SSE Endpoint | Protocol | Environment Variables |
|-------------|------|--------------|----------|----------------------|
| Odoo 17.0 | 8765 | http://localhost:8765/sse | XML-RPC | ODOO17_URL, ODOO17_DB_NAME, ODOO17_DB_USER, ODOO17_DB_PASSWORD |
| Odoo 18.0 | 8766 | http://localhost:8766/sse | XML-RPC | ODOO18_URL, ODOO18_DB_NAME, ODOO18_DB_USER, ODOO18_DB_PASSWORD |
| Odoo 19.0 | 8767 | http://localhost:8767/sse | JSON-RPC 2.0 | ODOO_URL, ODOO_DB_NAME, ODOO_DB_USER, ODOO_DB_PASSWORD |

### Command Line Arguments

The MCP server supports the following arguments:

| Argument | Description | Example |
|----------|-------------|---------|
| `--version` | Odoo version (17.0, 18.0, 19.0) | `--version 19.0` |
| `--port` | Server port | `--port 8767` |
| `--host` | Server host (default: localhost) | `--host 0.0.0.0` |
| `--transport` | Transport mode (stdio, sse) | `--transport sse` |

### Environment Variables for MCP Server

| Variable | Description | Default |
|----------|-------------|---------|
| `PYTHONPATH` | Python path for imports | Required |
| `ODOO_URL` | Odoo 19 URL | http://localhost:8069 |
| `ODOO_DB_NAME` | Odoo 19 database name | Required |
| `ODOO_DB_USER` | Odoo 19 username | admin |
| `ODOO_DB_PASSWORD` | Odoo 19 password | Required |
| `ODOO18_URL` | Odoo 18 URL | http://localhost:8069 |
| `ODOO18_DB_NAME` | Odoo 18 database name | Required |
| `ODOO17_URL` | Odoo 17 URL | http://localhost:8069 |
| `ODOO17_DB_NAME` | Odoo 17 database name | Required |

### Restarting Servers

After configuring, restart VS Code and start the MCP servers:

```bash
# Start all versions
cd <path-to-odoo-agent-pro-kit>/plugin/odoo_mcp
./start_mcp_server.sh --all

# Or start specific version
./start_mcp_server.sh --start --version 19.0

# Check status
./start_mcp_server.sh --status
```

### Using the Tools

Once connected, use the MCP tools in your editor's chat:

```
@odoo-mcp-19 search_models query:sale
@odoo-mcp-19 get_fields model:res.partner
@odoo-mcp-19 get_relationships model:sale.order
```

## Available Tools and Resources

### MCP Tools

| Tool | Description | Example |
|------|-------------|---------|
| `search_models` | Search models by query | `search_models(query="sale")` |
| `get_fields` | Get all fields for a model | `get_fields(model_name="res.partner")` |
| `get_relationships` | Get model relationships | `get_relationships(model_name="sale.order")` |
| `validate_field` | Validate a field exists | `validate_field(model="res.partner", field_name="email")` |
| `get_model_info` | Get model information | `get_model_info(model_name="product.product")` |
| `list_all_models` | List all available models | `list_all_models(limit=100)` |

### MCP Resources

| Resource | Description |
|----------|-------------|
| `models://list` | List all available Odoo models |
| `models://{model_name}` | Get details for a specific model |

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
lsof -i :8765

# Check logs
tail -f logs/mcp_server.log
```

### Connection Errors

1. **Verify Odoo is running**:
   ```bash
   nc -z localhost 8107  # Odoo 17
   nc -z localhost 8090  # Odoo 18/19
   ```

2. **Check credentials** in `.env` file

3. **Test direct connection**:
   ```python
   import xmlrpc.client
   url = "http://localhost:8107"
   db = "odoo17"
   username = "admin"
   password = "admin"
   common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
   uid = common.authenticate(db, username, password, {})
   print(f"UID: {uid}")
   ```

### MCP Client Issues

If Claude Code or VS Code can't see the MCP tools:

1. **Verify server is running**:
   ```bash
   ./start_mcp_server.sh --status
   ```

2. **Check MCP configuration**:
   - Ensure the path in config matches the server script path
   - Verify PYTHONPATH is set correctly

3. **Restart the editor** after configuration changes

### Debug Mode

Enable debug logging by setting the environment variable:

```bash
export COPILOT_LOG_LEVEL=debug
./start_mcp_server.sh --restart
```

## Additional Resources

- [MCP Documentation](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [Odoo RPC Documentation](https://www.odoo.com/documentation/17.0/developer/reference/external_api.html)
