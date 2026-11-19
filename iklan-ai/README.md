# Iklan AI — starter kit Meta Marketing API

Tarik data iklan Meta → fail CSV/JSON → dashboard HTML yang boleh dikongsi.
Dibina untuk digunakan bersama Claude Code, berdasarkan ebook *Sambung Meta API ke AI*
oleh Rahim Ibrahim.

---

## Apa yang anda perlu buat dahulu (ikut ebook)

Starter kit ni **bermula dari Bab 6**. Sebelum jalankan apa-apa di sini, siapkan Bab 2–5:

| Bab | Langkah | Tanda dah betul |
|---|---|---|
| 2 | Buat Meta App, pautkan ke Business Portfolio yang betul | Di bawah nama App tertulis `Business: [nama anda]` |
| 3A | Cipta System User, role **Admin** | Muncul dalam Users → System users |
| 3B | **Assign System User ke App** (Manage app / Full access) | Tab *Installed apps* System User ada App anda |
| 4 | Assign aset: akaun iklan + Page (Full control) | Tab *Assigned assets* ada kedua-duanya |
| 5 | Generate token, expiry **Never** | Token dicopy (dipaparkan sekali sahaja) |

Permission yang perlu di-tick: `ads_management`, `ads_read`, `business_management`,
`pages_show_list`, `pages_read_engagement`, `pages_manage_ads`.

> Bab 3B paling senang terlepas. Kalau App anda tak keluar dalam dropdown masa nak
> generate token, itu puncanya.

---

## Pasang (5 minit)

```bash
# 1. Letak folder ni sebagai folder projek anda, kemudian buka dengan Claude Code
cd iklan-ai
claude

# 2. Pasang dependency (satu sahaja: requests)
pip install -r requirements.txt

# 3. Sediakan .env
cp .env.example .env        # Windows: copy .env.example .env
```

**Isi `.env` sendiri** — buka dengan Notepad, TextEdit atau VS Code. Jangan minta AI
tampal token untuk anda, dan jangan tampal token dalam chat.

| Kunci | Isi dengan |
|---|---|
| `META_ACCESS_TOKEN` | Token dari Bab 5 |
| `META_AD_ACCOUNT_ID` | ID akaun iklan **dengan `act_` di depan**, cth `act_1234567890` |
| `META_PAGE_ID` | ID Facebook Page (pilihan untuk report, perlu untuk cipta iklan) |

> Fail bermula dengan titik tersembunyi secara default.
> Mac: `Cmd + Shift + .` dalam Finder. Windows: View → Show → Hidden items.

---

## Guna

```bash
python test_connection.py              # 1. Uji token & akses
python pull_insights.py --days 7       # 2. Tarik data
python build_dashboard.py              # 3. Bina dashboard.html
```

`test_connection.py` sepatutnya paparkan nama akaun iklan anda yang betul, mata wang,
status dan spend 7 hari. Kalau ini berjaya, semua setup Bab 2–5 anda betul.

### Pilihan `pull_insights.py`

```bash
python pull_insights.py --days 30          # 30 hari
python pull_insights.py --level adset      # level ad set (atau campaign)
python pull_insights.py --since 2026-11-01 --until 2026-11-15
```

Output:
- `data/insights_<level>_<since>_<until>.csv` — buka dalam Excel atau import ke Google Sheet
- `data/latest.json` — sumber untuk dashboard

Hari ini tidak dimasukkan secara default (data hari semasa belum lengkap), jadi
tempoh berakhir semalam.

---

## Sesuaikan `config.json`

Fail ni selamat untuk di-commit — tiada token di dalamnya.

**`areas`** — padanan nama campaign kepada kawasan. Skrip cari kata kunci ni dalam nama
campaign, ad set dan ad. Pecahan ikut kawasan ni yang menjawab soalan *kawasan mana
patut dapat lebih bajet*. Tambah kawasan baru bila buka cawangan baru.

**`result_actions`** — jenis hasil, ikut keutamaan. Skrip ambil jenis pertama yang
dijumpai dalam setiap baris:

| Jenis iklan | Guna |
|---|---|
| Click-to-WhatsApp | `onsite_conversion.messaging_conversation_started_7d` |
| Lead form / WhatsForm | `onsite_conversion.lead_grouped` atau `lead` |
| Trafik ke website | `link_click` |

Kalau lajur *Hasil* keluar 0 padahal anda tahu ada lead masuk, jenis hasil dalam
`config.json` tidak padan dengan objektif kempen anda. Minta Claude Code:
*"Senaraikan semua action_type yang ada dalam data/latest.json"*, kemudian letak yang
betul di tempat pertama.

**`max_cpl`** — max cost per lead anda. Dashboard tandakan apa yang melebihi.

---

## Dashboard yang update sendiri

`build_dashboard.py` hasilkan satu fail HTML standalone — tiada internet diperlukan,
boleh dibuka terus atau diletak di mana-mana static hosting untuk dikongsi dengan team.

Untuk buat ia "live", jalankan ikut jadual. `run_daily.sh` dah disediakan:

```bash
chmod +x run_daily.sh
crontab -e
# 0 7 * * * cd /laluan/penuh/ke/iklan-ai && ./run_daily.sh >> data/cron.log 2>&1
```

Windows: guna Task Scheduler.

Sekali sehari sudah cukup. Meta insights sendiri lag beberapa jam, dan tarik terlalu
kerap akan kena rate limit.

---

## Nota penting tentang nombor

Meta hanya tahu **chat dan klik**. Ia tidak tahu berapa pelajar yang akhirnya mendaftar.
Kos per lead RM10 tidak bermakna apa-apa kalau lead tu tak jadi pelajar.

Cadangan: simpan satu Google Sheet dengan lajur *pendaftaran ikut kawasan ikut minggu*
yang anda isi sendiri dari rekod cawangan. Kemudian kos per pendaftaran boleh dikira
dan itu nombor yang sepatutnya memandu keputusan bajet. Fasa seterusnya kit ni.

---

## Bila ada masalah

| Gejala | Punca & pembetulan |
|---|---|
| `Fail .env tidak dijumpai` | Belum `cp .env.example .env` |
| Code 190 / Invalid OAuth token | Token salah/tamat/di-revoke → generate baru (Bab 5), kemas kini `.env` |
| Code 200 atau 10 / permission | Aset belum di-assign (Bab 4) atau permission tak di-tick (Bab 5) |
| Code 100 / Invalid parameter | `META_AD_ACCOUNT_ID` tiada `act_` di depan |
| Code 17 / 80004 / too many calls | Rate limit. Skrip akan tunggu dan cuba lagi secara automatik |
| App tak keluar masa generate token | Ulang Bab 3B |
| Tiada data walaupun ada iklan | Cuba `--days 30`. Akaun baru perlu 5–7 hari data |

Skrip ni terjemah kod ralat Meta ke langkah pembetulan secara automatik. Kalau jumpa
ralat baru, tampal **mesej ralat (bukan token)** kepada Claude Code dan tanya langkah
mana yang tertinggal.

---

## Had & amaran

- API tetap ikut polisi Meta. Iklan yang melanggar polisi tetap ditolak.
- Letak **Account spending limit** di peringkat akaun iklan sebagai jaring keselamatan.
- Kit ni **baca sahaja**. Tiada fungsi cipta atau ubah kempen. Bila anda tambah fungsi
  tulis nanti, peraturan dalam `CLAUDE.md` terpakai: semua dicipta **PAUSED**.
- Satu token, satu projek. Jangan guna token sama di banyak tempat.
- Kalau rasa token bocor: System users → Revoke tokens → generate baru.
