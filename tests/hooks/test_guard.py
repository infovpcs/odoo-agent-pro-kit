from __future__ import annotations
from plugin.hooks.checks import guard


def _kinds(vs):
    return sorted(v.kind for v in vs)


def test_raw_odoo_bin_blocked():
    vs = guard.classify_bash("python3 odoo-bin -d test -i sale --stop-after-init", vcs_allowed=True)
    assert "raw_odoo_bin" in _kinds(vs)


def test_sandboxctl_not_flagged():
    vs = guard.classify_bash("sandbox/bin/sandboxctl module s-1 install mymod", vcs_allowed=True)
    assert vs == []


def test_manage_modules_direct_blocked():
    vs = guard.classify_bash("./manage_modules.sh update mymod", vcs_allowed=True)
    assert "manage_modules_direct" in _kinds(vs)


def test_manage_modules_via_bash_ok():
    vs = guard.classify_bash("WORKSPACE_PATH=$(pwd) bash manage_modules.sh update mymod", vcs_allowed=True)
    assert vs == []


def test_git_push_blocked_when_not_allowed():
    vs = guard.classify_bash("git push origin main", vcs_allowed=False)
    assert "vcs_write" in _kinds(vs)


def test_git_push_allowed_when_authorized():
    vs = guard.classify_bash("git push origin main", vcs_allowed=True)
    assert vs == []


def test_git_commit_plain_ok():
    vs = guard.classify_bash("git commit -m 'x'", vcs_allowed=False)
    assert vs == []


def test_gh_release_blocked():
    vs = guard.classify_bash("gh release create v1.2.3", vcs_allowed=False)
    assert "vcs_write" in _kinds(vs)
