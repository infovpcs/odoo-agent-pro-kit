# Render one real PDF report inside a running sandbox session.
#
# Piped into `odoo shell` in the Odoo container, next to the running server:
#   sandboxctl exec <session> -- sh -c \
#     'odoo shell --config /etc/odoo/odoo.conf --database sandbox_db --no-http < /workspace/scripts/report-pdf-smoke.py'
# wkhtmltopdf loads the report's CSS from report.url over HTTP, so this proves the image's
# wkhtmltopdf, fonts, and asset serving work together, not only that the binary starts.
# Nothing is committed.
import json
import os

url = os.environ.get("ODOO_URL", "http://127.0.0.1:8069")
params = env["ir.config_parameter"].sudo()
(params.set_str if hasattr(params, "set_str") else params.set_param)("report.url", url)  # Odoo 20: set_str
module = env["ir.module.module"].search([("name", "=", "base")])
pdf, kind = env["ir.actions.report"]._render_qweb_pdf("base.ir_module_reference_print", module.ids)
assert kind == "pdf", kind
assert pdf.startswith(b"%PDF-"), pdf[:16]
assert len(pdf) > 2000, len(pdf)
print(json.dumps({"report": "base.ir_module_reference_print", "pdf_bytes": len(pdf), "report_url": url}))
env.cr.rollback()
