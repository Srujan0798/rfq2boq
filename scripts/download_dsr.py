"""Download CPWD DSR 2023 PDFs.

CPWD releases Delhi Schedule of Rates annually. The PDFs are public-domain
under RTI/NDSAP. This script attempts automated download from mirrors.

Usage:
    python3 scripts/download_dsr.py [--vol 1|2]

If automated download fails, manual instructions are printed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib import request

MIRRORS_V1 = [
    "https://cpwd.gov.in/Documents/DSR2023_Vol1_Civil.pdf",
    "https://helptheengineer.com/wp-content/uploads/DSR-2023-Vol-1.pdf",
    "https://civilenggascent.com/download/DSR-2023-Volume-1.pdf",
]

MIRRORS_V2 = [
    "https://cpwd.gov.in/Documents/DSR2023_Vol2.pdf",
    "https://helptheengineer.com/wp-content/uploads/DSR-2023-Vol-2.pdf",
]

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "rates" / "dsr_2023" / "raw_pdfs"


def download_file(url: str, dest: Path, timeout: int = 60) -> bool:
    try:
        req = request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; rfq2boq/1.0; "
                    "+https://github.com/srujan-sai/rfq2boq)"
                )
            },
        )
        with request.urlopen(req, timeout=timeout) as response:
            content = response.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "wb") as f:
                f.write(content)
            print(f"Downloaded: {url} -> {dest} ({len(content) / 1024 / 1024:.1f} MB)")
            return True
    except Exception as e:
        print(f"Failed: {url} — {e}")
        return False


def print_manual_instructions() -> None:
    print("\n" + "=" * 60)
    print("MANUAL DOWNLOAD REQUIRED")
    print("=" * 60)
    print(
        "\nCPWD blocks automated downloads. Please download manually:\n"
    )
    print("1. Open: https://cpwd.gov.in/Documents/cpwd_publication.aspx")
    print("   OR mirror: https://helptheengineer.com/cpwd-publication/")
    print("   OR search: 'CPWD DSR 2023 Vol 1 Civil PDF'")
    print("\n2. Download DSR 2023 Volume 1 (Civil) — typically ~80 MB")
    print("   (Volume 2 is electrical/specialty works — optional)")
    print(f"\n3. Save to: {OUTPUT_DIR.resolve()}")
    print("   Filename: DSR_Vol_1_Civil_2023.pdf")
    print("\n4. Re-run parse script:")
    print("   python3 scripts/parse_dsr_pdf.py")
    print("=" * 60 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Download CPWD DSR 2023 PDFs")
    parser.add_argument(
        "--vol",
        type=int,
        choices=[1, 2],
        default=1,
        help="Volume to download (default: 1)",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.vol == 1:
        filename = "DSR_Vol_1_Civil_2023.pdf"
        mirrors = MIRRORS_V1
    else:
        filename = "DSR_Vol_2_2023.pdf"
        mirrors = MIRRORS_V2

    dest = OUTPUT_DIR / filename

    if dest.exists():
        print(f"Already exists: {dest}")
        return 0

    print(f"Attempting download of DSR 2023 Vol {args.vol}...")
    for mirror in mirrors:
        if download_file(mirror, dest):
            return 0

    print_manual_instructions()
    return 1


if __name__ == "__main__":
    sys.exit(main())
