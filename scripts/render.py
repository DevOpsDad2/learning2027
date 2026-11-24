#!/usr/bin/env python3
"""Render Cisco IOS configs from YAML data and Jinja2 templates.

    python scripts/render.py              # render every host into output/
    python scripts/render.py --host r1    # render one host
    python scripts/render.py --stdout     # print instead of writing files

Data flow:  data/global.yaml + data/hosts/<host>.yaml  ->  templates/ios/<role>.j2  ->  output/<host>.cfg
"""

from __future__ import annotations

import argparse
import ipaddress
import os
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
TEMPLATE_DIR = REPO_ROOT / "templates"
OUTPUT_DIR = REPO_ROOT / "output"

REQUIRED_KEYS = ("hostname", "role", "interfaces")
ROLE_TEMPLATES = {
    "router": "ios/router.j2",
    "switch": "ios/switch.j2",
}


# ---------- Jinja2 filters ----------------------------------------------------

def ipv4_address(cidr: str) -> str:
    """'10.0.12.1/30' -> '10.0.12.1'"""
    return str(ipaddress.ip_interface(cidr).ip)


def ipv4_netmask(cidr: str) -> str:
    """'10.0.12.1/30' -> '255.255.255.252'"""
    return str(ipaddress.ip_interface(cidr).netmask)


# ---------- data loading ------------------------------------------------------

def load_yaml(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top level must be a mapping (key: value)")
    return data


def load_host(host_file: Path, global_vars: dict) -> dict:
    """Merge global vars with one host's vars. Host values win."""
    host_vars = load_yaml(host_file)
    missing = [k for k in REQUIRED_KEYS if k not in host_vars]
    if missing:
        raise ValueError(f"{host_file.name}: missing required keys: {', '.join(missing)}")
    if host_vars["role"] not in ROLE_TEMPLATES:
        raise ValueError(
            f"{host_file.name}: unknown role {host_vars['role']!r} "
            f"(expected one of: {', '.join(ROLE_TEMPLATES)})"
        )
    for intf in host_vars["interfaces"]:
        if "ipv4" in intf:
            ipaddress.ip_interface(intf["ipv4"])  # raises ValueError on a typo
    return {**global_vars, **host_vars}


def admin_secret() -> str:
    secret = os.environ.get("LAB_ADMIN_SECRET")
    if not secret:
        print("warning: LAB_ADMIN_SECRET not set; rendering placeholder 'CHANGE_ME'", file=sys.stderr)
        return "CHANGE_ME"
    return secret


# ---------- rendering ---------------------------------------------------------

def build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        undefined=StrictUndefined,   # a missing YAML key is an error, not a blank line
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.filters["ipv4_address"] = ipv4_address
    env.filters["ipv4_netmask"] = ipv4_netmask
    return env


def render_host(env: Environment, host_vars: dict) -> str:
    template = env.get_template(ROLE_TEMPLATES[host_vars["role"]])
    return template.render(**host_vars)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", help="render only this host (file name without .yaml)")
    parser.add_argument("--stdout", action="store_true", help="print configs instead of writing files")
    args = parser.parse_args(argv)

    global_vars = load_yaml(DATA_DIR / "global.yaml")
    global_vars["admin_secret"] = admin_secret()

    host_files = sorted((DATA_DIR / "hosts").glob("*.yaml"))
    if args.host:
        host_files = [f for f in host_files if f.stem == args.host]
        if not host_files:
            print(f"error: no data/hosts/{args.host}.yaml", file=sys.stderr)
            return 1

    env = build_env()
    OUTPUT_DIR.mkdir(exist_ok=True)
    for host_file in host_files:
        config = render_host(env, load_host(host_file, global_vars))
        if args.stdout:
            print(config)
        else:
            out_file = OUTPUT_DIR / f"{host_file.stem}.cfg"
            out_file.write_text(config, encoding="utf-8")
            print(f"rendered {out_file.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
