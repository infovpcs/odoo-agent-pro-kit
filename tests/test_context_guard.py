import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugin"))

import context_guard  # noqa: E402


class TestEffectiveThresholdPct(unittest.TestCase):
    def test_small_module_gets_higher_threshold(self):
        # <=5 tasks: base + 0.05
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.60, 3), 0.65)
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.60, 0), 0.65)

    def test_medium_module_keeps_base_threshold(self):
        # 6-15 tasks: unchanged
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.60, 10), 0.60)
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.60, 6), 0.60)
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.60, 15), 0.60)

    def test_large_module_gets_lower_threshold(self):
        # >15 tasks: base - 0.10 (hand off earlier)
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.60, 20), 0.50)
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.60, 45), 0.50)

    def test_bounds_are_respected(self):
        # Extreme low base clamped to 0.40 floor
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.30, 30), 0.40)
        # Extreme high base clamped to 0.80 ceiling
        self.assertAlmostEqual(context_guard._effective_threshold_pct(0.90, 2), 0.80)


class TestCountTasks(unittest.TestCase):
    def test_counts_done_and_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks_md = Path(tmp) / "tasks.md"
            tasks_md.write_text(
                "# Tasks\n\n"
                "- [x] Task 1: done\n"
                "- [x] Task 2: also done\n"
                "- [ ] Task 3: not done\n"
                "- [ ] Task 4: not done\n"
            )
            done, total = context_guard._count_tasks(tasks_md)
            self.assertEqual(done, 2)
            self.assertEqual(total, 4)

    def test_empty_file_returns_zero_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            tasks_md = Path(tmp) / "tasks.md"
            tasks_md.write_text("# No tasks here\n")
            self.assertEqual(context_guard._count_tasks(tasks_md), (0, 0))


class TestUsagePct(unittest.TestCase):
    def test_computes_fraction_of_context_window(self):
        usage = {"total_tokens": 64000}
        self.assertAlmostEqual(context_guard._usage_pct(usage, 128000), 0.5)

    def test_returns_none_without_usage(self):
        self.assertIsNone(context_guard._usage_pct(None, 128000))
        self.assertIsNone(context_guard._usage_pct({}, 128000))

    def test_returns_none_without_context_window(self):
        self.assertIsNone(context_guard._usage_pct({"total_tokens": 1000}, 0))

    def test_returns_none_for_non_positive_total(self):
        self.assertIsNone(context_guard._usage_pct({"total_tokens": 0}, 128000))
        self.assertIsNone(context_guard._usage_pct({"total_tokens": -5}, 128000))


class TestFindModuleDir(unittest.TestCase):
    def test_finds_module_dir_with_tasks_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            module_dir = Path(tmp) / "my_module"
            (module_dir / "docs").mkdir(parents=True)
            (module_dir / "docs" / "tasks.md").write_text("- [ ] a\n")
            nested = module_dir / "sub" / "deep"
            nested.mkdir(parents=True)
            found = context_guard._find_module_dir(nested)
            self.assertEqual(found, module_dir.resolve())

    def test_returns_none_when_no_tasks_md_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            found = context_guard._find_module_dir(Path(tmp))
            self.assertIsNone(found)


class TestMaybeHandleContextPressure(unittest.TestCase):
    """Integration-style test using a fake PluginContext, no real Hermes host."""

    class _FakeCtx:
        def __init__(self, config):
            self._config = config
            self.injected = []

        def get_config(self, key, default=None):
            return self._config.get(key, default)

        def inject_message(self, message, role="user"):
            self.injected.append((message, role))
            return True

    def test_no_op_below_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            module_dir = Path(tmp) / "my_module"
            (module_dir / "docs").mkdir(parents=True)
            (module_dir / "docs" / "tasks.md").write_text("- [ ] a\n- [ ] b\n")
            import os

            old_cwd = os.getcwd()
            os.chdir(module_dir)
            try:
                ctx = self._FakeCtx({})
                # 10% usage, well below any threshold
                context_guard.maybe_handle_context_pressure(
                    ctx, usage={"total_tokens": 12800}, model="test-model"
                )
                self.assertEqual(ctx.injected, [])
                self.assertFalse((module_dir / "CLAUDE.md").exists())
            finally:
                os.chdir(old_cwd)

    def test_no_op_outside_module_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            import os

            old_cwd = os.getcwd()
            os.chdir(tmp)
            try:
                ctx = self._FakeCtx({})
                # High usage, but no docs/tasks.md anywhere up the tree
                context_guard.maybe_handle_context_pressure(
                    ctx, usage={"total_tokens": 120000}, model="test-model"
                )
                self.assertEqual(ctx.injected, [])
            finally:
                os.chdir(old_cwd)

    def test_triggers_handoff_above_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            module_dir = Path(tmp) / "my_module"
            (module_dir / "docs").mkdir(parents=True)
            # 8 tasks -> medium bucket, unchanged 60% threshold
            (module_dir / "docs" / "tasks.md").write_text(
                "\n".join(f"- [ ] task {i}" for i in range(8)) + "\n"
            )
            import os

            old_cwd = os.getcwd()
            os.chdir(module_dir)
            context_guard._last_triggered_bucket.clear()
            try:
                ctx = self._FakeCtx({})
                # 70% usage of a 128000-token window, above the 60% threshold
                context_guard.maybe_handle_context_pressure(
                    ctx, usage={"total_tokens": 89600}, model="test-model"
                )
                self.assertTrue((module_dir / "CLAUDE.md").exists())
                self.assertTrue((module_dir / "GEMINI.md").exists())
                self.assertTrue((module_dir / "AGENTS.md").exists())
                claude_md = (module_dir / "CLAUDE.md").read_text()
                self.assertIn("Dynamic Context Handoff", claude_md)
                self.assertEqual(len(ctx.injected), 1)
                self.assertIn("Context usage reached", ctx.injected[0][0])
            finally:
                os.chdir(old_cwd)
                context_guard._last_triggered_bucket.clear()

    def test_uses_the_real_context_length(self):
        with tempfile.TemporaryDirectory() as tmp:
            module_dir = Path(tmp) / "my_module"
            (module_dir / "docs").mkdir(parents=True)
            (module_dir / "docs" / "tasks.md").write_text(
                "\n".join(f"- [ ] task {i}" for i in range(8)) + "\n"
            )
            import os

            old_cwd = os.getcwd()
            os.chdir(module_dir)
            context_guard._last_triggered_bucket.clear()
            try:
                ctx = self._FakeCtx({})
                # 89,600 tokens is 70% of the 128K default but under 9% of a 1M window
                context_guard.maybe_handle_context_pressure(
                    ctx, usage={"prompt_tokens": 89600}, context_length=1_050_000, model="m"
                )
                self.assertFalse((module_dir / "CLAUDE.md").exists())
                context_guard.maybe_handle_context_pressure(
                    ctx, usage={"input_tokens": 700_000}, context_length=1_050_000, model="m"
                )
                self.assertTrue((module_dir / "CLAUDE.md").exists())
            finally:
                os.chdir(old_cwd)
                context_guard._last_triggered_bucket.clear()

    def test_never_raises_on_malformed_usage(self):
        """Fail-open guarantee: malformed hook kwargs must never raise."""
        ctx = self._FakeCtx({})
        try:
            context_guard.maybe_handle_context_pressure(ctx, usage="not-a-dict")
            context_guard.maybe_handle_context_pressure(ctx)
            context_guard.maybe_handle_context_pressure(ctx, usage=None, model=None)
        except Exception as exc:  # noqa: BLE001
            self.fail(f"maybe_handle_context_pressure raised unexpectedly: {exc}")


if __name__ == "__main__":
    unittest.main()


class TestInjectIntoChat(unittest.TestCase):
    """A hosted chat needs the session key Hermes binds for a command; the CLI does not."""

    class _Ctx:
        def __init__(self):
            self.calls = []

        def inject_message(self, message, role="user", session_key=None):
            self.calls.append((message, role, session_key))
            return True

    def test_passes_the_bound_session_key(self):
        import types

        fake = types.ModuleType("gateway.session_context")
        fake.get_session_env = lambda name, default="": "sess-123" if name == "HERMES_SESSION_KEY" else default
        pkg = types.ModuleType("gateway")
        pkg.session_context = fake
        with unittest.mock.patch.dict(sys.modules, {"gateway": pkg, "gateway.session_context": fake}):
            ctx = self._Ctx()
            self.assertTrue(context_guard.inject_into_chat(ctx, "hi"))
        self.assertEqual(ctx.calls, [("hi", "user", "sess-123")])

    def test_without_session_context_calls_plainly(self):
        with unittest.mock.patch.dict(sys.modules, {"gateway": None, "gateway.session_context": None}):
            ctx = self._Ctx()
            self.assertTrue(context_guard.inject_into_chat(ctx, "hi", role="system"))
        self.assertEqual(ctx.calls, [("hi", "system", None)])


class TestCommandMarker(unittest.TestCase):
    def test_command_prompt_carries_marker(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import plugin

        prompt = plugin._command_prompt(
            "commands/start-coding.md", "20", "edit_remove_pricelist_rule", ""
        )
        self.assertEqual(
            prompt.splitlines()[-1],
            "[odoo-kit-command] name=start-coding version=20 args=edit_remove_pricelist_rule",
        )

    def test_parse_command_marker(self):
        text = (
            "body\n[odoo-kit-command] name=plan-analysis version=19 args=x\n"
            "more\n[odoo-kit-command] name=start-coding version=20 args=edit_remove_pricelist_rule"
        )
        self.assertEqual(
            context_guard.parse_command_marker(text),
            {"name": "start-coding", "version": "20", "args": "edit_remove_pricelist_rule"},
        )
        self.assertIsNone(context_guard.parse_command_marker("no marker here"))
        self.assertEqual(
            context_guard.parse_command_marker("[odoo-kit-command] name=testing version=- args=-"),
            {"name": "testing", "version": None, "args": None},
        )


class _HostedCtx:
    def __init__(self, config=None):
        self._config = config or {}

    def get_config(self, key, default=None):
        return self._config.get(key, default)


WINDOW = 1_050_000
MARKER = "[odoo-kit-command] name=start-coding version=20 args=edit_remove_pricelist_rule"


def _api(ctx, session, fraction, window=WINDOW):
    context_guard.on_post_api_request(
        ctx, session_id=session, usage={"prompt_tokens": int(window * fraction)}, context_length=window
    )


class TestHostedGuard(unittest.TestCase):
    def setUp(self):
        context_guard._hosted.clear()
        self.ctx = _HostedCtx()

    def test_threshold_floor_small_window(self):
        self.assertAlmostEqual(context_guard.compaction_threshold(128_000, 0.60), 0.75)
        self.assertAlmostEqual(context_guard.compaction_threshold(1_050_000, 0.60), 0.60)
        self.assertAlmostEqual(context_guard.compaction_threshold(128_000, 0.80), 0.80)

    def test_context_tokens_fallbacks(self):
        self.assertEqual(context_guard.context_tokens({"prompt_tokens": 9, "input_tokens": 5}), 9)
        self.assertEqual(context_guard.context_tokens({"input_tokens": 5, "cache_read_tokens": 3}), 8)
        self.assertEqual(context_guard.context_tokens({"input_tokens": 5}), 5)
        self.assertIsNone(context_guard.context_tokens({}))
        self.assertIsNone(context_guard.context_tokens(None))

    def test_no_note_without_pressure(self):
        _api(self.ctx, "s1", 0.30)
        self.assertIsNone(context_guard.on_transform_tool_result(self.ctx, session_id="s1", result="ok"))

    def test_save_note_once_before_compaction(self):
        context_guard.on_pre_llm_call(self.ctx, session_id="s1", user_message="go\n" + MARKER)
        _api(self.ctx, "s1", 0.56)
        _api(self.ctx, "s1", 0.57)
        out = context_guard.on_transform_tool_result(self.ctx, session_id="s1", result="ok")
        self.assertTrue(out.startswith("ok\n\n[odoo-agent-pro-kit] This chat is at 56%"))
        self.assertIn("Hermes compacts it at 60%", out)
        self.assertIn("/start-coding 20 edit_remove_pricelist_rule", out)
        self.assertIn("do not stop or ask the user to reset", out)
        self.assertIsNone(context_guard.on_transform_tool_result(self.ctx, session_id="s1", result="ok"))

    def test_save_note_small_window_comes_before_floored_compaction(self):
        _api(self.ctx, "s1", 0.65, window=128_000)
        self.assertIsNone(context_guard.on_transform_tool_result(self.ctx, session_id="s1", result="ok"))
        _api(self.ctx, "s1", 0.71, window=128_000)
        out = context_guard.on_transform_tool_result(self.ctx, session_id="s1", result="ok")
        self.assertIn("Hermes compacts it at 75%", out)

    def test_resume_note_after_shrink(self):
        context_guard.on_pre_llm_call(self.ctx, session_id="s1", user_message=MARKER)
        _api(self.ctx, "s1", 0.58)
        context_guard.on_transform_tool_result(self.ctx, session_id="s1", result="ok")  # save note
        _api(self.ctx, "s1", 0.20)
        out = context_guard.on_transform_tool_result(self.ctx, session_id="s1", result="ok")
        self.assertIn("This chat was just compacted. To carry on /start-coding 20 edit_remove_pricelist_rule", out)
        self.assertIn("continue from the first open task with the same rules", out)

    def test_resume_note_without_recorded_command(self):
        _api(self.ctx, "s2", 0.50)
        _api(self.ctx, "s2", 0.10)
        out = context_guard.on_transform_tool_result(self.ctx, session_id="s2", result="ok")
        self.assertIn("To carry on the kit command you were running: re-read", out)

    def test_sessions_kept_apart(self):
        context_guard.on_pre_llm_call(self.ctx, session_id="a", user_message=MARKER)
        context_guard.on_pre_llm_call(
            self.ctx, session_id="b",
            user_message="[odoo-kit-command] name=start-coding version=20 args=currency_rate_of_rbi",
        )
        _api(self.ctx, "a", 0.56)
        _api(self.ctx, "b", 0.56)
        self.assertIn("edit_remove_pricelist_rule", context_guard.on_transform_tool_result(self.ctx, session_id="a", result=""))
        self.assertIn("currency_rate_of_rbi", context_guard.on_transform_tool_result(self.ctx, session_id="b", result=""))

    def test_pre_llm_call_delivers_pending_note(self):
        context_guard.on_pre_llm_call(self.ctx, session_id="s1", user_message=MARKER)
        _api(self.ctx, "s1", 0.58)
        _api(self.ctx, "s1", 0.20)
        # the save note was never delivered; the resume note replaces it
        got = context_guard.on_pre_llm_call(self.ctx, session_id="s1", user_message="continue")
        self.assertIn("This chat was just compacted", got["context"])
        self.assertIsNone(context_guard.on_pre_llm_call(self.ctx, session_id="s1", user_message="x"))

    def test_guard_never_raises(self):
        self.assertIsNone(context_guard.on_post_api_request(self.ctx, usage="junk", context_length="x"))
        self.assertIsNone(context_guard.on_transform_tool_result(self.ctx, result=None))
        self.assertIsNone(context_guard.on_pre_llm_call(None, session_id=None, user_message=object()))


class TestHostedGuardRegistration(unittest.TestCase):
    def test_register_wires_the_hosted_hooks(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        import plugin

        ctx = unittest.mock.MagicMock()
        plugin.register(ctx)
        hooks = {c.args[0]: c.args[1] for c in ctx.register_hook.call_args_list}
        for name in ("post_api_request", "pre_llm_call", "transform_tool_result"):
            self.assertIn(name, hooks)
        guard = sys.modules["plugin.context_guard"]
        guard._hosted.clear()
        hooks["pre_llm_call"](session_id="r1", user_message="[odoo-kit-command] name=testing version=20 args=m")
        self.assertEqual(guard._hosted["r1"]["command"]["name"], "testing")


class TestHostedGuardSessionSplit(unittest.TestCase):
    def setUp(self):
        context_guard._hosted.clear()
        self.ctx = _HostedCtx()

    def test_resume_note_survives_a_compression_split(self):
        # Hermes's compaction can move the chat to a new session id; the chat's key stays.
        with unittest.mock.patch.object(context_guard, "_bound_session_key", return_value="chat-1"):
            context_guard.on_pre_llm_call(self.ctx, session_id="parent", user_message=MARKER)
            _api(self.ctx, "parent", 0.58)
            context_guard.on_transform_tool_result(self.ctx, session_id="parent", result="ok")
            _api(self.ctx, "child", 0.20)
            out = context_guard.on_transform_tool_result(self.ctx, session_id="child", result="ok")
        self.assertIn("This chat was just compacted. To carry on /start-coding 20 edit_remove_pricelist_rule", out)

    def test_without_a_session_key_the_session_id_is_used(self):
        with unittest.mock.patch.object(context_guard, "_bound_session_key", return_value=""):
            context_guard.on_pre_llm_call(self.ctx, session_id="a", user_message=MARKER)
            _api(self.ctx, "a", 0.56)
            self.assertIn("edit_remove_pricelist_rule", context_guard.on_transform_tool_result(self.ctx, session_id="a", result=""))
