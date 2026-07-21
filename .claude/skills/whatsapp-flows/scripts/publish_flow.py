#!/usr/bin/env python
"""Create, validate and (optionally) publish a WhatsApp Flow via the
Graph API, reusing the access token stored on a yeeko ``Account``.

Safe by design: the Flow is created as DRAFT, its ``validation_errors``
are fetched, and it is published only when they are empty and ``--publish``
is given (a published Flow cannot be edited, only cloned/deleted).

Token source order: ``--pid`` (read ``Account.token`` from the DB, never
printed) or the ``WA_TOKEN`` env var as a fallback for use outside this
repo.

Usage:
    python publish_flow.py --json assets/multiselect.flow.json \\
        --name "Multiselect genérico" --categories OTHER \\
        --waba 3449947368500778 --pid 1128183617053069 --publish
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


def _resolve_token(pid: Optional[str]) -> str:
    if not pid:
        token = os.environ.get("WA_TOKEN")
        if not token:
            sys.exit("No token: pass --pid or set WA_TOKEN.")
        return token

    # Bootstrap Django so we can read the token from the Account row
    # instead of passing the secret on the command line.
    repo_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(repo_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    import django

    django.setup()
    from infrastructure.place.models import Account

    account = Account.objects.filter(pk=pid).first()
    if not account or not account.token:
        sys.exit(f"Account {pid} not found or has no token.")
    return account.token


def _graph(method: str, path: str, token: str, version: str,
           fields: Optional[dict] = None) -> dict:
    base = f"https://graph.facebook.com/{version}/{path}"
    payload = dict(fields or {}, access_token=token)
    data = urllib.parse.urlencode(payload).encode()
    if method == "GET":
        request = urllib.request.Request(f"{base}?{data.decode()}")
    else:
        request = urllib.request.Request(base, data=data, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        sys.exit(f"Graph {method} {path} -> HTTP {exc.code}: {body}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="path to Flow JSON (omit with "
                        "--flow-id to publish an existing draft)")
    parser.add_argument("--name", help="required unless --flow-id is set")
    parser.add_argument("--flow-id", default=None,
                        help="publish this existing draft instead of "
                        "creating a new Flow")
    parser.add_argument("--categories", default="OTHER",
                        help="comma-separated Meta categories")
    parser.add_argument("--waba", required=True, help="WABA id")
    parser.add_argument("--pid", default=None,
                        help="Account pid to read the token from")
    parser.add_argument("--version", default="v21.0")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()

    token = _resolve_token(args.pid)

    if args.flow_id:
        flow_id = args.flow_id
        print("using existing flow id:", flow_id)
    else:
        if not args.json or not args.name:
            sys.exit("--json and --name are required to create a Flow.")
        flow_json = Path(args.json).read_text(encoding="utf-8")
        categories = json.dumps(
            [c.strip() for c in args.categories.split(",") if c.strip()])
        created = _graph(
            "POST", f"{args.waba}/flows", token, args.version,
            {"name": args.name, "categories": categories,
             "flow_json": flow_json})
        flow_id = created.get("id")
        print("created flow id:", flow_id)

    detail = _graph(
        "GET", str(flow_id), token, args.version,
        {"fields": "id,name,status,categories,validation_errors"})
    errors = detail.get("validation_errors") or []
    print("status:", detail.get("status"))
    print("validation_errors:", json.dumps(errors, ensure_ascii=False))

    if errors:
        sys.exit("Validation errors present; not publishing.")

    if not args.publish:
        print("Draft OK. Re-run with --publish to publish.")
        return

    published = _graph("POST", f"{flow_id}/publish", token, args.version)
    print("publish response:", json.dumps(published, ensure_ascii=False))

    final = _graph("GET", str(flow_id), token, args.version,
                   {"fields": "id,name,status"})
    print("FINAL status:", final.get("status"), "| flow_id:", flow_id)


if __name__ == "__main__":
    main()
