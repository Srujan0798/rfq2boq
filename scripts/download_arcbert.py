#!/usr/bin/env python3
"""Download ARCBERT model or SciBERT fallback.

Usage:
    python scripts/download_arcbert.py [--output models/arcbert-base]
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def download_arcbert(output_dir: str = "models/arcbert-base") -> bool:
    """Try to download ARCBERT, fall back to SciBERT on failure."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print("Attempting to download ARCBERT from HuggingFace...")
    try:
        from transformers import AutoModelForTokenClassification, AutoTokenizer

        model_name = "lsj126/arcbert-base"
        print(f"  Downloading: {model_name}")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=33,
        )
        tokenizer.save_pretrained(output_path)
        model.save_pretrained(output_path)
        print(f"  SUCCESS: ARCBERT saved to {output_path}")
        return True
    except Exception as e:
        print(f"  ARCBERT not available: {e}")
        print("  Falling back to SciBERT...")

    try:
        from transformers import AutoModelForTokenClassification, AutoTokenizer

        fallback_name = "allenai/scibert_scivocab_uncased"
        print(f"  Downloading: {fallback_name}")
        tokenizer = AutoTokenizer.from_pretrained(fallback_name)
        model = AutoModelForTokenClassification.from_pretrained(
            fallback_name,
            num_labels=33,
        )
        tokenizer.save_pretrained(output_path)
        model.save_pretrained(output_path)
        print(f"  SUCCESS: SciBERT fallback saved to {output_path}")

        Path(output_path / "FALLBACK_NOTICE.txt").write_text(
            "ARCBERT was not available. SciBERT (allenai/scibert_base_vocab_uncased) used as fallback.\n"
            "SciBERT is available under Apache 2.0 license.\n"
        )
        return True
    except Exception as e:
        print(f"  SciBERT fallback also failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download ARCBERT or SciBERT fallback")
    parser.add_argument("--output", default="models/arcbert-base", help="Output directory")
    args = parser.parse_args()

    success = download_arcbert(args.output)
    if not success:
        print("ERROR: Could not download any model. Check network connection.")
        sys.exit(1)


if __name__ == "__main__":
    main()
