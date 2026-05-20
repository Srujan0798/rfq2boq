"""Scrape real RFQ PDFs from Government e-Procurement portals.

Collects RFQ PDFs from:
- etenders.gov.in (CPWD, MES, various state PWDs)
- cppp.nic.in (Central Public Works Department)
- eprocure.gov.in (various ministries)

Usage:
    python scripts/scrape_etenders.py [--limit 50] [--output data/real_rfqs/raw]

Environment:
    Set proxies/credentials if needed for corporate networks.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))


SEARCH_TERMS = [
    "building construction",
    "residential building",
    "commercial complex",
    "hospital building",
    "school building",
    "office building",
    "warehouse construction",
]

TENDER_SOURCES = {
    "cpwd": "https://etenders.gov.in/eprocure/app?page=FrontEndOpenTendersAct.php&param=publish",
    "mes": "https://mes.gov.in/tenders",
    "delhi_pwd": "https://dda.org.in/tenders",
    "mh_publicworks": "https://mahapwd.com/tenders",
}


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape real RFQ PDFs from government portals")
    parser.add_argument("--limit", type=int, default=50, help="Maximum PDFs to download")
    parser.add_argument("--output", type=str, default="data/real_rfqs/raw", help="Output directory")
    parser.add_argument("--delay", type=float, default=2.0, help="Delay between requests (seconds)")
    parser.add_argument("--search-term", type=str, default=None, help="Override search term")
    parser.add_argument("--source", type=str, default=None, help="Specific source to scrape (cpwd/mes/etc)")
    return parser.parse_args()


def scrape_cpwd_tenders(output_dir: Path, limit: int, delay: float) -> list[dict[str, Any]]:
    import requests

    results = []
    tender_url = "https://etenders.gov.in/eprocure/app?page=FrontEndOpenTendersAct.php&param=publish"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(tender_url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch CPWD tenders: {e}")
        return results

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    tender_links = []
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if "tenderDocuments" in href or ".pdf" in href.lower():
            tender_links.append(link)

    print(f"Found {len(tender_links)} tender document links")

    for link in tender_links[:limit]:
        try:
            href = link.get("href", "")
            if not href:
                continue

            if href.startswith("/"):
                href = "https://etenders.gov.in" + href

            tender_name = link.get_text(strip=True) or "unnamed_tender"
            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in tender_name[:50])

            pdf_path = output_dir / f"cpwd_{safe_name}_{int(time.time())}.pdf"

            print(f"Downloading: {href[:80]}...")
            pdf_response = requests.get(href, headers=headers, timeout=60, stream=True)
            pdf_response.raise_for_status()

            with open(pdf_path, "wb") as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = pdf_path.stat().st_size
            if file_size > 10000:
                results.append({
                    "source": "cpwd",
                    "url": href,
                    "name": tender_name,
                    "path": str(pdf_path),
                    "size_bytes": file_size,
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                print(f"  Saved: {pdf_path.name} ({file_size / 1024:.1f} KB)")
            else:
                pdf_path.unlink()
                print(f"  Skipped (too small): {href[:60]}")

            time.sleep(delay)

        except Exception as e:
            print(f"  Failed to download: {e}")
            continue

    return results


def scrape_generic_tenders(source_name: str, url: str, output_dir: Path, limit: int, delay: float) -> list[dict[str, Any]]:
    import requests

    results = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch {source_name} tenders: {e}")
        return results

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    pdf_links = []
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        if ".pdf" in href.lower() or "tender" in href.lower():
            pdf_links.append((link.get_text(strip=True) or source_name, href))

    for name, href in pdf_links[:limit]:
        try:
            if href.startswith("/"):
                base_url = "/".join(url.split("/")[:3])
                href = base_url + href

            safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name[:50])
            pdf_path = output_dir / f"{source_name}_{safe_name}_{int(time.time())}.pdf"

            print(f"Downloading: {href[:80]}...")
            pdf_response = requests.get(href, headers=headers, timeout=60, stream=True)
            pdf_response.raise_for_status()

            with open(pdf_path, "wb") as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            file_size = pdf_path.stat().st_size
            if file_size > 10000:
                results.append({
                    "source": source_name,
                    "url": href,
                    "name": name,
                    "path": str(pdf_path),
                    "size_bytes": file_size,
                    "scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                })
                print(f"  Saved: {pdf_path.name} ({file_size / 1024:.1f} KB)")
            else:
                pdf_path.unlink(missing_ok=True)

            time.sleep(delay)

        except Exception as e:
            print(f"  Failed: {e}")
            continue

    return results


def filter_building_rfqs(pdfs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    building_keywords = [
        "building", "construction", "residential", "commercial", "hospital",
        "school", "office", "warehouse", "complex", "hostel", "institution",
        "workshop", "laboratory", "research", "housing",
    ]

    filtered = []
    for pdf in pdfs:
        name = pdf.get("name", "").lower()
        url = pdf.get("url", "").lower()
        combined = name + " " + url

        if any(kw in combined for kw in building_keywords):
            filtered.append(pdf)

    return filtered


def generate_metadata(pdfs: list[dict[str, Any]], output_dir: Path) -> None:
    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump({
            "total_collected": len(pdfs),
            "sources": list(set(p["source"] for p in pdfs)),
            "files": pdfs,
        }, f, indent=2)
    print(f"Metadata saved to {metadata_path}")


def main():
    args = parse_args()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    all_pdfs = []
    limit_per_source = max(1, args.limit // len(TENDER_SOURCES))

    sources_to_scrape = {"cpwd": TENDER_SOURCES["cpwd"]}
    if args.source is None:
        sources_to_scrape = TENDER_SOURCES

    for source_name, url in sources_to_scrape.items():
        if source_name == "cpwd":
            pdfs = scrape_cpwd_tenders(output_dir, limit_per_source, args.delay)
        else:
            pdfs = scrape_generic_tenders(source_name, url, output_dir, limit_per_source, args.delay)
        all_pdfs.extend(pdfs)
        print(f"Collected {len(pdfs)} PDFs from {source_name}")

    filtered_pdfs = filter_building_rfqs(all_pdfs)
    print(f"\nFiltered to {len(filtered_pdfs)} building-related RFQs")

    generate_metadata(filtered_pdfs, output_dir)

    print(f"\nScraping complete! Collected {len(filtered_pdfs)} PDFs")
    print(f"Files saved to: {output_dir}")

    print("\nNOTE: This script collects public tender documents.")
    print("For commercial use, ensure compliance with source terms of service.")
    print("Manual review is needed to filter relevant building construction RFQs.")


if __name__ == "__main__":
    try:
        from bs4 import BeautifulSoup  # noqa: F401
    except ImportError:
        print("Installing beautifulsoup4...")
        os.system(f"{sys.executable} -m pip install beautifulsoup4 requests -q")

    main()
