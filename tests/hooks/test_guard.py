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


def test_raw_odoo_bin_path_qualified_blocked():
    vs = guard.classify_bash("python3 /opt/odoo/odoo-bin -d x -i sale --stop-after-init", vcs_allowed=True)
    assert "raw_odoo_bin" in _kinds(vs)


def test_odoo_bin_substring_not_flagged():
    vs = guard.classify_bash("echo myodoo-binary", vcs_allowed=True)
    assert vs == []


def test_destructive_cleanup_blocked():
    vs = guard.classify_bash("docker volume rm somevol", vcs_allowed=False)
    assert "destructive_cleanup" in _kinds(vs)


def test_destructive_cleanup_allowed_when_authorized():
    vs = guard.classify_bash("docker volume rm somevol", vcs_allowed=True)
    assert vs == []


# --- read-only git subcommands must NOT be blocked ---

def test_git_merge_base_not_blocked():
    assert guard.classify_bash("git merge-base main HEAD", vcs_allowed=False) == []


def test_git_merge_still_blocked():
    vs = guard.classify_bash("git merge feature", vcs_allowed=False)
    assert "vcs_write" in _kinds(vs)


def test_git_tag_list_not_blocked():
    assert guard.classify_bash("git tag -l", vcs_allowed=False) == []
    assert guard.classify_bash("git tag --list", vcs_allowed=False) == []
    assert guard.classify_bash("git tag -n1", vcs_allowed=False) == []


def test_git_tag_create_still_blocked():
    vs = guard.classify_bash("git tag v2.0", vcs_allowed=False)
    assert "vcs_write" in _kinds(vs)


def test_git_rebase_recovery_not_blocked():
    assert guard.classify_bash("git rebase --abort", vcs_allowed=False) == []
    assert guard.classify_bash("git rebase --continue", vcs_allowed=False) == []


def test_git_rebase_interactive_still_blocked():
    vs = guard.classify_bash("git rebase -i main", vcs_allowed=False)
    assert "vcs_write" in _kinds(vs)


# --- reading/searching the guarded scripts must NOT be blocked ---

def test_cat_odoo_bin_not_flagged():
    assert guard.classify_bash("cat odoo-bin", vcs_allowed=True) == []


def test_grep_odoo_bin_not_flagged():
    assert guard.classify_bash('grep -rn "odoo-bin" docs/', vcs_allowed=True) == []


def test_python_odoo_bin_flagged():
    vs = guard.classify_bash("python3 odoo-bin -i sale", vcs_allowed=True)
    assert "raw_odoo_bin" in _kinds(vs)


def test_path_qualified_odoo_bin_flagged():
    vs = guard.classify_bash("python3 /opt/odoo/odoo-bin -d x", vcs_allowed=True)
    assert "raw_odoo_bin" in _kinds(vs)


def test_dot_slash_odoo_bin_flagged():
    vs = guard.classify_bash("./odoo-bin shell", vcs_allowed=True)
    assert "raw_odoo_bin" in _kinds(vs)


def test_cat_manage_modules_not_flagged():
    assert guard.classify_bash("cat manage_modules.sh", vcs_allowed=True) == []


def test_dot_slash_manage_modules_flagged():
    vs = guard.classify_bash("./manage_modules.sh update x", vcs_allowed=True)
    assert "manage_modules_direct" in _kinds(vs)


def test_bash_dash_x_manage_modules_ok():
    assert guard.classify_bash("bash -x manage_modules.sh update x", vcs_allowed=True) == []


def test_raw_allowed_lifts_odoo_bin_and_manage():
    assert guard.classify_bash("python3 odoo-bin -i sale", vcs_allowed=True, raw_allowed=True) == []
    assert guard.classify_bash("./manage_modules.sh update x", vcs_allowed=True, raw_allowed=True) == []
