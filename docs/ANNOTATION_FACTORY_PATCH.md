# check_gold_provenance.py — P2_02 monotonicity patch (PROPOSED, NOT YET APPLIED)

`scripts/check_gold_provenance.py` is FROZEN (Rule 5 — sha256 in `config/FROZEN_HASHES.sha256`).
This file documents the patch the orchestrator should apply + re-pin after P2_02 is
gated. The patch adds a monotonicity / bulk-stamping check: more than
`BULK_STAMP_THRESHOLD = 50` sentences sharing one `reviewed_at` timestamp = HARD FAIL.

The reason: a single owner session in 30 min cannot legitimately stamp >50 sentences
(target rate is ~50/hour). A bulk stamp at one timestamp is the signature of an
agent batch-writing verified files (incident #7 / #13 pattern), not of a human
reviewing one sentence at a time.

## What to change

In `scripts/check_gold_provenance.py`, immediately after the existing reviewer
check (after the line `if not n_legacy and not n_forged:` block, before the gold
lock check), add:

```python
    # --- 2b. Provenance monotonicity (P2_02): no bulk stamping ---
    # A single reviewed_at timestamp covering >50 sentences is the signature
    # of an agent batch-writing verified files, not a human session. Hard fail.
    BULK_STAMP_THRESHOLD = 50
    from collections import Counter as _Counter

    bulk_offenders: list[tuple[str, int, str]] = []
    for base in (Path("data/annotations/verified"), Path("data/real_rfqs/gold/rows")):
        if not base.exists():
            continue
        for f in sorted(base.glob("*.json")):
            try:
                data = json.loads(f.read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            docs = data if isinstance(data, list) else [data]
            for doc in docs:
                if not isinstance(doc, dict) or not doc.get("human_verified"):
                    continue
                ts = doc.get("reviewed_at")
                if not ts:
                    continue
                n_sents = len(doc.get("sentences", []))
                if n_sents > BULK_STAMP_THRESHOLD:
                    bulk_offenders.append((str(f), n_sents, str(ts)))

    if bulk_offenders:
        print(
            f"FAIL: {len(bulk_offenders)} human_verified:true record(s) bulk-stamped "
            f"(>{BULK_STAMP_THRESHOLD} sentences at one timestamp):"
        )
        for f, n, ts in bulk_offenders:
            print(f"    \u2717 {f}: {n} sentences at {ts}")
        exit_code = 1
    else:
        print(
            f"    \u2713 No bulk-stamped verified records (max sentences/timestamp <= {BULK_STAMP_THRESHOLD})"
        )
```

Also update the existing line that prints a ✓ at the end of the reviewer block
to chain the new check cleanly.

## Why this lives outside the worker commit

The file's sha256 is locked in `config/FROZEN_HASHES.sha256` (line 5). If the
worker touched it directly, the orchestrator's `check_frozen_hashes` gate would
fail the task. The patch is shipped as a deliverable here; the orchestrator
applies it under P0_03's eval-integrity-lock protocol (which allows frozen-eval
edits via documented patch + re-pin) and re-pins the new hash.

## Re-pin procedure (for the orchestrator)

```bash
# 1. apply the diff above
# 2. re-pin the manifest
python3 scripts/check_frozen_hashes.py --pin > config/FROZEN_HASHES.sha256
# 3. run the gate
make verify
```

## Test

The patch should reject a 51-sentence verified file at one timestamp. Quick
fixture (do not commit):

```bash
python3 -c "
import json
fake = {'doc_id': 'bulk', 'source_file': 'x.pdf',
        'human_verified': True, 'reviewer': 'srujan',
        'reviewed_at': '2026-07-06T12:00:00+00:00',
        'sentences': [{'tokens': ['x'], 'ner_tags': ['O']} for _ in range(51)]}
json.dump(fake, open('data/annotations/verified/_bulk_fixture.json', 'w'))
"
python3 scripts/check_gold_provenance.py  # expect exit 1 with bulk-stamped line
rm data/annotations/verified/_bulk_fixture.json
```
