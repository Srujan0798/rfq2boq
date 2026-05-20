# TASK: P3T5 — Demo Video — Owner

**Phase:** 3 | **Effort:** 1 day | **Priority:** P2 (final deliverable)

## 1. GOAL
Record a 3–5 minute screencast showing one PDF → BOQ → Excel flow end-to-end, demonstrating real-world usability. This is the artifact shown to the company.

## 2. CONTEXT
Read first:
- `ui/app.py` — polished UI from P3T2
- `data/samples/sample_rfq_simple.pdf` — sample input
- `data/samples/sample_boq_output.xlsx` — expected output from P3T3
- [docs/HYBRID_PLAN.md](../../../docs/HYBRID_PLAN.md)
- [docs/HYBRID_EXECUTION_PLAN.md](../../../docs/HYBRID_EXECUTION_PLAN.md)

## 3. DELIVERABLES
- [ ] `deliverables/demo/demo_video.mp4` — 3–5 min recording
- [ ] `deliverables/demo/script.md` — narration script
- [ ] `deliverables/demo/screenshots/` — 5–10 stills from the video
- [ ] `README.md` — link to demo video at the top
- [ ] `deliverables/demo/transcript.txt` — text transcript (for accessibility)

## 4. STEPS
1. Read context. Review the polished UI + Excel output.
2. **Write the script** `deliverables/demo/script.md`:
   - 0:00–0:30 Problem: manual BOQ extraction is slow and error-prone
   - 0:30–1:00 Show RFQ2BOQ landing page, explain in one line
   - 1:00–2:00 Upload a real RFQ PDF (from `data/real_rfqs/raw/`), show progress, then results
   - 2:00–3:00 Review the BOQ table, point out: descriptions, quantities, units, standards, grades. Show confidence indicators.
   - 3:00–3:30 Edit one row to show interactivity. Download Excel.
   - 3:30–4:00 Open the Excel, show CPWD-format output with DSR codes, totals, GST.
   - 4:00–4:30 Quick summary: how long this would take manually vs. with RFQ2BOQ.
3. **Set up screen recording**:
   - macOS: QuickTime → File → New Screen Recording → record with audio
   - Or: OBS Studio (free)
4. **Run the flow**:
   - Start: `make serve-ui`
   - Hit http://localhost:8501
   - Use the script as a guide; do 2–3 takes if needed
5. **Post-production** (light):
   - Trim dead time at the start/end
   - Optional: add a title card with project name + date
   - Export as MP4, 1080p, ≤100MB
6. **Save artifacts**:
   - `deliverables/demo/demo_video.mp4`
   - Take 5–10 screenshots during the recording, save to `deliverables/demo/screenshots/`
7. **Transcript**:
   - Manual transcript OR auto-generate via Whisper (model already in deps): `python3 -c "import whisper; m = whisper.load_model('base'); print(m.transcribe('deliverables/demo/demo_video.mp4')['text'])"`
   - Save to `deliverables/demo/transcript.txt`
8. **Update README**:
   - Top of README: link to the video file path
   - If hosting later (YouTube/Vimeo): replace with URL

## 5. VERIFICATION
```bash
# Video exists and is reasonable size/duration
$ ls -lh deliverables/demo/demo_video.mp4
EXPECT: 10MB–100MB

# Duration check (requires ffprobe)
$ ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 deliverables/demo/demo_video.mp4 2>/dev/null
EXPECT: 180–300 (3–5 minutes)

# Script and transcript exist
$ test -f deliverables/demo/script.md && test -f deliverables/demo/transcript.txt
EXPECT: exit 0

# Screenshots
$ ls deliverables/demo/screenshots/*.png 2>/dev/null | wc -l
EXPECT: ≥5

# README links to video
$ grep -i "demo" README.md
EXPECT: at least one mention
```

## 6. ACCEPTANCE CRITERIA
- [ ] Video plays end-to-end (no broken frames)
- [ ] Duration 3–5 min
- [ ] Audio audible (or clearly captioned/transcript)
- [ ] Shows: upload → extract → table → download → open Excel
- [ ] README references the video

## 7. CONSTRAINTS
- DO NOT show any real PII (bidder names, contact info) — use sample PDFs only
- File size ≤ 100MB (can be larger if hosted externally and only the URL is in repo)
- Audio in English (Hindi optional secondary)
- No sales-y / hyperbolic language; just demonstrate functionality
- Keep simple: no fancy animations or transitions

## 8. DEPENDENCIES
- **Blocked by:** P3T2 (polished UI), P3T3 (CPWD Excel)
- **Blocks:** None (final task)
- **Parallel-safe with:** None (final step)

## 9. GOTCHAS
- Screen recording on macOS captures the mouse cursor by default — fine
- If demo PDF is real (from `data/real_rfqs/raw/`): pick one without personal contact info
- Microphone audio can pick up background noise — record in a quiet room
- Video files don't belong in `git` if >50MB — use Git LFS or external hosting and put the link in README
- Whisper transcription is fine for accessibility but may miss technical terms
- See [docs/WAVE_GOTCHAS.md](../../../docs/WAVE_GOTCHAS.md)

## End-of-task

When done, this completes the entire hybrid plan. Update:
- `docs/HYBRID_EXECUTION_PLAN.md` — mark P3T5 DONE
- `docs/wave_status.md` — Phase 3 COMPLETE
- `README.md` — final metrics + demo link
- Tag the git commit: `git tag v1.0-handover`
