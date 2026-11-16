"""Report harian. Guna: python3 daily.py 2026-11-01 2026-11-15"""
import json, sys
from meta_api import ACCOUNT, check_env, get

check_env()
since, until = sys.argv[1], sys.argv[2]
res = get(f"{ACCOUNT}/insights", level="campaign", time_increment=1, limit=500,
          fields="campaign_name,spend,impressions,clicks,actions",
          time_range=json.dumps({"since": since, "until": until}))
rows = res.get("data", [])
import requests
while res.get("paging", {}).get("next"):
    res = requests.get(res["paging"]["next"], timeout=30).json(); rows += res.get("data", [])

days = {}
for r in rows:
    acts = {a["action_type"]: float(a["value"]) for a in r.get("actions", [])}
    w = "WHATSFORM" in r["campaign_name"].upper()
    n = acts.get("offsite_conversion.fb_pixel_custom", 0) if w else acts.get("lead", 0)
    d = days.setdefault(r["date_start"], dict(spend=0, impr=0, clicks=0, hasil=0, pcs=[0, 0]))
    d["spend"] += float(r["spend"]); d["impr"] += int(r["impressions"]); d["clicks"] += int(r["clicks"]); d["hasil"] += n
    if "PCS" in r["campaign_name"].upper() and not w:
        d["pcs"][0] += float(r["spend"]); d["pcs"][1] += n
json.dump(days, open("daily.json", "w"), indent=1)
print("Tarikh      Spend   Impr  Klik  Hasil    CPL")
for k in sorted(days):
    d = days[k]; cpl = d["spend"] / d["hasil"] if d["hasil"] else 0
    print(f"{k} {d['spend']:8.2f} {d['impr']:6} {d['clicks']:5} {d['hasil']:5.0f} {cpl:7.2f}")
T = lambda f: sum(f(d) for d in days.values())
s, h = T(lambda d: d["spend"]), T(lambda d: d["hasil"])
print(f"JUMLAH     {s:8.2f} {T(lambda d:d['impr']):6} {T(lambda d:d['clicks']):5} {h:5.0f} {s/h:7.2f}")
