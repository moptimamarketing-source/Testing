#!/usr/bin/env python3
"""
Langkah 1: uji sambungan.

Jalankan:  python test_connection.py

Kalau ini berjaya, token, akaun iklan dan permission anda semua betul.
Tiada token akan dipaparkan.
"""

from meta_api import ACCOUNT_STATUS, MetaAds, f, load_env


def main() -> None:
    env = load_env()
    api = MetaAds(env)

    print("\nMenguji sambungan ke Meta Marketing API...")
    print(f"  Versi API      : {api.version}")
    print(f"  Akaun iklan    : {api.account_id[:8]}***  (disembunyikan sebahagian)")

    acc = api.account()
    status_code = acc.get("account_status")
    status = ACCOUNT_STATUS.get(status_code, f"UNKNOWN ({status_code})")

    print("\n  SAMBUNGAN BERJAYA\n")
    print(f"  Nama akaun     : {acc.get('name', '-')}")
    print(f"  Status         : {status}")
    print(f"  Mata wang      : {acc.get('currency', '-')}")
    print(f"  Zon waktu      : {acc.get('timezone_name', '-')}")

    # Spend 7 hari lepas
    rows = api.insights(level="account", date_preset="last_7d")
    spend = sum(f(r.get("spend")) for r in rows)
    print(f"  Spend 7 hari   : {acc.get('currency', 'RM')} {spend:,.2f}")

    # Semak Page ID kalau diisi
    if api.page_id:
        try:
            page = api.get(api.page_id, {"fields": "name"})
            print(f"  Page           : {page.get('name', '-')}")
        except SystemExit:
            print("  Page           : tidak dapat dibaca (semak pages_show_list + Bab 4)")
            raise

    print("\n  Langkah seterusnya: python pull_insights.py --days 7\n")


if __name__ == "__main__":
    main()
