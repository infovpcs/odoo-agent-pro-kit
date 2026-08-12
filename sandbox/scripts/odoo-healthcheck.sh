#!/usr/bin/env bash
set -euo pipefail
exec python3 -c 'import urllib.request; urllib.request.urlopen("http://127.0.0.1:8069/web/health", timeout=2).read()'
