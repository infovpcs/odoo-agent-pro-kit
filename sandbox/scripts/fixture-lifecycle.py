#!/usr/bin/env python3
"""Exercise fixture CRUD through the protocol selected for this Odoo series."""

import json
import os
import urllib.request
import xmlrpc.client

URL = "http://127.0.0.1:8069"
DB = "sandbox_db"
MODEL = "sandbox.fixture"


def xmlrpc_lifecycle():
    password = os.environ["ODOO_API_PASSWORD"]
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    version = common.version()
    uid = common.authenticate(DB, "admin", password, {})
    assert uid
    objects = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    seeded = objects.execute_kw(DB, uid, password, MODEL, "search_read", [[("name", "=", "Phase 2 fixture")]], {"fields": ["lifecycle_marker"]})
    assert seeded and seeded[0]["lifecycle_marker"] == "updated"
    record_id = objects.execute_kw(DB, uid, password, MODEL, "create", [{"name": "rpc-created"}])
    row = objects.execute_kw(DB, uid, password, MODEL, "read", [[record_id]], {"fields": ["name", "lifecycle_marker"]})[0]
    assert row["name"] == "rpc-created" and row["lifecycle_marker"] == "installed"
    assert objects.execute_kw(DB, uid, password, MODEL, "write", [[record_id], {"lifecycle_marker": "updated"}])
    assert objects.execute_kw(DB, uid, password, MODEL, "unlink", [[record_id]])
    return version["server_version"]


def json2(method, body):
    request = urllib.request.Request(
        f"{URL}/json/2/{MODEL}/{method}",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"bearer {os.environ['ODOO_API_KEY']}",
            "Content-Type": "application/json; charset=utf-8",
            "X-Odoo-Database": DB,
        },
    )
    return json.load(urllib.request.urlopen(request, timeout=10))


def json2_lifecycle():
    seeded = json2("search_read", {"domain": [["name", "=", "Phase 2 fixture"]], "fields": ["lifecycle_marker"]})
    assert seeded and seeded[0]["lifecycle_marker"] == "updated"
    created = json2("create", {"vals_list": {"name": "rpc-created"}})
    record_id = created[0] if isinstance(created, list) else created
    row = json2("read", {"ids": [record_id], "fields": ["name", "lifecycle_marker"], "load": None})[0]
    assert row["name"] == "rpc-created" and row["lifecycle_marker"] == "installed"
    assert json2("write", {"ids": [record_id], "vals": {"lifecycle_marker": "updated"}})
    assert json2("unlink", {"ids": [record_id]})
    return "19.0"


protocol = os.environ["ODOO_RPC_PROTOCOL"]
server_version = xmlrpc_lifecycle() if protocol == "xmlrpc" else json2_lifecycle()
print(json.dumps({"protocol": protocol, "server_version": server_version, "crud": "passed"}))
