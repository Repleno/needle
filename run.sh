#!/bin/bash
# Runs needle once per day. If the script succeeds, later cron slots are skipped.
# Set up cron at 10:00, 13:00, 16:00 CET (= 09:00, 12:00, 15:00 UTC).

MARKER="/tmp/needle-success-$(date +%Y-%m-%d)"
LOG_DIR="$(dirname "$0")"

if [ -f "$MARKER" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') already ran successfully today — skipping" >> "$LOG_DIR/run.log"
    exit 0
fi

cd "$LOG_DIR" || exit 1

# Load secrets from .env.local and export them to child processes
if [ -f .env.local ]; then
    set -a
    # shellcheck source=.env.local
    source .env.local
    set +a
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') starting" >> run.log

if python3 reddit_scout.py >> run.log 2>&1; then
    touch "$MARKER"
    echo "$(date '+%Y-%m-%d %H:%M:%S') success" >> run.log
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') failed — will retry at next slot" >> run.log
    exit 1
fi
