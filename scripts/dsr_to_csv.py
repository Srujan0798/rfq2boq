"""Convert cpwd_dsr_2023.json to CSV for spreadsheet compatibility."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


def dsr_to_csv(json_path: Path, csv_path: Path | None = None) -> int:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    items = data.get("items", [])
    if not items:
        print(f"No items found in {json_path}")
        return 1

    if csv_path is None:
        csv_path = json_path.with_suffix(".csv")

    fieldnames = ["code", "description", "chapter", "unit", "rate_inr", "year"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

    print(f"Exported {len(items)} items to {csv_path}")
    return 0


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Convert cpwd_dsr_2023.json to CSV")
    parser.add_argument(
        "--json",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "rates" / "cpwd_dsr_2023.json",
        help="Input JSON file",
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Output CSV file",
    )
    args = parser.parse_args()
    return dsr_to_csv(args.json, args.csv)


if __name__ == "__main__":
    sys.exit(main())
