import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "sandbox" / "schemas"


def load_schema(name):
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def test_session_schema_contract():
    schema = load_schema("session.schema.json")
    assert schema["$schema"].endswith("draft/2020-12/schema")
    assert schema["properties"]["schema_version"]["const"] == "1.0.0"
    assert schema["properties"]["odoo_version"]["enum"] == ["17.0", "18.0", "19.0"]
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) <= set(schema["properties"])


def test_operation_result_schema_contract():
    schema = load_schema("operation-result.schema.json")
    statuses = schema["properties"]["status"]["enum"]
    assert {"succeeded", "failed", "cancelled", "timed_out"} <= set(statuses)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) <= set(schema["properties"])
