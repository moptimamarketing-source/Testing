#!/usr/bin/env bash
# Jalankan ikut jadual supaya dashboard sentiasa terkini.
#
# Cara pasang (Linux/Mac) - setiap hari 7:00 pagi:
#   chmod +x run_daily.sh
#   crontab -e
#   0 7 * * * cd /laluan/penuh/ke/iklan-ai && ./run_daily.sh >> data/cron.log 2>&1
#
# Windows: guna Task Scheduler, arahkan ke python.exe dengan argumen pull_insights.py

set -euo pipefail
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ==="
"$PYTHON" pull_insights.py --days 7 --quiet
"$PYTHON" build_dashboard.py
echo "Siap."
