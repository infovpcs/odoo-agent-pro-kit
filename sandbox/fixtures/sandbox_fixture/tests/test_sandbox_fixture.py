from odoo.tests import TransactionCase


class TestSandboxFixture(TransactionCase):
    """One real test, so the CI smoke run's module test has something to run (an empty run fails)."""

    def test_installed_record_and_default_marker(self):
        record = self.env.ref("sandbox_fixture.fixture_record")
        self.assertEqual(record.name, "Phase 2 fixture")
        self.assertEqual(record.lifecycle_marker, "installed")
        created = self.env["sandbox.fixture"].create({"name": "created in a test"})
        self.assertEqual(created.lifecycle_marker, "installed")
