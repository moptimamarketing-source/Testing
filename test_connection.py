"""Uji sambungan: nama akaun, mata wang, status dan spend 7 hari lepas."""
from meta_api import ACCOUNT, check_env, get

STATUS = {1: "ACTIVE", 2: "DISABLED", 3: "UNSETTLED", 7: "PENDING_RISK_REVIEW",
          9: "IN_GRACE_PERIOD", 100: "PENDING_CLOSURE", 101: "CLOSED"}

check_env()
acc = get(ACCOUNT, fields="name,currency,account_status")
ins = get(f"{ACCOUNT}/insights", fields="spend", date_preset="last_7d").get("data", [])
spend = float(ins[0]["spend"]) if ins else 0.0

print("✓ Sambungan berjaya")
print(f"  Akaun   : {acc['name']} ({ACCOUNT[:8]}•••••)")
print(f"  Status  : {STATUS.get(acc['account_status'], acc['account_status'])}  ·  Mata wang: {acc['currency']}")
print(f"  Spend 7 hari: {acc['currency']} {spend:,.2f}")
