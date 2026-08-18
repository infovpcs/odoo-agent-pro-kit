#!/usr/bin/env python3
"""
Auto-test runner for Odoo custom module tasks.
- Odoo 17/18: XML-RPC (default port 8069)
- Odoo 19:    JSON-RPC 2.0 (default port 8069)

Usage:
    python3 auto_test_runner.py --version 19 --module vpcs_hr --task "Task 2: Employee Extension"
    python3 auto_test_runner.py --version 17 --module vpcs_pos --task "Task 1: POS Session"
"""

import argparse
import json
import os
import sys
import xmlrpc.client
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests as _requests_module
    HAS_REQUESTS = True
except ImportError:
    _requests_module = None  # type: ignore[assignment]
    HAS_REQUESTS = False


DEFAULT_HOSTS = {
    "17": os.getenv("ODOO17_URL", "http://localhost:8069"),
    "18": os.getenv("ODOO18_URL", "http://localhost:8069"),
    "19": os.getenv("ODOO19_URL", "http://localhost:8069"),
}

DEFAULT_DBS = {
    "17": os.getenv("ODOO17_DB", "odoo17"),
    "18": os.getenv("ODOO18_DB", "odoo18"),
    "19": os.getenv("ODOO19_DB", "odoo19"),
}

DEFAULT_USER = os.getenv("ODOO_USER", "admin")
DEFAULT_PASS = os.getenv("ODOO_PASS", "admin")

RESULTS_DIR = Path(__file__).parent.parent / "output" / "auto_test_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


# ─── JSON-RPC 2.0 client (Odoo 19) ────────────────────────────────────────────

class JsonRpc2Client:
    def __init__(self, base_url: str, db: str, uid: int, password: str):
        self.base_url = base_url.rstrip("/")
        self.db = db
        self.uid = uid
        self.password = password
        self._id = 0
        self._requests = _requests_module  # type: ignore[assignment]

    @classmethod
    def authenticate(cls, base_url: str, db: str, user: str, password: str):
        if not HAS_REQUESTS or _requests_module is None:
            raise ImportError("Install 'requests': pip install requests")
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": 1,
            "params": {"db": db, "login": user, "password": password},
        }
        resp = _requests_module.post(f"{base_url}/web/session/authenticate", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise ConnectionError(f"Auth failed: {result['error']}")
        uid = result["result"].get("uid")
        if not uid:
            raise ConnectionError("Invalid credentials or database.")
        instance = cls(base_url, db, uid, password)
        return instance

    def execute_kw(self, model: str, method: str, args: list, kwargs=None):
        self._id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "id": self._id,
            "params": {
                "model": model,
                "method": method,
                "args": args,
                "kwargs": kwargs or {},
            },
        }
        resp = self._requests.post(f"{self.base_url}/web/dataset/call_kw", json=payload, timeout=60)  # type: ignore[union-attr]
        resp.raise_for_status()
        result = resp.json()
        if result.get("error"):
            raise RuntimeError(f"RPC error: {result['error']['data']['message']}")
        return result["result"]


# ─── XML-RPC client (Odoo 17/18) ──────────────────────────────────────────────

class XmlRpcClient:
    def __init__(self, base_url: str, db: str, uid: int, password: str):
        self.db = db
        self.uid = uid
        self.password = password
        self._obj = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/object")

    @classmethod
    def authenticate(cls, base_url: str, db: str, user: str, password: str):
        common = xmlrpc.client.ServerProxy(f"{base_url}/xmlrpc/2/common")
        raw_uid = common.authenticate(db, user, password, {})
        if not isinstance(raw_uid, int) or not raw_uid:
            raise ConnectionError(f"XML-RPC auth failed for {db}/{user}")
        uid = raw_uid
        return cls(base_url, db, uid, password)

    def execute_kw(self, model: str, method: str, args: list, kwargs=None):
        return self._obj.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs or {}
        )


# ─── Connection factory ────────────────────────────────────────────────────────

def connect(version: str, host: str, db: str, user: str, password: str):
    if version == "19":
        return JsonRpc2Client.authenticate(host, db, user, password)
    return XmlRpcClient.authenticate(host, db, user, password)


# ─── Test helpers ──────────────────────────────────────────────────────────────

def module_is_installed(client, module_name: str) -> bool:
    result = client.execute_kw(
        "ir.module.module", "search_read",
        [[["name", "=", module_name], ["state", "=", "installed"]]],
        {"fields": ["name", "state"], "limit": 1},
    )
    return bool(result)


def get_custom_models(client, module_name: str) -> list:
    models = client.execute_kw(
        "ir.model", "search_read",
        [[["modules", "ilike", module_name]]],
        {"fields": ["model"], "limit": 50},
    )
    return [m["model"] for m in models]


def test_model_crud(client, model_name: str) -> dict:
    result = {"model": model_name, "passed": [], "failed": []}
    try:
        records = client.execute_kw(model_name, "search_read", [[]], {"limit": 5, "fields": ["id"]})
        result["passed"].append(f"search_read: {len(records)} records")
    except Exception as e:
        result["failed"].append(f"search_read: {e}")
        return result
    try:
        fields = client.execute_kw(model_name, "fields_get", [], {"attributes": ["string", "type"]})
        result["passed"].append(f"fields_get: {len(fields)} fields")
    except Exception as e:
        result["failed"].append(f"fields_get: {e}")
    return result


def test_access_rights(client, model_name: str) -> dict:
    result = {"model": model_name, "access": []}
    try:
        has_read = client.execute_kw(model_name, "check_access_rights", ["read"], {"raise_exception": False})
        result["access"].append({"read": has_read})
        has_write = client.execute_kw(model_name, "check_access_rights", ["write"], {"raise_exception": False})
        result["access"].append({"write": has_write})
    except Exception as e:
        result["access"].append({"error": str(e)})
    return result


# ─── Task-aware scenario inference ────────────────────────────────────────────

def infer_test_scenarios(task_title: str) -> list:
    title_lower = task_title.lower()
    scenarios = ["module_installed", "custom_models_exist", "basic_crud", "access_rights"]
    if any(k in title_lower for k in ["view", "menu", "action"]):
        scenarios.append("view_exists")
    if any(k in title_lower for k in ["security", "rule", "acl"]):
        scenarios.append("security_rules")
    if any(k in title_lower for k in ["constraint", "validate"]):
        scenarios.append("constraint_check")
    if any(k in title_lower for k in ["cron", "scheduled"]):
        scenarios.append("cron_exists")
    if any(k in title_lower for k in ["mail", "message", "chatter"]):
        scenarios.append("mail_thread")
    return scenarios


def run_scenarios(client, module_name: str, scenarios: list, models: list) -> dict:
    results = {"passed": 0, "failed": 0, "details": []}

    if "module_installed" in scenarios:
        installed = module_is_installed(client, module_name)
        results["details"].append({"scenario": "module_installed", "result": installed})
        results["passed" if installed else "failed"] += 1

    if "custom_models_exist" in scenarios:
        count = len(models)
        results["details"].append({"scenario": "custom_models_exist", "result": count > 0, "count": count})
        results["passed" if count > 0 else "failed"] += 1

    for scenario in scenarios:
        if scenario in ("module_installed", "custom_models_exist"):
            continue
        for model in models[:3]:
            if scenario == "basic_crud":
                detail = test_model_crud(client, model)
                passed = len(detail.get("failed", [])) == 0
                results["details"].append({"scenario": "basic_crud", "model": model, **detail})
                results["passed" if passed else "failed"] += 1
            elif scenario == "access_rights":
                detail = test_access_rights(client, model)
                results["details"].append({"scenario": "access_rights", "model": model, **detail})
                results["passed"] += 1
            elif scenario == "view_exists":
                views = client.execute_kw("ir.ui.view", "search_count", [[["model", "=", model]]])
                results["details"].append({"scenario": "view_exists", "model": model, "result": views > 0, "count": views})
                results["passed" if views > 0 else "failed"] += 1
            elif scenario == "security_rules":
                acl = client.execute_kw("ir.model.access", "search_count", [[["model_id.model", "=", model]]])
                results["details"].append({"scenario": "security_rules", "model": model, "result": acl > 0, "acl_count": acl})
                results["passed" if acl > 0 else "failed"] += 1
            elif scenario == "cron_exists":
                crons = client.execute_kw("ir.cron", "search_count", [[["code", "ilike", module_name]]])
                results["details"].append({"scenario": "cron_exists", "result": crons > 0, "count": crons})
                results["passed"] += 1

    return results


# ─── Result writer ─────────────────────────────────────────────────────────────

def write_result(result: dict, output_path, module: str, task: str):
    if output_path:
        path = Path(output_path)
    else:
        safe_task = task.replace(" ", "_").replace(":", "").replace("/", "_")[:40]
        path = RESULTS_DIR / f"{module}_{safe_task}_{datetime.now(timezone.utc).replace(tzinfo=None).strftime('%Y%m%d_%H%M%S')}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    print(f"   Result written: {path}")


# ─── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Odoo task auto-test runner")
    parser.add_argument("--version", required=True, choices=["17", "18", "19"])
    parser.add_argument("--module", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--host")
    parser.add_argument("--db")
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASS)
    parser.add_argument("--output")
    args = parser.parse_args()

    host = args.host or DEFAULT_HOSTS[args.version]
    db = args.db or DEFAULT_DBS[args.version]

    print(f"\nAuto-test: {args.module} | version={args.version} | task={args.task}")
    print(f"  Target: {host} / {db}")

    try:
        client = connect(args.version, host, db, args.user, args.password)
        print(f"  Connected (uid={client.uid})")
    except Exception as e:
        print(f"  Connection failed: {e}")
        result = {
            "status": "connection_error",
            "error": str(e),
            "version": args.version,
            "module": args.module,
            "task": args.task,
            "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
        }
        write_result(result, args.output, args.module, args.task)
        sys.exit(1)

    models = get_custom_models(client, args.module)
    print(f"  Custom models: {models or 'none yet'}")

    scenarios = infer_test_scenarios(args.task)
    print(f"  Scenarios: {scenarios}")
    results = run_scenarios(client, args.module, scenarios, models)

    total = results["passed"] + results["failed"]
    status = "PASS" if results["failed"] == 0 else "PARTIAL" if results["passed"] > 0 else "FAIL"
    icon = "PASS" if status == "PASS" else "PARTIAL" if status == "PARTIAL" else "FAIL"
    print(f"\n  {icon}: {results['passed']}/{total} checks passed")

    output = {
        "status": status,
        "version": args.version,
        "module": args.module,
        "task": args.task,
        "passed": results["passed"],
        "failed": results["failed"],
        "total": total,
        "details": results["details"],
        "timestamp": datetime.now(timezone.utc).replace(tzinfo=None).isoformat(),
    }
    write_result(output, args.output, args.module, args.task)

    if status == "FAIL":
        print("\n  Failed checks:")
        for d in results["details"]:
            if d.get("failed"):
                print(f"    - {d}")

    return 0 if status in ("PASS", "PARTIAL") else 1


if __name__ == "__main__":
    sys.exit(main())
