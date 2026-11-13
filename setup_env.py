"""Cipta fail .env di komputer anda. Token ditaip tersembunyi (tidak dipaparkan)."""
import getpass, os, re, sys

if os.path.exists(".env"):
    if input(".env sudah wujud. Tulis ganti? (y/N): ").strip().lower() != "y":
        sys.exit("Dibatalkan.")

token = getpass.getpass("Tampal META_ACCESS_TOKEN (tak akan dipaparkan): ").strip().strip('"\'')
if len(token) < 20 or " " in token:
    sys.exit("Token nampak tak betul. Cuba lagi.")

acct = input("META_AD_ACCOUNT_IDS (contoh act_1234567890, akaun 02 sahaja): ").strip()
if not re.fullmatch(r"act_\d+(,\s*act_\d+)*", acct):
    sys.exit("Format mesti act_ diikuti nombor.")

page = input("META_PAGE_ID: ").strip()
if not page.isdigit():
    sys.exit("META_PAGE_ID mesti nombor.")

with open(".env", "w", encoding="utf-8") as f:
    f.write("# Meta Marketing API - JANGAN kongsi fail ini\n")
    f.write(f"META_ACCESS_TOKEN={token}\n")
    f.write(f"META_AD_ACCOUNT_IDS={acct}\n")
    f.write(f"META_PAGE_ID={page}\n")
    f.write("META_API_VERSION=v23.0\n")
print(".env dicipta. Jalankan: python meta_test.py")
