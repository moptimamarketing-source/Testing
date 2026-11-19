#!/usr/bin/env python3
"""
Langkah 2: tarik data prestasi iklan dari Meta.

Contoh penggunaan:
    python pull_insights.py                        # 7 hari lepas, level ad
    python pull_insights.py --days 30              # 30 hari lepas
    python pull_insights.py --level adset          # level ad set
    python pull_insights.py --since 2026-11-01 --until 2026-11-15

Output (dalam folder data/):
    insights_<level>_<since>_<until>.csv   -> untuk Excel / Google Sheet
    latest.json                            -> untuk dashboard
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date, timedelta
from pathlib import Path

from meta_api import ROOT, MetaAds, f, load_config, load_env, match_area, pick_result

DATA_DIR = ROOT / "data"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Tarik insights iklan Meta")
    p.add_argument("--days", type=int, default=7, help="Bilangan hari ke belakang (default 7)")
    p.add_argument("--since", help="Tarikh mula YYYY-MM-DD (abaikan --days)")
    p.add_argument("--until", help="Tarikh akhir YYYY-MM-DD")
    p.add_argument(
        "--level",
        default="ad",
        choices=["ad", "adset", "campaign"],
        help="Tahap data (default: ad)",
    )
    p.add_argument("--quiet", action="store_true", help="Jangan cetak jadual")
    return p.parse_args()


def date_window(args: argparse.Namespace) -> tuple[str, str]:
    if args.since:
        until = args.until or date.today().isoformat()
        return args.since, until
    # Semalam sebagai hari terakhir: data hari ini belum lengkap
    until_d = date.today() - timedelta(days=1)
    since_d = until_d - timedelta(days=args.days - 1)
    return since_d.isoformat(), until_d.isoformat()


def enrich(rows: list, config: dict) -> list:
    """Tambah kawasan, bilangan hasil dan kos per hasil kepada setiap baris."""
    areas = config.get("areas", {})
    result_actions = config.get("result_actions", [])
    out = []

    for r in rows:
        name_blob = " ".join(
            [r.get("campaign_name", ""), r.get("adset_name", ""), r.get("ad_name", "")]
        )
        results, result_type = pick_result(r, result_actions)
        spend = f(r.get("spend"))
        out.append(
            {
                "campaign_name": r.get("campaign_name", ""),
                "adset_name": r.get("adset_name", ""),
                "ad_name": r.get("ad_name", ""),
                "campaign_id": r.get("campaign_id", ""),
                "adset_id": r.get("adset_id", ""),
                "ad_id": r.get("ad_id", ""),
                "kawasan": match_area(name_blob, areas),
                "spend": round(spend, 2),
                "impressions": int(f(r.get("impressions"))),
                "clicks": int(f(r.get("clicks"))),
                "ctr": round(f(r.get("ctr")), 2),
                "cpm": round(f(r.get("cpm")), 2),
                "reach": int(f(r.get("reach"))),
                "hasil": results,
                "jenis_hasil": result_type,
                "kos_per_hasil": round(spend / results, 2) if results else None,
            }
        )
    return out


def summarise_by_area(rows: list) -> list:
    buckets: dict[str, dict] = {}
    for r in rows:
        b = buckets.setdefault(
            r["kawasan"],
            {"kawasan": r["kawasan"], "spend": 0.0, "hasil": 0.0, "impressions": 0, "clicks": 0, "bil_iklan": 0},
        )
        b["spend"] += r["spend"]
        b["hasil"] += r["hasil"]
        b["impressions"] += r["impressions"]
        b["clicks"] += r["clicks"]
        b["bil_iklan"] += 1

    out = []
    for b in buckets.values():
        b["spend"] = round(b["spend"], 2)
        b["kos_per_hasil"] = round(b["spend"] / b["hasil"], 2) if b["hasil"] else None
        b["ctr"] = round(b["clicks"] / b["impressions"] * 100, 2) if b["impressions"] else 0.0
        out.append(b)
    # Yang paling banyak belanja di atas
    return sorted(out, key=lambda x: -x["spend"])


def write_csv(rows: list, path: Path) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def table(rows: list, columns: list, limit: int | None = None) -> str:
    """Cetak jadual teks ringkas."""
    if not rows:
        return "  (tiada data)"
    data = rows[:limit] if limit else rows
    widths = {}
    for key, label, kind in columns:
        width = len(label)
        for r in data:
            width = max(width, len(fmt_cell(r.get(key), kind)))
        widths[key] = width

    header = "  " + "  ".join(label.ljust(widths[key]) for key, label, _ in columns)
    sep = "  " + "  ".join("-" * widths[key] for key, _, _ in columns)
    lines = [header, sep]
    for r in data:
        lines.append(
            "  " + "  ".join(fmt_cell(r.get(key), kind).ljust(widths[key]) for key, _, kind in columns)
        )
    return "\n".join(lines)


def fmt_cell(value, kind: str) -> str:
    if value is None or value == "":
        return "-"
    if kind == "money":
        return f"{float(value):,.2f}"
    if kind == "pct":
        return f"{float(value):.2f}%"
    if kind == "int":
        return f"{int(float(value)):,}"
    text = str(value)
    return text if len(text) <= 34 else text[:31] + "..."


def main() -> None:
    args = parse_args()
    env = load_env()
    config = load_config()
    api = MetaAds(env)

    since, until = date_window(args)
    print(f"\nMenarik insights: level={args.level}, {since} hingga {until}")

    raw = api.insights(level=args.level, since=since, until=until)
    rows = enrich(raw, config)
    rows.sort(key=lambda r: (r["kos_per_hasil"] is None, r["kos_per_hasil"] or 0))

    if not rows:
        print("\n  Tiada data untuk tempoh ini. Mungkin tiada iklan aktif, atau akaun baru.")
        print("  Cuba tempoh lebih panjang: python pull_insights.py --days 30\n")
        return

    by_area = summarise_by_area(rows)
    total_spend = round(sum(r["spend"] for r in rows), 2)
    total_results = sum(r["hasil"] for r in rows)

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = DATA_DIR / f"insights_{args.level}_{since}_{until}.csv"
    write_csv(rows, csv_path)

    payload = {
        "dijana_pada": date.today().isoformat(),
        "tempoh": {"since": since, "until": until, "hari": args.days},
        "level": args.level,
        "mata_wang": config.get("currency", "RM"),
        "max_cpl": config.get("max_cpl"),
        "jumlah": {
            "spend": total_spend,
            "hasil": total_results,
            "kos_per_hasil": round(total_spend / total_results, 2) if total_results else None,
            "impressions": sum(r["impressions"] for r in rows),
            "clicks": sum(r["clicks"] for r in rows),
        },
        "ikut_kawasan": by_area,
        "baris": rows,
    }
    (DATA_DIR / "latest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    if not args.quiet:
        cur = config.get("currency", "RM")
        max_cpl = config.get("max_cpl")

        print(f"\n  JUMLAH: {cur} {total_spend:,.2f} spend | {total_results:,.0f} hasil", end="")
        if total_results:
            print(f" | {cur} {total_spend / total_results:,.2f} per hasil")
        else:
            print()

        print("\n  IKUT KAWASAN")
        print(
            table(
                by_area,
                [
                    ("kawasan", "Kawasan", "text"),
                    ("spend", f"Spend ({cur})", "money"),
                    ("hasil", "Hasil", "int"),
                    ("kos_per_hasil", f"{cur}/hasil", "money"),
                    ("ctr", "CTR", "pct"),
                    ("bil_iklan", "Bil. iklan", "int"),
                ],
            )
        )

        name_key = {"ad": "ad_name", "adset": "adset_name", "campaign": "campaign_name"}[args.level]
        with_results = [r for r in rows if r["kos_per_hasil"] is not None]
        no_results = [r for r in rows if r["kos_per_hasil"] is None and r["spend"] > 0]

        cols = [
            (name_key, "Nama", "text"),
            ("kawasan", "Kawasan", "text"),
            ("spend", f"Spend ({cur})", "money"),
            ("ctr", "CTR", "pct"),
            ("hasil", "Hasil", "int"),
            ("kos_per_hasil", f"{cur}/hasil", "money"),
        ]

        print("\n  5 TERBAIK (kos per hasil paling rendah)")
        print(table(with_results, cols, limit=5))

        print("\n  5 PALING MAHAL")
        print(table(sorted(with_results, key=lambda r: -(r["kos_per_hasil"] or 0)), cols, limit=5))

        if no_results:
            print("\n  BELANJA TAPI TIADA HASIL (perlu disemak)")
            print(table(sorted(no_results, key=lambda r: -r["spend"]), cols, limit=5))

        if max_cpl:
            over = [r for r in with_results if (r["kos_per_hasil"] or 0) > max_cpl]
            print(f"\n  {len(over)} dari {len(with_results)} melebihi max CPL {cur} {max_cpl}")

    print(f"\n  Disimpan: {csv_path.relative_to(ROOT)}")
    print(f"  Disimpan: {(DATA_DIR / 'latest.json').relative_to(ROOT)}")
    print("\n  Langkah seterusnya: python build_dashboard.py\n")


if __name__ == "__main__":
    main()
