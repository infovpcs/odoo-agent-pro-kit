# Sandbox-Native Frontend Verification (agent-browser)

Run browser automation **inside** the Docker Sandbox, next to the sandboxed
Odoo instance. This is the default frontend-verification path — it needs no
SSH tunnels, no `sbx ports` publishing, and no host-side relays.

## Why inside the sandbox

- The sandbox network policy blocks inbound connections from the host to the
  inner Compose network; tunnels/relays are fragile (outer sandbox auto-stops
  when no `sbx exec` is attached) and were the main source of lost time in
  earlier migration batches.
- `agent-browser` runs headless Chrome next to Odoo; the site is reachable at
  the container's internal IP directly.
- Console/error auditing, screenshots, and `.webm` recording come from one CLI.

## One-time setup per sandbox

```bash
sbx exec <sandbox> -- \
  bash /home/ubuntu/workspace/<repo>/sandbox/scripts/sandbox-browser-setup.sh
```

The script installs:

1. `agent-browser` npm CLI (Vercel package)
2. Its managed Chromium build + system libraries (`install --with-deps`)
3. `ffmpeg` (needed by `agent-browser record start|stop`)

## Keeping the outer sandbox alive

The outer sandbox stops its containers when no exec session is attached. Hold
it open while working from the agent machine:

```bash
# background task on the validation host
ssh <host> 'sbx exec <sandbox> -- bash -lc "while true; do sleep 30; done"'
```

## Driving Odoo

Resolve the inner Odoo container IP, then browse to it:

```bash
IP=$(docker inspect <compose-project>-odoo-1 \
  --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')

agent-browser open "http://$IP:8069/shop" --timeout 90000
agent-browser get title
```

Note: Chrome inherits the shell's proxy env vars; if navigation times out,
use the sandbox-loopback socat relay instead (`socat
TCP-LISTEN:18069,bind=127.0.0.1,reuseaddr,fork TCP:$IP:8069 &`, then open
`http://127.0.0.1:18069/...`), which bypasses proxy resolution.

## Standard evidence flow

```bash
OUT=.sandbox/sessions/<session>/tests/browser/screenshots

agent-browser screenshot "$OUT/01_shop.png"
agent-browser screenshot --full "$OUT/02_product_page.png"
agent-browser get count "#book_btn"        # widget presence checks
agent-browser record start "$VID/flow.webm"
# ... fill/click steps ...
agent-browser screenshot "$OUT/04_after_submit.png"
agent-browser record stop
agent-browser errors                        # console error audit (must be empty)
agent-browser network requests              # failed-request audit
```

Gate rule (matches Phase 6+ artifact contract): a frontend pass requires at
least one full-flow screenshot set, a recorded `.webm`, and an empty
`agent-browser errors` output. Anything less is recorded as `not_run`.
