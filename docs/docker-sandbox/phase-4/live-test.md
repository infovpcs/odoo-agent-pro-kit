# Agent adapters LIVE TEST

Date: 2026-08-13 (Asia/Kolkata)

## Environment

- Host: designated Oracle Cloud Ubuntu 24.04 x86_64 KVM validation host.
- Docker Sandbox: `sbx` 0.38.0,
  `c022b14634c4bea846ca12870d1d5e97d5868b54`.
- Sandbox: `odoo-phase4-codex`, built-in Codex template, clone mode, 2 CPUs,
  8 GiB memory, local `odoo-mixin` 0.4.0 kit.
- Agent: Codex CLI 0.146.0 with stored host-side OpenAI OAuth.
- Odoo session: `19-sandbox-fixture-107d14`.

No credential value or credential file was copied into the repository,
artifact, microVM, or evidence.

## Passed evidence

1. `sandbox/bin/sandbox-agent preflight` validated the kit with the real 0.38.0
   parser and allowed `auth.docker.io`, `registry-1.docker.io`, and `github.com`
   through the balanced policy.
   `sbx kit pack` then produced a non-empty `odoo-mixin-0.4.0.zip`, and
   `sbx kit inspect --json` read the expected v2 manifest from the package.
2. The wrapper created the Codex sandbox with the built-in template and mixin.
   The CLI reported the read-only source mount, private clone, agent-neutral kit,
   and stored OpenAI OAuth use.
3. Codex CLI launched successfully and reported `/home/ubuntu/phase4-src` as
   its cloned workspace.
4. As an SSH-gate candidate edit, the fixture display name was changed to
   `Docker Sandbox Fixture Phase 4 SSH Candidate`. Because SSH authentication
   failed, this edit was made with `sbx exec`; it is partial evidence only and
   does not satisfy the SSH/IDE gate.
5. The Odoo 19 runtime created successfully. Its private fixture copy contained
   the candidate edit. `install` and `test` emitted succeeded operation results;
   the test completed in 13,250 ms.
6. `sandbox-agent logs ... odoo` retrieved 35,990 bytes into the host-side
   live-test log file.
7. `sandboxctl destroy` removed the Odoo/PostgreSQL containers, network, and all
   three session volumes. `sbx rm --force` removed the outer sandbox, and
   `sbx ls` reported no sandboxes.

## Blocking SSH evidence

The required attach command did not pass:

```text
ssh odoo-phase4-codex.sbx -- id
Connection closed by UNKNOWN port 65535
exit 255
```

`sbx setup ssh` generated the documented `*.sbx` proxy configuration and known
host. Verbose SSH reached the Docker Sandbox Go SSH server, negotiated
`curve25519-sha256`, matched the managed ED25519 host key, and then closed during
user authentication. The daemon logged successful HTTP 101 upgrades for the
`/sandbox/odoo-phase4-codex/ssh` endpoint. The failure repeated while the
sandbox was running, after Codex workspace trust was accepted, after rerunning
`sbx setup ssh`, and after a controlled `sbx daemon restart`. `sbx exec`, Codex,
the inner Docker runtime, OAuth, policy, and kit paths remained operational.

The user then explicitly ran `sbx logout` and completed a fresh `sbx login`
device flow. A subsequent diagnostic reported authentication passed and daemon,
socket, storage, and version checks healthy (the update check alone warned on
HTTP 403). A newly created, running Codex sandbox still closed the SSH session
at authentication with the same exit 255. Docker's configured Ubuntu stable
repository offered no newer package than `docker-sbx` 0.38.0. The retry sandbox
was removed and `sbx ls` again reported no sandboxes.

## Supplemental OpenCode agent validation

At the user's request, Docker's built-in OpenCode template was validated as a
second coding-agent adapter without installing an unmanaged host binary.
`odoo-phase4-opencode` used clone mode, 2 CPUs, 8 GiB, and the same Odoo mixin.
OpenCode 1.18.13 received `ODOO_AGENT_RUNTIME=sandbox`, edited the fixture name
to `Docker Sandbox Fixture OpenCode`, and created Odoo 19 session
`19-sandbox-fixture-f43943`. Create, install, and test succeeded; correlated
Odoo log retrieval returned 34,455 bytes. The inner containers, network, and
three volumes were destroyed, the outer sandbox was removed, and `sbx ls`
reported no sandboxes. This proves another agent uses the same runtime contract,
but it is supplemental evidence and does not replace the failed SSH/IDE gate.

## Result

On 2026-08-13 the user explicitly approved `sbx exec` as the IDE-equivalent
fallback for the pinned Ubuntu/`sbx` 0.38.0 SSH limitation. The fallback edited
the isolated fixture and completed module tests and correlated-log retrieval.
Codex and supplemental OpenCode runs used the same mixin and controller, and all
inner and outer resources were removed. Phase 4's LIVE TEST and exit gate pass;
SSH remains the preferred adapter and the authentication failure remains a
documented platform limitation to retest on the next pinned CLI patch.
