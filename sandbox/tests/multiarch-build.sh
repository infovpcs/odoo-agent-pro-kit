#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
LOCK_FILE="$REPO_ROOT/sandbox/config/images.lock"
BUILDER="odoo-sandbox-matrix-$$"
OUTPUT_DIR="$(mktemp -d)"

cleanup() {
  docker buildx rm "$BUILDER" >/dev/null 2>&1 || true
  rm -rf "$OUTPUT_DIR"
}
trap cleanup EXIT

lock_value() {
  sed -n "s/^$1=//p" "$LOCK_FILE"
}

cd "$REPO_ROOT"
docker buildx create --driver docker-container --name "$BUILDER" --use >/dev/null
for version in 17 18 19; do
  key="ODOO_${version}_BASE"
  image="$(lock_value "$key")"
  manifest="$(docker buildx imagetools inspect "$image")"
  grep -q 'linux/amd64' <<<"$manifest"
  grep -q 'linux/arm64' <<<"$manifest"
  for platform in linux/amd64 linux/arm64; do
    output="$OUTPUT_DIR/odoo-${version}-${platform##*/}.oci.tar"
    docker buildx build --platform "$platform" --build-arg "ODOO_BASE_IMAGE=$image" \
      --file "sandbox/images/odoo-dev/${version}.Dockerfile" --output "type=oci,dest=$output" .
    test -s "$output"
  done
done

echo "OK: Odoo 17/18/19 dev images build for linux/amd64 and linux/arm64."
