"""Report prestasi iklan 7 hari (level ad). Bacaan sahaja; tiada perubahan dibuat.
.env: META_ACCESS_TOKEN, META_AD_ACCOUNT_IDS (atau META_AD_ACCOUNT_ID), META_API_VERSION
"""
import os, sys, requests
from dotenv import load_dotenv

load_dotenv()
token = os.getenv("META_ACCESS_TOKEN")
raw = os.getenv("META_AD_ACCOUNT_IDS") or os.getenv("META_AD_ACCOUNT_ID", "")
accts = [a.strip() for a in raw.split(",") if a.strip() and a.strip() != "act_"]
ver = os.getenv("META_API_VERSION", "v23.0")
if not token or not accts:
    sys.exit("META_ACCESS_TOKEN / META_AD_ACCOUNT_IDS belum diisi")

# Hasil = 3 jenis (ditetapkan oleh pemilik akaun):
RESULT_TYPES = {
    "Website lead": "offsite_conversion.fb_pixel_lead",
    "WhatsFormSubmit": "offsite_conversion.custom.952878694093622",   # custom conversion 'Lead WhatsForm'
    "Chat dimulakan": "onsite_conversion.messaging_conversation_started_7d",
}
H = {"Authorization": f"Bearer {token}"}

def get_all(url, params):
    rows = []
    while url:
        r = requests.get(url, headers=H, params=params, timeout=60).json()
        if "error" in r:
            sys.exit(f"Ralat Meta: code {r['error'].get('code')} - {r['error'].get('message')}")
        rows += r.get("data", [])
        url, params = r.get("paging", {}).get("next"), None
    return rows

def breakdown(row):
    out = {}
    for label, t in RESULT_TYPES.items():
        out[label] = sum(int(float(x["value"])) for x in row.get("actions", []) if x["action_type"] == t)
    return out

def result_of(row):
    return sum(breakdown(row).values())

for acct in accts:
    cur = requests.get(f"https://graph.facebook.com/{ver}/{acct}", headers=H,
                       params={"fields": "name,currency"}, timeout=30).json()
    rows = get_all(f"https://graph.facebook.com/{ver}/{acct}/insights", {
        "level": "ad", "date_preset": "last_7d", "limit": 200,
        "fields": "ad_name,campaign_name,spend,impressions,inline_link_click_ctr,ctr,actions",
    })
    data = []
    for r in rows:
        spend = float(r.get("spend", 0)); res = result_of(r)
        data.append({"ad": r.get("ad_name", "?"), "spend": spend, "imp": int(r.get("impressions", 0)),
                     "ctr": float(r.get("ctr", 0)), "res": res,
                     "cpr": spend / res if res else None})
    brk = {k: sum(breakdown(r)[k] for r in rows) for k in RESULT_TYPES}
    tot_s = sum(d["spend"] for d in data); tot_r = sum(d["res"] for d in data)
    print(f"\n=== {cur.get('name')} ({acct[:4]}…) · 7 hari lepas · {cur.get('currency')} ===")
    print(f"Jumlah spend: RM {tot_s:,.2f} · Hasil (website lead + WhatsFormSubmit + chat): {tot_r} · Purata kos/hasil: "
          f"{'RM %.2f' % (tot_s/tot_r) if tot_r else '-'} · Bilangan ad: {len(data)}\n")
    print("Pecahan hasil: " + " · ".join(f"{k} {v}" for k, v in brk.items()) + "\n")
    ranked = sorted(data, key=lambda d: (d["cpr"] is None, d["cpr"] or 0))
    print(f"{'Ad':44}{'Spend':>10}{'Impr':>9}{'CTR':>7}{'Hasil':>7}{'RM/hasil':>10}")
    print("-" * 87)
    for d in ranked:
        cpr = f"{d['cpr']:.2f}" if d["cpr"] else "-"
        print(f"{d['ad'][:43]:44}{d['spend']:>10.2f}{d['imp']:>9}{d['ctr']:>6.1f}%{d['res']:>7}{cpr:>10}")
    with_res = [d for d in ranked if d["cpr"]]
    print("\nPemenang (kos/hasil terendah, min 3 hasil):")
    for d in [x for x in with_res if x["res"] >= 3][:3]:
        print(f"  ★ {d['ad'][:50]} · RM {d['cpr']:.2f}/hasil · {d['res']} hasil")
    print("Paling membazir (spend tinggi, hasil rendah/tiada):")
    avg = (tot_s / tot_r) if tot_r else 0
    cand = [d for d in data if d["spend"] >= 20 and (d["res"] == 0 or (avg and d["cpr"] > 2 * avg))]
    waste = sorted(cand, key=lambda d: -d["spend"])[:3]
    for d in waste:
        print(f"  ⚠ {d['ad'][:50]} · spend RM {d['spend']:.2f} · {d['res']} hasil")
