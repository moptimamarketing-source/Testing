#!/usr/bin/env python3
"""
Bina data/snapshot.json untuk dashboard live (kemas kini setiap jam).

Baca sahaja. Guna meta_api.py yang sama dengan skrip lain. Tiada token dipaparkan.

    python build_snapshot.py              # 30 hari terakhir (termasuk hari ini)
    python build_snapshot.py --days 14
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

from meta_api import ROOT, MetaAds, f, load_config, load_env, match_area

# Jenis action yang dikira "lead" sebenar (bukan klik)
LEAD_TYPES = [
    "onsite_conversion.messaging_conversation_started_7d",
    "onsite_conversion.lead_grouped",
    "lead",
]

MYT = timezone(timedelta(hours=8))


def action_val(row: dict, key: str) -> float:
    for a in row.get("actions") or []:
        if a.get("action_type") == key:
            return f(a.get("value"))
    return 0.0


def leads_of(row: dict) -> tuple[float, str]:
    """Lead = jenis pertama dalam LEAD_TYPES yang ada. Klik TIDAK dikira lead."""
    for t in LEAD_TYPES:
        v = action_val(row, t)
        if v:
            return v, t
    return 0.0, ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=30)
    args = ap.parse_args()

    config = load_config()
    api = MetaAds(load_env())
    areas = config.get("areas", {})

    now = datetime.now(MYT)
    until = now.date()
    since = until - timedelta(days=args.days - 1)
    tr = json.dumps({"since": since.isoformat(), "until": until.isoformat()})
    base = "spend,impressions,clicks,ctr,cpm,reach,actions"

    # 1) Trend harian (akaun)
    daily_raw = api.get_all(
        f"{api.account_id}/insights",
        {"level": "account", "time_increment": 1, "time_range": tr, "fields": base, "limit": 500},
    )
    daily = []
    for r in sorted(daily_raw, key=lambda x: x["date_start"]):
        l, _ = leads_of(r)
        daily.append(
            {
                "d": r["date_start"],
                "spend": round(f(r.get("spend")), 2),
                "leads": l,
                "clicks": int(action_val(r, "link_click")),
                "impr": int(f(r.get("impressions"))),
                "custom": int(action_val(r, "offsite_conversion.fb_pixel_custom")),
            }
        )

    # 2) Status campaign
    camps = api.get_all(
        f"{api.account_id}/campaigns",
        {"fields": "name,effective_status,objective,daily_budget", "limit": 500},
    )
    meta = {c["id"]: c for c in camps}

    # 3) Ikut campaign dan ikut iklan (tempoh penuh)
    def pull(level: str, extra: str) -> list:
        return api.get_all(
            f"{api.account_id}/insights",
            {"level": level, "time_range": tr, "fields": f"{extra},{base}", "limit": 500},
        )

    camp_raw = pull("campaign", "campaign_id,campaign_name")
    ad_raw = pull("ad", "campaign_name,adset_name,ad_name,ad_id")

    def row(r: dict, name: str, blob: str) -> dict:
        l, lt = leads_of(r)
        spend = f(r.get("spend"))
        return {
            "name": name,
            "area": match_area(blob, areas),
            "spend": round(spend, 2),
            "impr": int(f(r.get("impressions"))),
            "clicks": int(action_val(r, "link_click")),
            "ctr": round(f(r.get("ctr")), 2),
            "cpm": round(f(r.get("cpm")), 2),
            "leads": l,
            "lead_type": lt,
            "cpl": round(spend / l, 2) if l else None,
            "lpv": int(action_val(r, "landing_page_view")),
            "custom": int(action_val(r, "offsite_conversion.fb_pixel_custom")),
            "cpc_custom": round(spend / action_val(r, "offsite_conversion.fb_pixel_custom"), 2)
            if action_val(r, "offsite_conversion.fb_pixel_custom") else None,
        }

    campaigns = []
    for r in camp_raw:
        m = meta.get(r.get("campaign_id"), {})
        x = row(r, r.get("campaign_name", ""), r.get("campaign_name", ""))
        x["status"] = m.get("effective_status", "?")
        x["objective"] = m.get("objective", "?")
        campaigns.append(x)
    campaigns.sort(key=lambda c: -c["spend"])

    ads = []
    for r in ad_raw:
        blob = " ".join([r.get("campaign_name", ""), r.get("adset_name", ""), r.get("ad_name", "")])
        x = row(r, r.get("ad_name", ""), blob)
        x["campaign"] = r.get("campaign_name", "")
        x["id"] = r.get("ad_id", "")
        ads.append(x)
    ads.sort(key=lambda a: -a["spend"])

    tot_spend = sum(c["spend"] for c in campaigns)
    tot_leads = sum(c["leads"] for c in campaigns)
    tot_clicks = sum(c["clicks"] for c in campaigns)
    tot_custom = sum(c["custom"] for c in campaigns)
    tot_lpv = sum(c["lpv"] for c in campaigns)
    snap = {
        "generated_at": now.isoformat(timespec="minutes"),
        "since": since.isoformat(),
        "until": until.isoformat(),
        "currency": config.get("currency", "RM"),
        "max_cpl": config.get("max_cpl"),
        "totals": {
            "spend": round(tot_spend, 2),
            "leads": tot_leads,
            "clicks": tot_clicks,
            "impr": sum(c["impr"] for c in campaigns),
            "cpl": round(tot_spend / tot_leads, 2) if tot_leads else None,
            "cost_per_click": round(tot_spend / tot_clicks, 2) if tot_clicks else None,
            "custom": tot_custom,
            "lpv": tot_lpv,
            "cost_per_custom": round(tot_spend / tot_custom, 2) if tot_custom else None,
        },
        "daily": daily,
        "campaigns": campaigns,
        "ads": ads[:60],
    }
    # Fail dataset untuk dashboard artifact: {rows, meta}
    meta = [{"label": "Dijana", "value": snap["generated_at"]},
            {"label": "Tempoh", "value": f"{snap['since']} hingga {snap['until']}"},
            {"label": "Sumber", "value": "Meta Marketing API (build_snapshot.py)"}]
    for name, rows_ in (("daily", daily), ("campaigns", campaigns), ("ads", ads[:60])):
        (ROOT / "data").mkdir(exist_ok=True)
        (ROOT / "data" / f"ds_{name}.json").write_text(
            json.dumps({"rows": rows_, "meta": meta}, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
    out = ROOT / "data" / "snapshot.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Snapshot siap: {out.relative_to(ROOT)} ({out.stat().st_size/1024:.1f} KB) "
          f"| {len(campaigns)} campaign, {len(ads)} iklan, {len(daily)} hari")


if __name__ == "__main__":
    main()
