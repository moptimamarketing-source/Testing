"""Uji sambungan Meta Marketing API. Token dibaca dari .env, tidak dipaparkan."""
import os, sys, requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("META_ACCESS_TOKEN")
acct = os.getenv("META_AD_ACCOUNT_ID")
ver = os.getenv("META_API_VERSION", "v23.0")
if not token or not acct or acct == "act_":
    sys.exit("META_ACCESS_TOKEN / META_AD_ACCOUNT_ID belum diisi dalam .env")

base = f"https://graph.facebook.com/{ver}/{acct}"
h = {"Authorization": f"Bearer {token}"}
info = requests.get(base, headers=h, params={"fields": "name,account_status,currency"}, timeout=30).json()
if "error" in info:
    sys.exit(f"Ralat Meta: code {info['error'].get('code')} - {info['error'].get('message')}")
ins = requests.get(f"{base}/insights", headers=h, params={"date_preset": "last_7d", "fields": "spend"}, timeout=30).json()
spend = (ins.get("data") or [{}])[0].get("spend", "0")
status = {1: "ACTIVE", 2: "DISABLED"}.get(info.get("account_status"), info.get("account_status"))
print(f"Akaun: {info['name']} ({acct[:4]}…)\nStatus: {status} · Mata wang: {info['currency']}\nSpend 7 hari: {spend} {info['currency']}")
