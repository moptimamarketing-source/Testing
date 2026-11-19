#!/usr/bin/env python3
"""
Langkah 3: bina dashboard HTML dari data/latest.json.

Jalankan:  python build_dashboard.py

Output: dashboard.html - satu fail standalone, tiada internet diperlukan.
Buka terus dalam browser, atau upload ke mana-mana static hosting untuk
dikongsi dengan team.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

from meta_api import ROOT

DATA = ROOT / "data" / "latest.json"
OUT = ROOT / "dashboard.html"

# Palet: slot biru (kategorikal 1) - satu siri sahaja, jadi tiada legend.
TEMPLATE = """<!DOCTYPE html>
<html lang="ms">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root {
    color-scheme: light;
    --plane:          #f9f9f7;
    --surface-1:      #fcfcfb;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --text-muted:     #898781;
    --grid:           #e1e0d9;
    --baseline:       #c3c2b7;
    --border:         rgba(11,11,11,0.10);
    --series-1:       #2a78d6;
    --status-warning: #fab219;
    --status-critical:#d03b3b;
    --good:           #006300;
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --plane:          #0d0d0d;
      --surface-1:      #1a1a19;
      --text-primary:   #f0efec;
      --text-secondary: #c3c2b7;
      --text-muted:     #898781;
      --grid:           #2c2c2a;
      --baseline:       #383835;
      --border:         rgba(255,255,255,0.10);
      --series-1:       #3987e5;
      --good:           #0ca30c;
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --plane:          #0d0d0d;
    --surface-1:      #1a1a19;
    --text-primary:   #f0efec;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --grid:           #2c2c2a;
    --baseline:       #383835;
    --border:         rgba(255,255,255,0.10);
    --series-1:       #3987e5;
    --good:           #0ca30c;
  }

  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 28px 20px 56px;
    background: var(--plane); color: var(--text-primary);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    font-size: 14px; line-height: 1.5;
  }
  .wrap { max-width: 1040px; margin: 0 auto; }
  header { display: flex; align-items: baseline; gap: 16px; flex-wrap: wrap; margin-bottom: 4px; }
  h1 { font-size: 19px; font-weight: 600; margin: 0; letter-spacing: -0.01em; }
  .meta { color: var(--text-muted); font-size: 13px; }
  button.theme {
    margin-left: auto; background: var(--surface-1); color: var(--text-secondary);
    border: 1px solid var(--border); border-radius: 7px; padding: 6px 11px;
    font: inherit; font-size: 13px; cursor: pointer;
  }
  button.theme:hover { color: var(--text-primary); }

  section {
    background: var(--surface-1); border: 1px solid var(--border);
    border-radius: 10px; padding: 20px; margin-top: 18px;
  }
  h2 { font-size: 14px; font-weight: 600; margin: 0 0 2px; }
  .sub { color: var(--text-muted); font-size: 13px; margin: 0 0 18px; }

  /* ---- KPI ---- */
  .kpis { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 20px 28px; }
  .kpi .label { color: var(--text-secondary); font-size: 13px; }
  .kpi .value { font-size: 27px; font-weight: 600; letter-spacing: -0.02em; margin-top: 2px; }
  .kpi.hero .value { font-size: 48px; line-height: 1.05; }
  .kpi .note { color: var(--text-muted); font-size: 12px; margin-top: 2px; }
  .kpi .note.over { color: var(--status-critical); }
  .kpi .note.under { color: var(--good); }

  /* ---- bar ---- */
  .chart { position: relative; }
  .row { display: grid; grid-template-columns: 150px 1fr; gap: 14px; align-items: center; padding: 7px 0; }
  .row .name { color: var(--text-secondary); font-size: 13px; text-align: right;
               overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .track { position: relative; height: 24px; display: flex; align-items: center; }
  .bar {
    height: 20px; background: var(--series-1);
    border-radius: 0 4px 4px 0; min-width: 2px;
  }
  .bar.none { background: var(--grid); }
  .tip-at { font-variant-numeric: tabular-nums; font-size: 13px; color: var(--text-primary);
            padding-left: 9px; white-space: nowrap; }
  .axis { border-top: 1px solid var(--baseline); margin-left: 164px; margin-top: 6px;
          display: flex; justify-content: space-between; }
  .axis span { color: var(--text-muted); font-size: 12px; font-variant-numeric: tabular-nums;
               padding-top: 5px; }
  .refline { position: absolute; top: 0; bottom: 26px; width: 1px; background: var(--status-critical);
             opacity: 0.55; }
  .reflabel { position: absolute; bottom: 0; font-size: 12px; color: var(--status-critical);
              white-space: nowrap; transform: translateX(-50%); }

  /* ---- jadual ---- */
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { text-align: left; padding: 8px 10px 8px 0; border-bottom: 1px solid var(--grid); }
  th { color: var(--text-muted); font-weight: 500; font-size: 12px; text-transform: uppercase;
       letter-spacing: 0.04em; }
  td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; padding-right: 0; }
  td:last-child, th:last-child { padding-left: 14px; }
  td.name { max-width: 300px; }
  .flag { color: var(--status-critical); font-size: 12px; white-space: nowrap; }
  .ok { color: var(--text-muted); font-size: 12px; }
  details summary { cursor: pointer; color: var(--text-secondary); font-size: 13px; }

  .tooltip {
    position: fixed; pointer-events: none; opacity: 0; transition: opacity .1s;
    background: var(--surface-1); color: var(--text-primary);
    border: 1px solid var(--border); border-radius: 7px; padding: 8px 11px;
    font-size: 13px; box-shadow: 0 4px 14px rgba(0,0,0,.14); z-index: 10;
    font-variant-numeric: tabular-nums;
  }
  footer { color: var(--text-muted); font-size: 12px; margin-top: 18px; }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>__TITLE__</h1>
    <span class="meta">__PERIOD__</span>
    <button class="theme" id="themeBtn" type="button">Mod gelap</button>
  </header>

  <section>
    <h2>Ringkasan tempoh</h2>
    <p class="sub">Semua nilai dari Meta Marketing API. Pendaftaran sebenar perlu diisi sendiri.</p>
    <div class="kpis">__KPIS__</div>
  </section>

  <section>
    <h2>Kos per hasil ikut kawasan</h2>
    <p class="sub">__CHART_SUB__</p>
    <div class="chart">__BARS__</div>
  </section>

  <section>
    <h2>Butiran</h2>
    <p class="sub">Disusun dari kos per hasil paling rendah.</p>
    __TABLE__
  </section>

  <footer>Dijana __GENERATED__ oleh pull_insights.py + build_dashboard.py &middot; data/latest.json</footer>
</div>
<div class="tooltip" id="tip"></div>
<script>
(function () {
  var btn = document.getElementById('themeBtn');
  function current() {
    var set = document.documentElement.getAttribute('data-theme');
    if (set) return set;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  function paint() { btn.textContent = current() === 'dark' ? 'Mod cerah' : 'Mod gelap'; }
  btn.addEventListener('click', function () {
    document.documentElement.setAttribute('data-theme', current() === 'dark' ? 'light' : 'dark');
    paint();
  });
  paint();

  var tip = document.getElementById('tip');
  document.querySelectorAll('[data-tip]').forEach(function (el) {
    el.addEventListener('mousemove', function (e) {
      tip.innerHTML = el.getAttribute('data-tip');
      tip.style.opacity = '1';
      var x = Math.min(e.clientX + 14, window.innerWidth - tip.offsetWidth - 10);
      tip.style.left = x + 'px';
      tip.style.top = (e.clientY + 16) + 'px';
    });
    el.addEventListener('mouseleave', function () { tip.style.opacity = '0'; });
  });
})();
</script>
</body>
</html>
"""


def esc(value) -> str:
    return html.escape(str(value if value is not None else ""), quote=True)


def money(value, cur: str = "RM") -> str:
    if value is None:
        return "-"
    return f"{cur} {float(value):,.2f}"


def num(value) -> str:
    if value is None:
        return "-"
    return f"{float(value):,.0f}"


def kpi(label: str, value: str, note: str = "", note_class: str = "", hero: bool = False) -> str:
    cls = "kpi hero" if hero else "kpi"
    note_html = f'<div class="note {note_class}">{esc(note)}</div>' if note else ""
    return (
        f'<div class="{cls}"><div class="label">{esc(label)}</div>'
        f'<div class="value">{value}</div>{note_html}</div>'
    )


def build_bars(areas: list, cur: str, max_cpl) -> tuple[str, str]:
    """Bar melintang: kos per hasil ikut kawasan. Satu siri, jadi tiada legend."""
    priced = [a for a in areas if a.get("kos_per_hasil") is not None]
    if not priced:
        return ("<p class=\"sub\">Tiada hasil direkod dalam tempoh ini, jadi kos per hasil tidak dapat dikira.</p>", "")

    values = [a["kos_per_hasil"] for a in priced]
    data_top = max(values)
    # Tunjuk garis max CPL hanya kalau ia dekat dengan data. Kalau jauh di atas,
    # bar akan jadi terlalu pendek untuk dibanding.
    show_ref = bool(max_cpl) and max_cpl <= data_top * 1.5
    scale = max((max_cpl if show_ref else data_top) * 1.15, 1)

    rows = []
    for a in sorted(priced, key=lambda x: x["kos_per_hasil"]):
        cpl = a["kos_per_hasil"]
        width = max(cpl / scale * 100, 0.6)
        tip = (
            f"<strong>{esc(a['kawasan'])}</strong><br>"
            f"Spend: {money(a['spend'], cur)}<br>"
            f"Hasil: {num(a['hasil'])}<br>"
            f"Kos per hasil: {money(cpl, cur)}<br>"
            f"CTR: {a.get('ctr', 0):.2f}% &middot; {num(a.get('bil_iklan'))} iklan"
        )
        rows.append(
            f'<div class="row" data-tip="{esc(tip)}">'
            f'<div class="name">{esc(a["kawasan"])}</div>'
            f'<div class="track"><div class="bar" style="width:{width:.1f}%"></div>'
            f'<span class="tip-at">{money(cpl, cur)}</span></div></div>'
        )

    # Garis rujukan max CPL
    ref = ""
    if show_ref:
        pos = max_cpl / scale * 100
        ref = (
            f'<div class="refline" style="left:calc(164px + (100% - 164px) * {pos / 100:.4f})"></div>'
            f'<div class="reflabel" style="left:calc(164px + (100% - 164px) * {pos / 100:.4f})">'
            f"max {money(max_cpl, cur)}</div>"
        )

    axis = (
        f'<div class="axis"><span>0</span><span>{cur} {scale:,.0f}</span></div>'
        '<div style="height:20px"></div>'
    )
    if show_ref:
        sub = f"Garis merah = max CPL anda ({money(max_cpl, cur)})."
    elif max_cpl:
        sub = f"Semua kawasan jauh di bawah max CPL anda ({money(max_cpl, cur)})."
    else:
        sub = "Satu bar = satu kawasan."
    return ("".join(rows) + axis + ref, sub)


def build_table(rows: list, level: str, cur: str, max_cpl) -> str:
    name_key = {"ad": "ad_name", "adset": "adset_name", "campaign": "campaign_name"}.get(level, "ad_name")
    head = (
        "<tr><th>Nama</th><th>Kawasan</th>"
        f'<th class="num">Spend ({cur})</th><th class="num">CTR</th>'
        f'<th class="num">Hasil</th><th class="num">{cur}/hasil</th><th></th></tr>'
    )
    body = []
    for r in rows:
        cpl = r.get("kos_per_hasil")
        if cpl is None:
            flag = '<span class="flag">&#9888; Tiada hasil</span>' if r.get("spend", 0) > 0 else ""
        elif max_cpl and cpl > max_cpl:
            flag = '<span class="flag">&#9888; Melebihi CPL</span>'
        else:
            flag = '<span class="ok">OK</span>'
        body.append(
            "<tr>"
            f'<td class="name">{esc(r.get(name_key))}</td>'
            f"<td>{esc(r.get('kawasan'))}</td>"
            f'<td class="num">{float(r.get("spend", 0)):,.2f}</td>'
            f'<td class="num">{float(r.get("ctr", 0)):.2f}%</td>'
            f'<td class="num">{num(r.get("hasil"))}</td>'
            f'<td class="num">{(f"{cpl:,.2f}" if cpl is not None else "-")}</td>'
            f"<td>{flag}</td>"
            "</tr>"
        )
    return f"<table><thead>{head}</thead><tbody>{''.join(body)}</tbody></table>"


def main() -> None:
    if not DATA.exists():
        raise SystemExit(
            f"\n[RALAT] {DATA} tidak dijumpai.\n"
            "        Jalankan dahulu: python pull_insights.py\n"
        )

    payload = json.loads(DATA.read_text(encoding="utf-8"))
    cur = payload.get("mata_wang", "RM")
    max_cpl = payload.get("max_cpl")
    totals = payload.get("jumlah", {})
    period = payload.get("tempoh", {})
    areas = payload.get("ikut_kawasan", [])
    rows = payload.get("baris", [])

    cpl = totals.get("kos_per_hasil")
    note, note_class = "", ""
    if cpl is not None and max_cpl:
        gap = cpl - max_cpl
        if gap > 0:
            note, note_class = f"{money(gap, cur)} di atas max CPL {money(max_cpl, cur)}", "over"
        else:
            note, note_class = f"{money(-gap, cur)} di bawah max CPL {money(max_cpl, cur)}", "under"

    kpis = "".join(
        [
            kpi("Kos per hasil (keseluruhan)", money(cpl, cur) if cpl is not None else "-", note, note_class, hero=True),
            kpi("Jumlah spend", money(totals.get("spend"), cur)),
            kpi("Jumlah hasil", num(totals.get("hasil")), f"dari {len(rows)} {payload.get('level', 'ad')}"),
            kpi("Klik", num(totals.get("clicks")), f"{num(totals.get('impressions'))} impressions"),
        ]
    )

    bars, chart_sub = build_bars(areas, cur, max_cpl)
    table = build_table(rows, payload.get("level", "ad"), cur, max_cpl)

    period_text = f"{period.get('since', '?')} hingga {period.get('until', '?')} &middot; level {payload.get('level', 'ad')}"

    out = (
        TEMPLATE.replace("__TITLE__", "Dashboard Iklan Meta")
        .replace("__PERIOD__", period_text)
        .replace("__KPIS__", kpis)
        .replace("__BARS__", bars)
        .replace("__CHART_SUB__", chart_sub)
        .replace("__TABLE__", table)
        .replace("__GENERATED__", esc(payload.get("dijana_pada", "")))
    )
    OUT.write_text(out, encoding="utf-8")
    print(f"\n  Dashboard siap: {OUT}")
    print("  Buka fail ni dalam browser. Jalankan semula selepas setiap pull_insights.py\n")


if __name__ == "__main__":
    main()
