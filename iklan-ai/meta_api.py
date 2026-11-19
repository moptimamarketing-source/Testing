"""
Klien ringkas untuk Meta Marketing API.

Modul ini dikongsi oleh semua skrip lain. Ia:
  - baca kredential dari fail .env (tiada dependency tambahan)
  - hantar permintaan GET/POST dengan retry bila kena rate limit
  - terjemah kod ralat Meta ke bahasa manusia
  - PASTIKAN token tidak pernah dicetak ke terminal atau log

Jangan tulis token terus dalam fail ini. Semua nilai datang dari .env.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:  # pragma: no cover
    sys.exit("Pakej 'requests' belum dipasang. Jalankan: pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent

# Kod ralat rate limit dari Meta (Bab 10 ebook)
RATE_LIMIT_CODES = {4, 17, 32, 613, 80000, 80001, 80002, 80003, 80004}

# Terjemahan kod ralat biasa -> langkah pembetulan
ERROR_HINTS = {
    190: (
        "Token tidak sah, sudah tamat atau sudah di-revoke.\n"
        "   -> Generate token baru (Bab 5 ebook) dan kemas kini META_ACCESS_TOKEN dalam .env"
    ),
    200: (
        "Tiada kebenaran untuk aset ini.\n"
        "   -> Semak System User sudah di-assign akaun iklan + Page (Bab 4)\n"
        "   -> Semak permission ads_read / ads_management di-tick masa generate token (Bab 5)"
    ),
    10: (
        "Permission tidak mencukupi.\n"
        "   -> Sama seperti di atas: semak Bab 4 dan senarai permission Bab 5"
    ),
    100: (
        "Parameter tidak sah.\n"
        "   -> Semak META_AD_ACCOUNT_ID bermula dengan 'act_'\n"
        "   -> Semak nama field / tarikh yang dihantar"
    ),
    2635: (
        "Versi API atau endpoint sudah lapuk.\n"
        "   -> Naikkan META_API_VERSION dalam .env ke versi yang lebih baharu"
    ),
    294: (
        "Perlu pengesahan pengiklan (advertiser verification).\n"
        "   -> Lengkapkan verification di Business Settings"
    ),
}


def die(msg: str) -> None:
    """Berhenti dengan mesej ralat yang jelas."""
    print(f"\n[RALAT] {msg}\n", file=sys.stderr)
    sys.exit(1)


def load_env(path: Path | None = None) -> dict:
    """Baca fail .env tanpa dependency luar. Format: KUNCI=nilai, satu per baris."""
    path = Path(path) if path else ROOT / ".env"
    if not path.exists():
        die(
            f"Fail .env tidak dijumpai di {path}\n"
            "        Salin .env.example kepada .env, kemudian isi nilainya sendiri.\n"
            "        Jangan minta AI tampal token untuk anda."
        )
    env: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip().strip('"').strip("'")
    return env


def load_config(path: Path | None = None) -> dict:
    """Baca config.json (pemetaan kawasan, jenis hasil, max CPL)."""
    path = Path(path) if path else ROOT / "config.json"
    if not path.exists():
        die(f"Fail config.json tidak dijumpai di {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"config.json tidak sah (JSON rosak): {exc}")
    return {}


class MetaAds:
    """Pembalut tipis di atas Graph API."""

    def __init__(self, env: dict | None = None):
        env = env or load_env()
        self.token = env.get("META_ACCESS_TOKEN", "").strip()
        self.account_id = env.get("META_AD_ACCOUNT_ID", "").strip()
        self.page_id = env.get("META_PAGE_ID", "").strip()
        self.version = env.get("META_API_VERSION", "v23.0").strip() or "v23.0"

        # Mod proxy: token disuntik oleh proxy (cth. sesi Claude Code Cloud).
        # Dalam mod ini kita TIDAK hantar access_token sendiri.
        self.proxy_auth = env.get("META_AUTH_MODE", "").strip().lower() == "proxy"
        if self.proxy_auth:
            self.token = ""
        if not self.token and not self.proxy_auth:
            die("META_ACCESS_TOKEN masih kosong dalam .env. Isi token anda sendiri (Bab 6C).")
        if not self.account_id:
            die("META_AD_ACCOUNT_ID masih kosong dalam .env.")
        if not self.account_id.startswith("act_"):
            die(
                f"META_AD_ACCOUNT_ID mesti bermula dengan 'act_' (anda isi: {self.account_id}).\n"
                "        Contoh betul: act_1234567890"
            )

        self.base = f"https://graph.facebook.com/{self.version}"

    # ---------- keselamatan ----------

    def scrub(self, text: str) -> str:
        """Buang token dari sebarang teks sebelum dipaparkan."""
        if self.token and self.token in text:
            text = text.replace(self.token, "<TOKEN DISEMBUNYIKAN>")
        return text

    # ---------- permintaan ----------

    def get(self, path: str, params: dict | None = None, _try: int = 0) -> dict:
        params = dict(params or {})
        url = f"{self.base}/{path.lstrip('/')}"
        send = dict(params)
        if self.token:
            send["access_token"] = self.token

        try:
            resp = requests.get(url, params=send, timeout=90)
        except requests.RequestException as exc:
            die(self.scrub(f"Gagal sambung ke Meta: {exc}"))

        if resp.status_code == 200:
            return resp.json()

        error = {}
        try:
            error = resp.json().get("error", {}) or {}
        except ValueError:
            pass

        code = error.get("code")
        if code in RATE_LIMIT_CODES and _try < 3:
            wait = 90 * (_try + 1)
            print(f"  [rate limit] Meta minta kita perlahan. Tunggu {wait}s, kemudian cuba lagi...")
            time.sleep(wait)
            return self.get(path, params, _try + 1)

        message = self.scrub(error.get("message", resp.text[:400]))
        hint = ERROR_HINTS.get(code, "")
        detail = f"Meta menolak permintaan (HTTP {resp.status_code}, code {code}).\n        {message}"
        if hint:
            detail += f"\n\n   Maksudnya: {hint}"
        die(detail)
        return {}

    def get_all(self, path: str, params: dict | None = None, max_pages: int = 50) -> list:
        """Ikut paging sampai habis. Pulangkan senarai rekod."""
        rows: list = []
        page = self.get(path, params)
        pages = 1
        while True:
            rows.extend(page.get("data", []))
            nxt = (page.get("paging") or {}).get("next")
            if not nxt or pages >= max_pages:
                break
            try:
                resp = requests.get(nxt, timeout=90)
            except requests.RequestException:
                break
            if resp.status_code != 200:
                break
            page = resp.json()
            pages += 1
        return rows

    # ---------- endpoint khusus ----------

    def account(self) -> dict:
        return self.get(
            self.account_id,
            {"fields": "name,currency,account_status,timezone_name,spend_cap,amount_spent"},
        )

    def insights(
        self,
        level: str = "ad",
        since: str | None = None,
        until: str | None = None,
        date_preset: str | None = None,
        extra_fields: str = "",
    ) -> list:
        """Tarik insights. Beri since+until ATAU date_preset."""
        fields = [
            "campaign_name",
            "adset_name",
            "ad_name",
            "campaign_id",
            "adset_id",
            "ad_id",
            "spend",
            "impressions",
            "clicks",
            "ctr",
            "cpm",
            "reach",
            "actions",
            "cost_per_action_type",
        ]
        if extra_fields:
            fields.append(extra_fields)

        params: dict = {
            "level": level,
            "fields": ",".join(fields),
            "limit": 500,
        }
        if date_preset:
            params["date_preset"] = date_preset
        else:
            params["time_range"] = json.dumps({"since": since, "until": until})

        return self.get_all(f"{self.account_id}/insights", params)


# ---------- pembantu umum ----------

ACCOUNT_STATUS = {
    1: "ACTIVE",
    2: "DISABLED",
    3: "UNSETTLED",
    7: "PENDING_RISK_REVIEW",
    8: "PENDING_SETTLEMENT",
    9: "IN_GRACE_PERIOD",
    100: "PENDING_CLOSURE",
    101: "CLOSED",
    201: "ANY_ACTIVE",
    202: "ANY_CLOSED",
}


def match_area(text: str, areas: dict) -> str:
    """Padankan nama campaign/ad set kepada kawasan dalam config.json."""
    low = (text or "").lower()
    for area, keywords in areas.items():
        for kw in keywords:
            if kw.lower() in low:
                return area
    return "Lain-lain"


def pick_result(row: dict, result_actions: list) -> tuple[float, str]:
    """
    Ambil bilangan hasil dari senarai 'actions'.
    Ikut keutamaan dalam config.json: jenis pertama yang ada, itu yang diguna.
    Pulangkan (bilangan, jenis_yang_diguna).
    """
    actions = {a.get("action_type"): a.get("value") for a in (row.get("actions") or [])}
    for wanted in result_actions:
        if wanted in actions:
            try:
                return float(actions[wanted]), wanted
            except (TypeError, ValueError):
                return 0.0, wanted
    return 0.0, ""


def f(value, default: float = 0.0) -> float:
    """Tukar ke float dengan selamat."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
