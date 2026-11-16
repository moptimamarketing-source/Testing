"""Pembantu Meta Marketing API. Token dibaca dari .env, tak pernah dipaparkan."""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("META_ACCESS_TOKEN", "")
ACCOUNT = os.getenv("META_AD_ACCOUNT_ID", "")
PAGE_ID = os.getenv("META_PAGE_ID", "")
VERSION = os.getenv("META_API_VERSION", "v23.0")
BASE = f"https://graph.facebook.com/{VERSION}"


def check_env():
    missing = [k for k, v in {"META_ACCESS_TOKEN": TOKEN, "META_AD_ACCOUNT_ID": ACCOUNT}.items()
               if not v or v == "act_"]
    if missing:
        sys.exit("Fail .env belum lengkap: " + ", ".join(missing))


def get(path, **params):
    params["access_token"] = TOKEN
    r = requests.get(f"{BASE}/{path}", params=params, timeout=30)
    if not r.ok:
        err = r.json().get("error", {})
        sys.exit(f"Ralat Meta {r.status_code}: {err.get('message')} (code {err.get('code')})")
    return r.json()


def post(path, **data):
    """Guna untuk cipta objek. Sentiasa paksa status PAUSED."""
    data["access_token"] = TOKEN
    data["status"] = "PAUSED"
    r = requests.post(f"{BASE}/{path}", data=data, timeout=30)
    if not r.ok:
        err = r.json().get("error", {})
        sys.exit(f"Ralat Meta {r.status_code}: {err.get('message')} (code {err.get('code')})")
    return r.json()
