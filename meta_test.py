"""Uji sambungan Meta Marketing API untuk satu atau lebih akaun iklan.
Token dibaca dari .env dan tidak dipaparkan.
.env: META_AD_ACCOUNT_IDS=act_111,act_222   (atau META_AD_ACCOUNT_ID=act_111)
"""
import os, sys, requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("META_ACCESS_TOKEN")
raw = os.getenv("META_AD_ACCOUNT_IDS") or os.getenv("META_AD_ACCOUNT_ID", "")
accts = [a.strip() for a in raw.split(",") if a.strip() and a.strip() != "act_"]
ver = os.getenv("META_API_VERSION", "v23.0")
if not token or not accts:
    sys.exit("META_ACCESS_TOKEN / META_AD_ACCOUNT_IDS belum diisi dalam .env")

h = {"Authorization": f"Bearer {token}"}
STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW", 9: "GRACE_PERIOD", 101: "CLOSED"}
for acct in accts:
    base = f"https://graph.facebook.com/{ver}/{acct}"
    info = requests.get(base, headers=h, params={"fields": "name,account_status,currency"}, timeout=30).json()
    if "error" in info:
        print(f"[{acct}] Ralat Meta: code {info['error'].get('code')} - {info['error'].get('message')}")
        continue
    ins = requests.get(f"{base}/insights", headers=h, params={"date_preset": "last_7d", "fields": "spend"}, timeout=30).json()
    spend = (ins.get("data") or [{}])[0].get("spend", "0")
    st = STATUS.get(info.get("account_status"), info.get("account_status"))
    print(f"Akaun: {info['name']} ({acct[:4]}…) · Status: {st} · Spend 7 hari: {spend} {info['currency']}")
