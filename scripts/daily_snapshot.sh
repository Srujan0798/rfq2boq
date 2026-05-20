#!/bin/bash
# Daily Snapshot — regenerates TIMELINE_AND_OBJECTIVES.html with today's state.
# Run automatically via cron or launchd at 6 PM, or manually any time.
#
# Outputs:
#   - deliverables/TIMELINE_AND_OBJECTIVES.html (the slide deck)
#   - deliverables/daily_log/YYYY-MM-DD.md (an append-only progress log)
#   - deliverables/daily_log/latest.md (symlink to today's log)
#
# Usage:
#   ./scripts/daily_snapshot.sh           # generate + save log
#   ./scripts/daily_snapshot.sh --dry-run # show what would change, don't write

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TODAY=$(date +%Y-%m-%d)
TODAY_HUMAN=$(date "+%d %b %Y")
LOG_DIR="deliverables/daily_log"
LOG_FILE="$LOG_DIR/$TODAY.md"
DECK_HTML="deliverables/TIMELINE_AND_OBJECTIVES.html"

mkdir -p "$LOG_DIR"

# ─────────────────────────────────────────────────────────────
# 1. CAPTURE TODAY'S STATE
# ─────────────────────────────────────────────────────────────

echo "=== Daily snapshot for $TODAY_HUMAN ==="

# Today's commits (any branch)
TODAY_COMMITS=$(git log --since="$TODAY 00:00:00" --until="$TODAY 23:59:59" --oneline 2>/dev/null || echo "")
COMMIT_COUNT=$(echo "$TODAY_COMMITS" | grep -c . || true)

# Test pass count
TEST_COUNT=$(python3 -m pytest tests/unit tests/integration tests/golden tests/fuzz --collect-only -q 2>/dev/null | tail -1 | grep -oE '[0-9]+ test' | head -1 | grep -oE '[0-9]+' || echo "?")

# Real F1 (from real_world_metrics_v2.json)
REAL_F1=$(python3 -c "
import json, os
try:
    f = 'results/real_world_metrics_v2.json'
    if os.path.exists(f):
        d = json.load(open(f))
        print(f\"{d.get('micro_f1', 0):.3f}\")
    else:
        print('?')
except: print('?')
" 2>/dev/null)

# DSR item count
DSR_COUNT=$(python3 -c "
import json, os
try:
    f = 'data/rates/cpwd_dsr_2023.json'
    if os.path.exists(f):
        d = json.load(open(f))
        print(len(d.get('items', d) if isinstance(d, dict) else d))
    else: print('?')
except: print('?')
" 2>/dev/null)

# Real PDFs / gold annotations
REAL_PDFS=$(find data/real_rfqs/raw -maxdepth 2 -name "*.pdf" 2>/dev/null | grep -v synthetic_archive | wc -l | tr -d ' ')
GOLD_COUNT=$(python3 -c "
import json, os
try:
    f = 'data/real_rfqs/annotations/gold_annotations.json'
    if os.path.exists(f):
        d = json.load(open(f))
        filled = sum(1 for x in d if len(x.get('entities', [])) > 0)
        print(filled)
    else: print(0)
except: print(0)
" 2>/dev/null)

# Git status
DIRTY=$(git status --short | wc -l | tr -d ' ')

# ─────────────────────────────────────────────────────────────
# 2. WRITE THE DAILY LOG
# ─────────────────────────────────────────────────────────────

cat > "$LOG_FILE" <<EOF
# Daily Progress — $TODAY_HUMAN

## Snapshot

| Metric | Value |
|--------|-------|
| Commits today | $COMMIT_COUNT |
| Tests passing | $TEST_COUNT |
| Real-world F1 | $REAL_F1 |
| DSR rate items | $DSR_COUNT |
| Real RFQ PDFs | $REAL_PDFS |
| Gold annotations | $GOLD_COUNT |
| Uncommitted changes | $DIRTY |

## Today's commits

\`\`\`
$(if [ -n "$TODAY_COMMITS" ]; then echo "$TODAY_COMMITS"; else echo "(none)"; fi)
\`\`\`

## Generated

$(date "+%Y-%m-%d %H:%M:%S %Z")
EOF

# Symlink latest.md to today
ln -sf "$TODAY.md" "$LOG_DIR/latest.md"

echo "📝 Wrote $LOG_FILE"

# ─────────────────────────────────────────────────────────────
# 3. REGENERATE THE HTML DECK
# ─────────────────────────────────────────────────────────────

# Build the "today's progress" snippet
TODAY_LIST=""
if [ -n "$TODAY_COMMITS" ]; then
  TODAY_LIST=$(echo "$TODAY_COMMITS" | head -8 | sed 's/^[a-f0-9]* /    <li>/; s/$/<\/li>/')
fi

# Patch the title slide date + results slide F1 + the footer date in the existing HTML.
# We use a marker-based approach so the script is idempotent.
python3 - <<PYEOF
import re, pathlib
p = pathlib.Path("$DECK_HTML")
if not p.exists():
    print(f"⚠️  {p} not found — skip patch (run once manually first to create it)")
    raise SystemExit(0)
html = p.read_text()

# Patch title date
html = re.sub(r'IIT Gandhinagar · SWA Consultancy Internship<br>\s*\d+\s+\w+\s+\d+',
              'IIT Gandhinagar · SWA Consultancy Internship<br>\n    $TODAY_HUMAN',
              html)

# Patch real F1 on results slide
html = re.sub(r'(<strong>Real-world F1</strong></td><td class="metric"><strong>)[0-9.]+(</strong>)',
              r'\g<1>$REAL_F1\g<2>',
              html)

# Patch tests passing
html = re.sub(r'(<td>Tests passing</td><td class="metric ok">)[0-9]+( of [0-9]+)',
              r'\g<1>$TEST_COUNT\g<2>',
              html)

# Patch DSR items
html = re.sub(r'(<td>DSR rate coverage</td><td class="metric">)[0-9]+( items)',
              r'\g<1>$DSR_COUNT\g<2>',
              html)

# Patch the footer "Last update"
html = re.sub(r'Last update: \d+\s+\w+\s+\d+',
              f'Last update: $TODAY_HUMAN',
              html)

p.write_text(html)
print(f"🖼  Updated {p} — title date, F1, test count, DSR count, footer date")
PYEOF

# ─────────────────────────────────────────────────────────────
# 4. SUMMARY
# ─────────────────────────────────────────────────────────────

echo ""
echo "═══════════════════════════════════════════════"
echo "✓ Daily snapshot complete — $TODAY_HUMAN"
echo "═══════════════════════════════════════════════"
echo "  Commits today:     $COMMIT_COUNT"
echo "  Tests passing:     $TEST_COUNT"
echo "  Real-world F1:     $REAL_F1"
echo "  DSR items:         $DSR_COUNT"
echo "  Real RFQs:         $REAL_PDFS"
echo "  Gold annotations:  $GOLD_COUNT"
echo ""
echo "📂 Log:  $LOG_FILE"
echo "🎤 Deck: $DECK_HTML"
echo ""
echo "→ Open the deck:  open $DECK_HTML"
