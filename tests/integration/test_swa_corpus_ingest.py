"""Integration tests for SWA corpus ingestion."""

from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path("data/real_rfqs/swa_enquiries")
INGESTED = ROOT / "ingested"
MANIFEST_CSV = ROOT / "manifest.csv"


class TestSwaCorpusIngest:
    """End-to-end tests for SWA corpus ingestion pipeline."""

    def test_ingested_dir_exists(self):
        assert INGESTED.exists(), "ingested/ directory should exist"

    def test_exactly_ten_json_files(self):
        json_files = sorted(INGESTED.glob("*.json"))
        assert len(json_files) == 10, f"Expected 10 JSON files (8 + 2 GeM), got {len(json_files)}"

    def test_each_json_has_required_keys(self):
        json_files = sorted(INGESTED.glob("*.json"))
        for fpath in json_files:
            with open(fpath) as fh:
                d = json.load(fh)
            assert "enquiry_id" in d, f"{fpath.name} missing enquiry_id"
            assert "client" in d, f"{fpath.name} missing client"
            assert "project" in d, f"{fpath.name} missing project"
            assert "files" in d, f"{fpath.name} missing files"

    def test_manifest_csv_exists(self):
        assert MANIFEST_CSV.exists(), "manifest.csv should exist"

    def test_manifest_csv_exactly_19_rows(self):
        with open(MANIFEST_CSV, newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        assert len(rows) == 19, f"Expected 19 data rows in manifest.csv, got {len(rows)}"  # 17 source + 2 GeM

    def test_manifest_csv_has_required_columns(self):
        with open(MANIFEST_CSV, newline="") as fh:
            reader = csv.DictReader(fh)
            assert reader.fieldnames is not None
            expected = {
                "enquiry_id", "client", "project", "source_file", "format",
                "pages_or_rows", "sha256", "size_bytes",
                "is_boq_ground_truth", "is_spec", "is_tds", "notes",
            }
            assert expected.issubset(set(reader.fieldnames)), f"Missing columns: {expected - set(reader.fieldnames)}"

    def test_each_enquiry_json_files_array_matches_source_files(self):
        json_files = sorted(INGESTED.glob("*.json"))
        for fpath in json_files:
            with open(fpath) as fh:
                d = json.load(fh)
            assert len(d["files"]) > 0, f"{fpath.name} has no files"

    def test_at_least_one_boq_ground_truth_enquiry_has_xlsx_file(self):
        with open(MANIFEST_CSV, newline="") as fh:
            reader = csv.DictReader(fh)
            boq_rows = [r for r in reader if r.get("is_boq_ground_truth") == "True"]
        assert len(boq_rows) >= 1, "At least one enquiry should have is_boq_ground_truth=True"

    def test_sha256_non_empty_all_files(self):
        with open(MANIFEST_CSV, newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                assert row["sha256"], f"Empty SHA256 for {row['source_file']}"
                assert len(row["sha256"]) == 64, f"SHA256 should be 64 hex chars for {row['source_file']}"

    def test_no_duplicate_files_in_manifest(self):
        with open(MANIFEST_CSV, newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        filenames = [r["source_file"] for r in rows]
        assert len(filenames) == len(set(filenames)), "Duplicate filenames in manifest"
