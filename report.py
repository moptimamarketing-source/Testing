"""Report level ad. Guna: python3 report.py 2026-11-01 2026-11-15"""
import json, sys
from meta_api import ACCOUNT, check_env, get

check_env()
since, until = sys.argv[1], sys.argv[2]
params = dict(level="ad", fields="campaign_name,ad_name,spend,impressions,reach,clicks,ctr,actions,cost_per_action_type",
              time_range=json.dumps({"since": since, "until": until}), limit=200)
rows, res = [], get(f"{ACCOUNT}/insights", **params)
while True:
    rows += res.get("data", [])
    nxt = res.get("paging", {}).get("next")
    if not nxt: break
    import requests; res = requests.get(nxt, timeout=30).json()

KEYS = ["onsite_conversion.messaging_conversation_started_7d", "lead", "onsite_conversion.lead_grouped"]
out = []
for r in rows:
    acts = {a["action_type"]: float(a["value"]) for a in r.get("actions", [])}
    res_ = next((acts[k] for k in KEYS if k in acts), 0)
    out.append(dict(campaign=r["campaign_name"], ad=r["ad_name"], spend=float(r["spend"]), impr=int(r["impressions"]),
                    reach=int(r.get("reach", 0)), clicks=int(r.get("clicks", 0)), ctr=float(r.get("ctr", 0)), results=res_,
                    link_clicks=acts.get("link_click", 0)))
json.dump(out, open("report.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "iklan")
