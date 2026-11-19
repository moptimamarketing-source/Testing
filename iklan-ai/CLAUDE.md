# Peraturan projek: Iklan Meta

Projek ni sambung ke Meta Marketing API untuk tarik data iklan dan (nanti) cipta kempen.

## Keselamatan token

- Token ada dalam `.env`. **Jangan baca, cetak, paparkan atau ulang isi `.env`** dalam chat,
  dalam log, atau dalam komen kod.
- Kalau saya tersilap tampal token dalam chat, beritahu saya supaya revoke dan generate baru.
  Jangan guna token dari chat.
- Semua kredential baru (Google service account, Airtable, ClickUp) masuk `.env` dan
  masuk `.gitignore`. Jangan sekali-kali hardcode dalam fail `.py`.

## Peraturan operasi

- **SEMUA campaign, ad set dan ad yang dicipta mesti status PAUSED.** Tiada pengecualian.
  Saya semak dalam Ads Manager dulu, baru aktifkan sendiri.
- Jangan ubah bajet, pause, atau padam apa-apa tanpa approval saya secara eksplisit.
- Sebelum buat apa-apa perubahan tulis (write), tunjuk ringkasan dulu: apa akan berubah,
  dari nilai apa ke nilai apa, dan berapa banyak objek terlibat. Tunggu saya kata "ya".
- Kalau saya minta banyak perubahan serentak, ingatkan saya: approve satu sahaja setiap
  minggu, supaya kita tahu mana yang beri kesan.
- Guna versi API dari `META_API_VERSION` dalam `.env`. Jangan hardcode versi.
- Jangan ubah ad set yang berumur kurang 3 hari. Ia masih dalam fasa pembelajaran.

## Konteks bisnes

- Minda Optima - kelas membaca kanak-kanak (program fizikal di cawangan + online).
- Iklan dipecahkan ikut kawasan. Nama campaign mengandungi nama kawasan.
  Pemetaan kawasan ada dalam `config.json`.
- Hasil utama = lead WhatsApp / WhatsForm, bukan jualan. Lihat nota di bawah.
- Max CPL rujukan ada dalam `config.json` (`max_cpl`).

## Cara report

- Report dan penjelasan dalam **Bahasa Melayu**, mata wang **RM**.
- Guna jadual bila banding lebih dari 2 item.
- Sebut nombor, bukan adjektif. "CTR 2.8% berbanding purata akaun 1.4%", bukan "prestasi bagus".
- **Jangan samakan lead dengan pendaftaran.** Meta hanya tahu chat dan klik. Bila menilai
  iklan, sebut jelas yang kita ukur kos per lead, dan ingatkan saya isi data pendaftaran
  sebenar kalau saya nak kos per pendaftaran.
- Akaun atau iklan baru: jangan beri kesimpulan sebelum 5-7 hari data.

## Struktur projek

```
meta_api.py          klien API + pemetaan ralat (jangan ubah tanpa sebab)
test_connection.py   uji token & akses
pull_insights.py     tarik data -> data/*.csv + data/latest.json
build_dashboard.py   data/latest.json -> dashboard.html
config.json          kawasan, jenis hasil, max CPL (selamat di-commit)
.env                 token (JANGAN commit, JANGAN paparkan)
data/                output - tidak di-commit
```

## Bila ada ralat

Terjemahan kod ralat Meta ada dalam `ERROR_HINTS` di `meta_api.py`. Kalau jumpa kod baru,
tambah ke situ dengan langkah pembetulan, supaya kali seterusnya lebih senang.
