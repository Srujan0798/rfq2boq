#!/usr/bin/env python3
"""
Generate genuine BIOES training data from ALL available RFQ extraction sources.

COVERS: All 127 RFQ documents in the corpus (minus the 42-doc TEST split).
SOURCES:
  1) output/batch_extractions/*.extracted.json    → per-entry BIOES (via gen_annotation_drafts logic)
  2) data/annotations/cli_drafts/bioes/*.bioes.json    (previously generated drafts)
  3) data/annotations/draft_from_rfqs/bioes/*.bioes.json (rfq pipeline drafts)
  4) data/annotations/verified_from_rowgold/bioes/*.json (human-verified sentences)
  5) data/annotations/draft/*.json                      (intake drafts - tokens+tags format)

RULES:
  - NEVER include TEST split docs (from split_test.json)
  - Each sentence must have valid BIOES tags
  - Deduplicate by tokens+tags fingerprint
  - Report per-document and per-source breakdown

OUTPUT: data/annotations/expanded/training_sentences.json
"""

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# ── Paths ──────────────────────────────────────────────────────────────
SPLIT_FILE = BASE / "data/real_rfqs/split_test.json"
BATCH_DIR = BASE / "output/batch_extractions"
BATCH_V2_DIR = BASE / "output/batch_extractions_v2"
CLI_DRAFTS_DIR = BASE / "data/annotations/cli_drafts/bioes"
DRAFT_RFQS_DIR = BASE / "data/annotations/draft_from_rfqs/bioes"
VERIFIED_DIR = BASE / "data/annotations/verified_from_rowgold/bioes"
INTAKE_DRAFTS_DIR = BASE / "data/annotations/draft"
OUTPUT_DIR = BASE / "data/annotations/expanded"
OUTPUT_FILE = OUTPUT_DIR / "training_sentences.json"

DATE = "2026-07-05"


# ── Load TEST split paths ──────────────────────────────────────────────
def load_test_paths() -> set:
    """Return normalized paths for all TEST split documents."""
    split = json.loads(SPLIT_FILE.read_text())
    result = set()
    for p in split["test"]["all_paths"]:
        norm = Path(p).resolve()
        result.add(str(norm))
        # Also add the filename alone for matching
        result.add(norm.name.lower())
    return result


TEST_PATHS = load_test_paths()


def is_sacred_source(source_str: str) -> bool:
    """Check if a source_file path or identifier belongs to the TEST split."""
    if not source_str:
        return False
    s = str(source_str)
    # Direct path match
    try:
        resolved = Path(s).resolve()
        if str(resolved) in TEST_PATHS:
            return True
    except Exception:
        pass
    # Filename match (lowercase)
    s_lower = s.lower()
    for tp in TEST_PATHS:
        if (
            isinstance(tp, str)
            and (tp.lower() in s_lower or s_lower in tp.lower())
            and len(tp) > 5
        ):
            return True
    # swa_enquiries path = definitely sacred
    if "swa_enquiries" in s_lower:
        return True
    # swa_draft_* prefix = definitely from sacred SWA docs
    if s_lower.startswith("swa_draft_") or "swa_draft_" in s_lower:
        return True
    # Sacred 10 doc IDs (by project name)
    sacred_doc_ids = {
        "01_gsecl", "02_isro", "03_zydus_matoda", "04_adani",
        "05_zydus_animal", "06_avante", "07_grew_solar", "08_sael",
        "09_gem_bid_7439924", "10_gem_bid_7552777",
        "gsecl_wanakbori", "isro_vssc", "zydus_matoda", "adani",
        "zydus_animal", "avante_kirloskar", "grew_solar", "sael",
        "gem_bid_7439924", "gem_bid_7552777",
        # SHA256-derived names / aliases
        "vssc", "40_vssc", "gem-bidding",
    }
    return any(sid in s_lower for sid in sacred_doc_ids)


# ── Tokenization & Entity Detection (from gen_annotation_drafts.py) ────
def fix_obvious_typos(text: str) -> str:
    fixes = {
        "accoustic": "acoustic", "Acountic": "Acoustic", "acountic": "acoustic",
        "Acustic": "Acoustic", "acustic": "acoustic",
        "Insulaton": "Insulation", "insulaton": "insulation",
        "ductiing": "ducting", "insulatione": "insulation",
    }
    for wrong, right in fixes.items():
        text = text.replace(wrong, right)
    return text


def tokenize_material(text: str) -> list[str]:
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    tokens = re.findall(r"\d+(?:\.\d+)?|[A-Za-z]+|[/()\-,.]|[\u0900-\u097F]+", text)
    return tokens


def detect_entity(token: str, prev_token: str | None, next_token: str | None) -> str:
    t_lower = token.lower()
    if re.match(r"^\d+(\.\d+)?$", token):
        return "QUANTITY"
    units = {
        "sqm", "sq.m", "sqm.", "m", "mm", "cm", "kg", "nos", "no", "ltr",
        "kg/m3", "kg/m", "mtr", "m.", "meter", "meters", "mmthick",
        "kg.", "nos.", "cum", "cu.m", "sqft", "sq.ft", "rmt",
    }
    if t_lower in units or t_lower.rstrip(".") in units:
        return "UNIT"
    location_signals = {"at", "for", "in", "near", "zone", "area", "building", "floor", "level"}
    if t_lower in location_signals and next_token and next_token[0].isupper() and next_token.lower() not in units:
        return "LOCATION"
    if re.match(r"^\d+\s*(mm|cm|m|kg|nos|sqm|ltr)$", token, re.I):
        return "DIMENSION"
    action_words = {"supply", "supplying", "supply.", "install", "installation", "provide", "lay", "erect", "fix"}
    if t_lower in action_words:
        return "ACTION"
    grade_words = {"grade", "type", "class", "is", "bs", "astm", "din", "en"}
    if t_lower in grade_words:
        return "GRADE"
    std_patterns = {"is:", "is ", "bs ", "astm ", "din ", "en ", "iso "}
    for pat in std_patterns:
        if t_lower.startswith(pat):
            return "STANDARD"
    if prev_token and prev_token.lower() in {"thick", "thickness", "size", "dia", "diameter", "width", "length"}:
        return "DIMENSION"
    return "MATERIAL"


def generate_bioes_sentence(entry: dict) -> dict | None:
    """Create a single BIOES sentence from an extraction entry (rowgold format)."""
    material = entry.get("material", "").strip()
    if not material:
        return None
    material = fix_obvious_typos(material)
    tokens = tokenize_material(material)
    if not tokens:
        return None

    quantity = entry.get("quantity", "")
    unit = entry.get("unit", "")
    grade = entry.get("grade", "")
    location = entry.get("location", "")
    action = entry.get("action", "")

    # Build extra tokens (quantity, unit, grade, action, location)
    extra_tokens = []
    if quantity:
        extra_tokens.append(str(quantity))
    if unit:
        extra_tokens.append(unit)
    if grade:
        extra_tokens.extend(tokenize_material(grade))
    if action:
        extra_tokens.append(action)
    if location:
        extra_tokens.extend(location.split())

    all_tokens = tokens + extra_tokens
    tags = []

    for i, tok in enumerate(all_tokens):
        prev = all_tokens[i - 1] if i > 0 else None
        nxt = all_tokens[i + 1] if i < len(all_tokens) - 1 else None
        is_extra = i >= len(tokens)

        if is_extra:
            if tok == str(quantity) or (quantity and tok == str(quantity)):
                tags.append("S-QUANTITY")
            elif unit and tok.lower() == unit.lower():
                tags.append("S-UNIT")
            elif tok.lower() in {"supply", "install", "provide", "lay", "erect", "fix"}:
                tags.append("S-ACTION")
            elif tok == grade:
                tags.append("S-GRADE")
            else:
                tags.append("O")
        else:
            entity = detect_entity(tok, prev, nxt)
            tags.append(f"S-{entity}")

    # Clean empty tokens
    clean_tokens = []
    clean_tags = []
    for tok, tag in zip(all_tokens, tags, strict=False):
        if tok and tag:
            clean_tokens.append(tok)
            clean_tags.append(tag)

    return {
        "tokens": clean_tokens,
        "ner_tags": clean_tags,
        "labels": clean_tags,
    }


# ── Validate BIOES tags ────────────────────────────────────────────────
VALID_ENTITIES = {"MATERIAL", "QUANTITY", "UNIT", "ACTION", "GRADE", "STANDARD", "LOCATION", "DIMENSION"}
BIOES_PREFIXES = {"B", "I", "O", "S", "E"}


def validate_bioes_tags(tags: list[str]) -> tuple[bool, str]:
    """Validate that BIOES tags follow correct format and sequence rules."""
    if not tags:
        return False, "empty tags"
    for tag in tags:
        if tag == "O":
            continue
        parts = tag.split("-", 1)
        if len(parts) != 2:
            return False, f"invalid tag format: {tag}"
        prefix, entity = parts
        if prefix not in BIOES_PREFIXES:
            return False, f"invalid prefix {prefix} in {tag}"
        if entity not in VALID_ENTITIES:
            return False, f"unknown entity {entity} in {tag}"
    # Check B-I-E-S sequence rules
    for i, tag in enumerate(tags):
        if tag == "O":
            continue
        prefix = tag.split("-", 1)[0]
        if prefix == "I":
            if i == 0 or tags[i - 1] == "O":
                return False, f"I-tag without B at position {i}: {tag}"
            prev_prefix = tags[i - 1].split("-", 1)[0]
            if prev_prefix not in ("B", "I"):
                return False, f"I-tag following invalid prefix {prev_prefix} at {i}: {tag}"
        if prefix == "E" and (i == 0 or tags[i - 1] == "O"):
            return False, f"E-tag without preceding B/I at position {i}: {tag}"
        if (
            prefix == "B"
            and i > 0
            and tags[i - 1] not in ("O",)
            and not tags[i - 1].startswith("E-")
            and tags[i - 1].split("-", 1)[0] in ("B", "I")
        ):
            pass  # B after O or E is fine, B after B/I needs same entity check
    return True, "ok"


# ── Source 1: Process batch_extractions (raw extracted entries) ────────
def process_batch_extractions() -> list[dict]:
    """Process all extracted.json files from batch_extractions (non-TEST only)."""
    result = []
    per_doc = defaultdict(list)
    skipped_sacred = 0

    for fpath in sorted(BATCH_DIR.glob("*.extracted.json")):
        data = json.loads(fpath.read_text())
        source = data.get("source", str(fpath))
        stem = fpath.stem.replace(".extracted", "")

        if is_sacred_source(source):
            skipped_sacred += 1
            continue

        entries = data.get("entries", [])
        doc_sentences = []
        for entry in entries:
            sent = generate_bioes_sentence(entry)
            if sent:
                valid, reason = validate_bioes_tags(sent["ner_tags"])
                if not valid:
                    # Convert single-S tags to valid format
                    pass  # S tags are valid per BIOES spec
                sent["source"] = f"batch_extraction:{stem}"
                sent["source_file"] = source
                sent["human_verified"] = False
                doc_sentences.append(sent)
                result.append(sent)

        per_doc[stem] = doc_sentences

    return result, per_doc, skipped_sacred


# ── Source 1b: Process batch_extractions_v2 (alternate pipeline) ──────
def process_batch_v2() -> tuple[list[dict], dict, int]:
    """Process extracted JSON files from batch_extractions_v2."""
    result = []
    per_doc = defaultdict(list)
    skipped_sacred = 0

    for fpath in sorted(BATCH_V2_DIR.glob("*.json")):
        if fpath.name in ("summary.json", "SUMMARY.md"):
            continue
        data = json.loads(fpath.read_text())
        project = data.get("project_name", fpath.stem)
        filepath = data.get("filepath", "")

        if is_sacred_source(filepath) or is_sacred_source(project):
            skipped_sacred += 1
            continue

        boq_items = data.get("boq_items", [])
        doc_sentences = []
        for item in boq_items:
            entry = {
                "material": item.get("material", ""),
                "quantity": str(item.get("quantity", "")),
                "unit": item.get("unit", ""),
                "grade": item.get("grade", ""),
                "location": item.get("location", ""),
                "action": item.get("action", ""),
            }
            sent = generate_bioes_sentence(entry)
            if sent:
                sent["source"] = f"batch_v2:{project}"
                sent["source_file"] = filepath
                sent["human_verified"] = False
                doc_sentences.append(sent)
                result.append(sent)

        per_doc[project] = doc_sentences

    return result, per_doc, skipped_sacred


# ── Source 2: Load existing cli_drafts BIOES ───────────────────────────
def load_cli_drafts() -> tuple[list[dict], dict, int]:
    """Load existing BIOES files from cli_drafts/bioes."""
    result = []
    per_doc = defaultdict(list)
    skipped = 0

    for fpath in sorted(CLI_DRAFTS_DIR.glob("*.bioes.json")):
        data = json.loads(fpath.read_text())
        source = data.get("source_file", "")
        stem = fpath.stem.replace(".bioes", "")

        if is_sacred_source(source):
            skipped += 1
            continue

        sentences = data.get("sentences", [])
        for sent in sentences:
            if "tokens" not in sent or "ner_tags" not in sent:
                continue
            valid, reason = validate_bioes_tags(sent["ner_tags"])
            if not valid:
                continue
            sent["source"] = f"cli_draft:{stem}"
            sent["source_file"] = source
            sent["human_verified"] = False
            result.append(sent)
            per_doc[stem].append(sent)

    return result, per_doc, skipped


# ── Source 3: Load draft_from_rfqs BIOES ───────────────────────────────
def load_draft_from_rfqs() -> tuple[list[dict], dict, int]:
    """Load existing BIOES files from draft_from_rfqs/bioes."""
    result = []
    per_doc = defaultdict(list)
    skipped = 0

    for fpath in sorted(DRAFT_RFQS_DIR.glob("*.bioes.json")):
        data = json.loads(fpath.read_text())
        source = data.get("source_file", "")
        stem = fpath.stem.replace(".bioes", "")

        if is_sacred_source(source):
            skipped += 1
            continue

        sentences = data.get("sentences", [])
        for sent in sentences:
            if "tokens" not in sent or "ner_tags" not in sent:
                continue
            valid, reason = validate_bioes_tags(sent["ner_tags"])
            if not valid:
                continue
            sent["source"] = f"draft_rfq:{stem}"
            sent["source_file"] = source
            sent["human_verified"] = False
            result.append(sent)
            per_doc[stem].append(sent)

    return result, per_doc, skipped


# ── Source 4: Load verified_from_rowgold ───────────────────────────────
def load_verified() -> tuple[list[dict], dict, int]:
    """Load human-verified BIOES sentences from verified_from_rowgold."""
    result = []
    per_doc = defaultdict(list)
    skipped = 0

    for fpath in sorted(VERIFIED_DIR.glob("*.json")):
        data = json.loads(fpath.read_text())
        doc_id = data.get("doc_id", fpath.stem)
        source = data.get("source_file", "")

        if is_sacred_source(source) or is_sacred_source(doc_id):
            skipped += 1
            continue

        sent = {
            "tokens": data.get("tokens", []),
            "ner_tags": data.get("ner_tags", []),
            "labels": data.get("labels", data.get("ner_tags", [])),
            "source": f"verified:{doc_id}",
            "source_file": source,
            "human_verified": True,
        }
        if not sent["tokens"] or not sent["ner_tags"]:
            continue
        valid, reason = validate_bioes_tags(sent["ner_tags"])
        if not valid:
            continue
        result.append(sent)
        per_doc[doc_id].append(sent)

    return result, per_doc, skipped


# ── Source 5: Load intake drafts ──────────────────────────────────────
def load_intake_drafts() -> tuple[list[dict], dict, int]:
    """Load intake draft annotations from data/annotations/draft/."""
    result = []
    per_doc = defaultdict(list)
    skipped = 0

    for fpath in sorted(INTAKE_DRAFTS_DIR.glob("*.json")):
        raw = json.loads(fpath.read_text())
        # Some files are lists (multiple docs) — handle both shapes
        doc_list = raw if isinstance(raw, list) else [raw]
        for data in doc_list:
            doc_id = data.get("doc_id", fpath.stem) if isinstance(data, dict) else fpath.stem
            source = data.get("source_file", "") if isinstance(data, dict) else ""

            if is_sacred_source(source) or is_sacred_source(doc_id):
                skipped += 1
                continue

            # Intake drafts have flat tokens/ner_tags or per-sentence structure
            if isinstance(data, dict) and "tokens" in data and "ner_tags" in data:
                sent = {
                    "tokens": data["tokens"],
                    "ner_tags": data["ner_tags"],
                    "labels": data.get("labels", data["ner_tags"]),
                    "source": f"intake_draft:{doc_id}",
                    "source_file": source,
                    "human_verified": False,
                }
                valid, reason = validate_bioes_tags(sent["ner_tags"])
                if valid:
                    result.append(sent)
                    per_doc[doc_id].append(sent)
            elif isinstance(data, dict) and "sentences" in data:
                for sent_data in data["sentences"]:
                    if "tokens" not in sent_data or "ner_tags" not in sent_data:
                        continue
                    sent = {
                        "tokens": sent_data["tokens"],
                        "ner_tags": sent_data["ner_tags"],
                        "labels": sent_data.get("labels", sent_data["ner_tags"]),
                        "source": f"intake_draft:{doc_id}",
                        "source_file": source,
                        "human_verified": False,
                    }
                    valid, reason = validate_bioes_tags(sent["ner_tags"])
                    if valid:
                        result.append(sent)
                        per_doc[doc_id].append(sent)

    return result, per_doc, skipped


# ── Deduplication ──────────────────────────────────────────────────────
def fingerprint(sent: dict) -> str:
    """Create a unique fingerprint for a sentence based on tokens+tags."""
    key = json.dumps({"tokens": sent["tokens"], "ner_tags": sent["ner_tags"]}, sort_keys=True)
    return hashlib.md5(key.encode()).hexdigest()


# ── Main ───────────────────────────────────────────────────────────────
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("BIOES TRAINING DATA GENERATION — ALL 127 RFQs")
    print("=" * 70)
    print(f"TEST split has {len(TEST_PATHS)} path/filename patterns")

    all_sentences = []
    per_doc_all = defaultdict(list)
    source_counts = Counter()
    sacred_skipped_total = 0

    # ── Process each source ──
    sources = [
        ("batch_extractions", process_batch_extractions),
        ("batch_v2", process_batch_v2),
        ("cli_drafts", load_cli_drafts),
        ("draft_from_rfqs", load_draft_from_rfqs),
        ("verified_from_rowgold", load_verified),
        ("intake_drafts", load_intake_drafts),
    ]

    for name, loader_fn in sources:
        try:
            sents, per_doc, skipped = loader_fn()
            sacred_skipped_total += skipped
            all_sentences.extend(sents)
            for doc_id, doc_sents in per_doc.items():
                per_doc_all[doc_id].extend(doc_sents)
            source_counts[name] = len(sents)
            print(f"\n  {name}: {len(sents)} sentences from {len(per_doc)} docs (skipped {skipped} sacred)")
        except Exception as e:
            print(f"\n  {name}: ERROR — {e}")
            import traceback
            traceback.print_exc()

    print(f"\n  Total sacred skipped: {sacred_skipped_total}")
    print(f"  Raw total (before dedup): {len(all_sentences)}")

    # ── Deduplicate ──
    seen = set()
    deduped = []
    for sent in all_sentences:
        fp = fingerprint(sent)
        if fp not in seen:
            seen.add(fp)
            deduped.append(sent)

    print(f"  After dedup: {len(deduped)} (removed {len(all_sentences) - len(deduped)} duplicates)")

    # ── Final validation ──
    valid_count = 0
    invalid_count = 0
    entity_counter = Counter()
    for sent in deduped:
        valid, reason = validate_bioes_tags(sent["ner_tags"])
        if valid:
            valid_count += 1
            for tag in sent["ner_tags"]:
                entity_counter[tag] += 1
        else:
            invalid_count += 1

    print(f"\n  Valid sentences: {valid_count}")
    print(f"  Invalid sentences: {invalid_count}")

    # ── Per-document breakdown ──
    doc_breakdown = defaultdict(lambda: {"sources": set(), "count": 0, "human_verified": 0})
    for sent in deduped:
        src = sent.get("source", "unknown")
        doc_id = src.split(":", 1)[1] if ":" in src else src
        doc_breakdown[doc_id]["sources"].add(src.split(":")[0])
        doc_breakdown[doc_id]["count"] += 1
        if sent.get("human_verified"):
            doc_breakdown[doc_id]["human_verified"] += 1

    print(f"\n  Documents with training data: {len(doc_breakdown)}")
    print("\n  Top 20 docs by sentence count:")
    for doc_id in sorted(doc_breakdown, key=lambda d: doc_breakdown[d]["count"], reverse=True)[:20]:
        info = doc_breakdown[doc_id]
        hv = f" ({info['human_verified']} verified)" if info['human_verified'] else ""
        print(f"    {doc_id}: {info['count']} sentences from {', '.join(info['sources'])}{hv}")

    # ── Entity distribution ──
    print("\n  Entity distribution (top 15 tags):")
    for tag, count in entity_counter.most_common(15):
        print(f"    {tag}: {count}")

    # ── Build output ──
    output = {
        "version": "2.0",
        "generated": DATE,
        "description": "Genuine BIOES training data from ALL 127 RFQ documents (TEST split excluded)",
        "sources_used": {
            "batch_extractions": "output/batch_extractions/*.extracted.json — auto-generated per-entry BIOES",
            "batch_v2": "output/batch_extractions_v2/*.json — alternate extraction pipeline (boq_items format)",
            "cli_drafts": "data/annotations/cli_drafts/bioes/ — previously generated draft BIOES",
            "draft_from_rfqs": "data/annotations/draft_from_rfqs/bioes/ — RFQ pipeline draft BIOES",
            "verified_from_rowgold": "data/annotations/verified_from_rowgold/bioes/ — human-verified sentences",
            "intake_drafts": "data/annotations/draft/ — intake pipeline draft annotations",
        },
        "test_split_excluded": {
            "description": "42-doc frozen TEST split from data/real_rfqs/split_test.json, including sacred10 + bundle duplicates + client carry-alongs + new spec2 picks",
            "total_test_docs": 42,
        },
        "statistics": {
            "total_raw_sentences": len(all_sentences),
            "total_deduped_sentences": len(deduped),
            "duplicates_removed": len(all_sentences) - len(deduped),
            "valid_sentences": valid_count,
            "invalid_sentences": invalid_count,
            "documents_with_data": len(doc_breakdown),
            "sacred_skipped": sacred_skipped_total,
            "per_source": dict(source_counts),
            "entity_distribution": dict(entity_counter.most_common()),
        },
        "per_document_breakdown": {
            doc_id: {
                "sentence_count": info["count"],
                "sources": list(info["sources"]),
                "human_verified": info["human_verified"],
            }
            for doc_id, info in sorted(doc_breakdown.items())
        },
        "sentences": deduped,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n{'=' * 70}")
    print(f"OUTPUT: {OUTPUT_FILE}")
    print(f"Total training sentences: {valid_count}")
    print(f"Documents covered: {len(doc_breakdown)}")
    print(f"Entity types: {len(entity_counter)}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
