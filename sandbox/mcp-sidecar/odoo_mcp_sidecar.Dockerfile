FROM python:3.12-slim

WORKDIR /app

COPY odoo_mcp/requirements.txt /app/odoo_mcp/requirements.txt
# mcp>=2.0.0 removed the fastmcp submodule odoo_mcp_server.py depends on.
# Pin below 2.0.0 until the server is ported to the new mcp API.
RUN pip install --no-cache-dir "mcp[server]>=1.0.0,<2.0.0" \
    && pip install --no-cache-dir pydantic python-dotenv requests uvicorn starlette sse-starlette

COPY odoo_mcp /app/odoo_mcp

ARG ODOO_VERSION=19.0
ARG MCP_PORT=8767
ENV DEFAULT_ODOO_VERSION=${ODOO_VERSION}
ENV MCP_PORT=${MCP_PORT}

EXPOSE ${MCP_PORT}

ENTRYPOINT ["python3", "-m", "odoo_mcp.odoo_mcp_server", "--transport", "sse", "--host", "0.0.0.0"]
CMD ["--version", "19.0", "--port", "8767"]
