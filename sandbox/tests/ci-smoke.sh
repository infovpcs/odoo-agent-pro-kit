#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
version="${1:?usage: ci-smoke.sh 17|18|19}"
session="$("$ROOT/sandbox/bin/sandboxctl" create --version "$version" --module sandbox_fixture | tail -n 1)"
trap '"$ROOT/sandbox/bin/sandboxctl" destroy "$session" --allow-unexported >/dev/null 2>&1 || true' EXIT
"$ROOT/sandbox/bin/sandboxctl" module "$session" install sandbox_fixture
"$ROOT/sandbox/bin/sandboxctl" module "$session" test sandbox_fixture
"$ROOT/sandbox/bin/sandboxctl" destroy "$session" --allow-unexported
trap - EXIT
