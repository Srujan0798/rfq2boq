#!/bin/bash
# Wrapper to run the UI drop-in driver in the background.
# Usage: ./run_dropin.sh [single|combo|all]
set -uo pipefail
cd /Users/srujansai/rfq2boq-phase9
export PYTHONPATH=/Users/srujansai/rfq2boq-phase9
export RFQ2BOQ_OCR_CONFIDENCE_THRESHOLD=0.0
LOG_FILE="results/ui_dropin/_scratch/driver_$(date +%Y%m%d_%H%M%S).log"
mkdir -p results/ui_dropin/_scratch
echo "Logging to $LOG_FILE"
PYTHONUNBUFFERED=1 python3.12 -u -m tests.e2e.test_ui_corpus_dropin "$@" > "$LOG_FILE" 2>&1 &
PID=$!
echo "Driver PID: $PID"
echo "$PID" > results/ui_dropin/_scratch/driver.pid
disown
echo "Driver launched in background."
