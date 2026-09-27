"""The repository is public: tracked files must not carry real host addresses or SSH logins."""
import ipaddress
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IPV4 = re.compile(r"(?<![\w.])(\d{1,3}(?:\.\d{1,3}){3})(?![\w.])")
# Odoo module/series versions (17.0.1.0, 19.0.0.2, 20.0.1.0) and tool versions (0.12.6.1) look like IPs.
VERSION = re.compile(r"^(?:0|1[0-9]|20)\.")


def tracked_text_files():
    names = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.split()
    for name in names:
        path = ROOT / name
        if path.is_file() and path.suffix not in {".png", ".jpg", ".gif", ".pdf", ".ico", ".woff", ".woff2", ".tgz", ".gz"}:
            try:
                yield name, path.read_text()
            except UnicodeDecodeError:
                continue


def test_no_public_ipv4_addresses_in_tracked_files():
    found = []
    for name, text in tracked_text_files():
        for match in IPV4.finditer(text):
            value = match.group(1)
            if VERSION.match(value):
                continue
            try:
                address = ipaddress.ip_address(value)
            except ValueError:
                continue
            if address.is_global:
                found.append(f"{name}: {value}")
    assert not found, "public host addresses must stay out of this public repository:\n" + "\n".join(found)


def test_no_ssh_login_to_a_literal_host():
    login = re.compile(r"\b(?:ubuntu|opc|root|ec2-user)@\d{1,3}(?:\.\d{1,3}){3}\b")
    found = [name for name, text in tracked_text_files() if login.search(text)]
    assert not found, found
