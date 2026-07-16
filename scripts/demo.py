"""RFQ2BOQ Demo — processes sample RFQ files and shows results."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline import Pipeline
from src.pipeline_xlsx import XLSXRowPipeline

console = Console()

DEMO_DIR = Path("results/demo")
DEMO_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    {
        "path": "data/real_rfqs/swa_enquiries/02_isro_vssc/VSSC_BOQ_with_qty.xlsx",
        "title": "ISRO VSSC — XLSX table extraction",
        "color": "green",
    },
    {
        "path": "data/real_rfqs/swa_enquiries/04_adani/BOQ PAGEadani proj.pdf",
        "title": "Adani — PDF table extraction (page 1)",
        "color": "cyan",
    },
]


def _as_dict(result) -> dict:
    if hasattr(result, "model_dump"):
        return result.model_dump()  # type: ignore[attr-defined]
    if hasattr(result, "dict"):
        return result.dict()  # type: ignore[attr-defined]
    return dict(result)


def print_boq_table(result: dict) -> None:
    table = Table(title="Bill of Quantities", show_lines=True)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Material", style="blue")
    table.add_column("Qty", style="green", width=8)
    table.add_column("Unit", style="yellow", width=6)
    table.add_column("Grade", style="magenta", width=8)
    table.add_column("Location", style="red", width=12)
    table.add_column("Conf", style="yellow", width=5)

    for idx, item in enumerate(result.get("boq_items", []), start=1):
        if hasattr(item, "model_dump"):
            item = item.model_dump()
        elif hasattr(item, "dict"):
            item = item.dict()
        conf = item.get("confidence", 0.0)
        conf_str = f"{conf * 100:.0f}%"
        table.add_row(
            str(idx),
            str(item.get("material", "N/A")),
            str(item.get("quantity", "")),
            str(item.get("unit", "")),
            str(item.get("grade", "")),
            str(item.get("location", "")),
            conf_str,
        )

    console.print(table)


def run_sample(sample: dict) -> None:
    path = Path(sample["path"])
    if not path.exists():
        console.print(f"[yellow]Skipping {sample['title']}: {path} not found[/yellow]")
        return

    console.print(Panel(f"[bold {sample['color']}]{sample['title']}[/bold {sample['color']}]\n{path}", expand=False))

    try:
        if path.suffix.lower() in {".xlsx", ".xls"}:
            result = XLSXRowPipeline().run(str(path))
        else:
            result = Pipeline().run(str(path))
        result_dict = _as_dict(result)
    except Exception as exc:
        console.print(f"[red]Extraction failed: {exc}[/red]")
        return

    print_boq_table(result_dict)

    out_path = DEMO_DIR / f"{path.stem}_demo.json"
    out_path.write_text(json.dumps(result_dict, indent=2, default=str))
    console.print(f"[dim]Saved JSON: {out_path}[/dim]\n")


def main() -> None:
    console.print("[bold]RFQ2BOQ Demo[/bold]\n")
    for sample in SAMPLES:
        run_sample(sample)
    console.print("[green]Demo complete.[/green]")


if __name__ == "__main__":
    main()
