#!/usr/bin/env python3
"""Validate annotation quality — BIOES consistency, entity distribution.

Extended by P2_02:
  * Walks data/annotations/drafts/ in addition to legacy train/val/test.
  * Tolerates both 'ner_tags' and 'labels' keys.
  * Strict tokens/tags length equality check.
  * Strict schema-tag whitelist (config.constants.BIOES_LABELS).
  * Stricter BIOES: catches I-/E- without preceding B-/I-; dangling E- followed by I-;
    and unknown tag formats.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from config.constants import BIOES_LABELS  # noqa: E402


def load_annotations(path):
    with open(path) as f:
        return json.load(f)


def _iter_sentence_records(node) -> list[dict]:
    """Normalize a loaded annotation blob into a list of sentence records.

    Accepts:
      - list[dict]  (legacy train.json/val.json/test.json shape)
      - {"sentences": [{"tokens", "ner_tags"|"labels", ...}, ...]}  (factory shape)
    """
    if isinstance(node, list):
        return [d for d in node if isinstance(d, dict)]
    if isinstance(node, dict):
        sents = node.get("sentences")
        if isinstance(sents, list):
            return [d for d in sents if isinstance(d, dict)]
    return []


def _tags_of(sent: dict) -> list[str] | None:
    if "ner_tags" in sent:
        return sent["ner_tags"]
    if "labels" in sent:
        return sent["labels"]
    return None


def validate_bioes(tags, sample_id):
    """Strict BIOES check.

    Rules:
    - All tags must be in config.constants.BIOES_LABELS.
    - I-X or E-X must be preceded (at some contiguous run) by B-X.
    - E-X must not be followed by I- (entity must terminate at E-).
    - B-X must NOT be immediately followed by E-Y (Y != X) — type mismatch.
    - B-X must be followed by I-X, E-X, B-X (same type new entity), O, or end-of-sentence.
    """
    errors: list[str] = []
    valid = set(BIOES_LABELS)
    for i, tag in enumerate(tags):
        if tag not in valid:
            errors.append(f"Sample {sample_id}: tag at pos {i} not in BIOES_LABELS: {tag!r}")
            continue
        if not (tag.startswith("I-") or tag.startswith("E-")):
            continue
        ent = tag[2:]
        prev = tags[i - 1] if i > 0 else None
        if prev is None or prev not in (f"B-{ent}", f"I-{ent}"):
            errors.append(f"Sample {sample_id}: {tag} at pos {i} without preceding B-{ent} or I-{ent} (got {prev!r})")
        nxt = tags[i + 1] if i + 1 < len(tags) else None
        if tag.startswith("E-") and nxt is not None and nxt.startswith("I-"):
            errors.append(f"Sample {sample_id}: E-{ent} at pos {i} followed by I- (entity run continues past E-)")
    return errors


def count_entity_types(data) -> dict:
    counts = defaultdict(int)
    for item in data:
        for tag in _tags_of(item) or []:
            if tag == "O":
                continue
            if tag.startswith("B-") or tag.startswith("S-"):
                counts[tag[2:]] += 1
    return counts


def _collect_token_tag_errors(sent: dict, sample_id: str) -> list[str]:
    out: list[str] = []
    tokens = sent.get("tokens")
    tags = _tags_of(sent)
    if tokens is None or tags is None:
        out.append(f"{sample_id}: missing tokens or ner_tags/labels")
    elif not isinstance(tokens, list) or not isinstance(tags, list):
        out.append(f"{sample_id}: tokens/ner_tags must be lists")
    elif len(tokens) != len(tags):
        out.append(f"{sample_id}: tokens/tags length mismatch ({len(tokens)} vs {len(tags)})")
    return out


def _scan_legacy_split_files(base: Path) -> tuple[int, list[str]]:
    n = 0
    errs: list[str] = []
    for name in ("train", "val", "test"):
        path = base / f"{name}.json"
        if not path.exists():
            continue
        data = load_annotations(path)
        sents = _iter_sentence_records(data)
        for idx, sent in enumerate(sents):
            sid = f"{name}_{idx}"
            errs.extend(_collect_token_tag_errors(sent, sid))
            tags = _tags_of(sent)
            if tags is not None and len(tags) == len(sent.get("tokens", [])):
                errs.extend(validate_bioes(tags, sid))
            n += 1
    return n, errs


def _scan_drafts_dir(drafts_dir: Path) -> tuple[int, list[str]]:
    n = 0
    errs: list[str] = []
    if not drafts_dir.exists():
        return n, errs
    for f in sorted(drafts_dir.glob("*.draft.json")):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as exc:
            errs.append(f"{f.name}: json decode: {exc}")
            continue
        sents = _iter_sentence_records(data)
        for idx, sent in enumerate(sents):
            sid = f"{f.name}::sent{idx}"
            errs.extend(_collect_token_tag_errors(sent, sid))
            tags = _tags_of(sent)
            if tags is not None and len(tags) == len(sent.get("tokens", [])):
                errs.extend(validate_bioes(tags, sid))
            n += 1
    return n, errs


def main():
    base = Path("data/annotations")
    drafts_dir = base / "drafts"

    print("=== ANNOTATION QUALITY REPORT ===\n")

    all_errors: list[str] = []
    n_legacy, legacy_errs = _scan_legacy_split_files(base)
    n_drafts, draft_errs = _scan_drafts_dir(drafts_dir)
    all_errors.extend(legacy_errs)
    all_errors.extend(draft_errs)

    print(f"Legacy train/val/test sentences: {n_legacy}")
    print(f"Factory draft sentences         : {n_drafts}")
    print(f"Total sentences scanned         : {n_legacy + n_drafts}\n")

    print("--- BIOES Consistency ---")
    if all_errors:
        print(f"ERRORS FOUND: {len(all_errors)}")
        for err in all_errors[:10]:
            print(f"  {err}")
        if len(all_errors) > 10:
            print(f"  ... and {len(all_errors) - 10} more")
    else:
        print("All BIOES tags valid (and tokens/tags aligned)")

    print("\n--- Entity Distribution (factory drafts) ---")
    entity_types = ["MATERIAL", "QUANTITY", "UNIT", "LOCATION", "DIMENSION", "STANDARD", "ACTION", "GRADE"]
    dataset_counts: dict[str, dict[str, int]] = {}
    if drafts_dir.exists():
        for f in sorted(drafts_dir.glob("*.draft.json")):
            try:
                data = json.loads(f.read_text())
            except json.JSONDecodeError:
                continue
            for sent in _iter_sentence_records(data):
                for et, c in count_entity_types([sent]).items():
                    dataset_counts.setdefault("drafts", defaultdict(int))[et] += c

    header = f"{'Entity':<10} {'Drafts':>8}"
    print(header)
    print("-" * len(header))
    for et in entity_types:
        c = dataset_counts.get("drafts", {}).get(et, 0) if dataset_counts else 0
        print(f"{et:<10} {c:>8}")
    total_all = sum(sum(c.values()) for c in dataset_counts.values())
    print("-" * len(header))
    print(f"{'TOTAL':<10} {total_all:>8}")

    print("\n--- Tag Format Check (legacy) ---")
    all_tags = set()
    for name in ("train", "val", "test"):
        p = base / f"{name}.json"
        if not p.exists():
            continue
        for sent in _iter_sentence_records(load_annotations(p)):
            tags = _tags_of(sent)
            if tags:
                all_tags.update(tags)
    valid = set(BIOES_LABELS)
    bad_tags = [t for t in all_tags if t not in valid]
    if bad_tags:
        print(f"Invalid tag formats found (in legacy): {bad_tags}")
    else:
        print("All legacy tags use valid BIOES format from config.constants.BIOES_LABELS")

    print("\n=== END REPORT ===")
    return 0 if not all_errors else 1


if __name__ == "__main__":
    sys.exit(main())
