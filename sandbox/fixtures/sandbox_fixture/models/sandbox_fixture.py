from odoo import fields, models


class SandboxFixture(models.Model):
    _name = "sandbox.fixture"
    _description = "Docker Sandbox Fixture"

    name = fields.Char(required=True)
    lifecycle_marker = fields.Char(default="installed")
