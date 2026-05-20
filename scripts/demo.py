"""RFQ2BOQ Demo — processes sample PDFs and shows results."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.pipeline import Pipeline

console = Console()

DEMO_DIR = Path("results/demo")
DEMO_DIR.mkdir(parents=True, exist_ok=True)


SAMPLES = {
    "simple": {
        "path": "data/samples/sample_rfq_simple.pdf",
        "title": "Simple RFQ (2 pages, ~6 items)",
        "color": "green",
    },
    "medium": {
        "path": "data/samples/sample_rfq_medium.pdf",
        "title": "Medium RFQ (5 pages, ~15 items)",
        "color": "cyan",
    },
    "complex": {
        "path": "data/samples/sample_rfq_complex.pdf",
        "title": "Complex RFQ (10 pages, ~35 items)",
        "color": "magenta",
    },
}


ENTITY_COLORS = {
    "MATERIAL": "blue",
    "QUANTITY": "green",
    "UNIT": "yellow",
    "GRADE": "cyan",
    "STANDARD": "magenta",
    "LOCATION": "red",
    "DIMENSION": "white",
    "ACTION": "bold green",
}


def print_entities(result):
    table = Table(title="Extracted Entities", show_lines=True)
    table.add_column("Text", style="cyan", no_wrap=False)
    table.add_column("Type", style="bold")
    table.add_column("Start", style="dim")
    table.add_column("End", style="dim")
    table.add_column("Conf", style="yellow")

    for e in result.get("entities", []):
        conf = e.get("conf", 0)
        conf_str = f"{conf * 100:.0f}%" if conf else "N/A"
        table.add_row(
            e.get("text", ""),
            e.get("type", "UNKNOWN"),
            str(e.get("start", "")),
            str(e.get("end", "")),
            conf_str,
        )

    console.print(table)


def print_boq_table(result):
    table = Table(title="Bill of Quantities", show_lines=True)
    table.add_column("#", style="cyan", width=3)
    table.add_column("Material", style="blue")
    table.add_column("Qty", style="green", width=8)
    table.add_column("Unit", style="yellow", width=6)
    table.add_column("Grade", style="magenta", width=8)
    table.add_column("Action", style="white", width=8)
    table.add_column("Location", style="red", width=12)
    table.add_column("Conf", style="yellow", width=5)

    for item in result.get("boq_items", []):
        conf = item.get("confidence", 0)
        conf_str = f"{conf * 100:.0f}%"
        table.add_row(
            str(item.get("item_no", "")),
            item.get("material", "N/A"),
            str(item.get("quantity", "")),
            item.get("unit", ""),
            item.get("grade", ""),
            item.get("action", ""),
            item.get("location", ""),
            conf_str,
        )

    console.print(table)


def print_summary(result, processing_time):
    meta = result.get("metadata", {})
    entities = result.get("entities", [])
    items = result.get("boq_items", [])

    entity_counts = meta.get("entity_counts", {})
    entity_str = ", ".join(f"{k}: {v}" for k, v in entity_counts.items()) if entity_counts else "None"

    avg_conf = meta.get("avg_confidence", 0)
    avg_conf_str = f"{avg_conf * 100:.1f}%" if avg_conf else "N/A"

    summary = f"""[bold]Extraction Summary[/bold]

Total Entities Found: {len(entities)}
Total BOQ Items: {len(items)}

Entity Types: {entity_str}

Average Confidence: {avg_conf_str}
Processing Time: {processing_time:.2f}s
Pages Processed: {meta.get('pages_processed', 'N/A')}

Warnings: {len(meta.get('warnings', []))}"""

    console.print(Panel(summary, title="Summary", border_style="cyan"))


def process_sample(name, info):
    path = Path(info["path"])
    if not path.exists():
        console.print(f"[yellow]⚠ Sample file not found: {path}[/yellow]")
        return None

    console.print(f"\n[bold {info['color']}]Processing: {info['title']}[/bold {info['color']}]")
    console.print(f"[dim]Path: {path}[/dim]\n")

    start = datetime.now()
    pipeline = Pipeline()
    result = pipeline.run(str(path))
    processing_time = (datetime.now() - start).total_seconds()

    result_dict = result.model_dump() if hasattr(result, 'model_dump') else {
        "entities": [
            {
                "text": e.text if hasattr(e, 'text') else str(e),
                "type": e.type.value if hasattr(e.type, 'value') else str(e.type),
                "start": e.start,
                "end": e.end,
                "conf": e.conf,
            }
            for e in result.entities
        ],
        "boq_items": [
            {
                "item_no": i.item_no,
                "material": i.material,
                "quantity": str(i.quantity),
                "unit": i.unit,
                "grade": i.grade,
                "action": i.action,
                "location": i.location,
                "confidence": i.confidence,
            }
            for i in result.boq_items
        ],
        "metadata": {
            "total_items": result.metadata.total_items if result.metadata else 0,
            "avg_confidence": result.metadata.avg_confidence if result.metadata else 0,
            "pages_processed": result.metadata.pages_processed if result.metadata else 0,
            "entity_counts": result.metadata.entity_counts if result.metadata else {},
            "warnings": result.metadata.warnings if result.metadata else [],
        },
    }

    print_entities(result_dict)
    console.print()
    print_boq_table(result_dict)
    console.print()
    print_summary(result_dict, processing_time)

    excel_path = DEMO_DIR / f"boq_{name}.xlsx"
    json_path = DEMO_DIR / f"boq_{name}.json"

    pipeline.export(result, str(excel_path), "excel")
    console.print(f"[green]✓ Excel: {excel_path}[/green]")

    pipeline.export(result, str(json_path), "json")
    console.print(f"[green]✓ JSON: {json_path}[/green]")

    return result_dict


def main():
    console.print(Panel("[bold cyan]RFQ to BOQ Extraction System[/bold cyan]\nDemo Pipeline", border_style="cyan"))
    console.print()

    results = {}
    for name, info in SAMPLES.items():
        result = process_sample(name, info)
        if result:
            results[name] = result

    console.print("\n[bold cyan]========================================[/bold cyan]")
    console.print("[bold]Demo Complete![/bold]")
    console.print(f"\nOutputs saved to: [cyan]{DEMO_DIR.absolute()}[/cyan]")
    console.print("\nFiles generated:")
    for f in DEMO_DIR.glob("*"):
        console.print(f"  - {f.name}")

    console.print("\n[bold cyan]Next Steps:[/bold cyan]")
    console.print("  1. View generated Excel files in results/demo/")
    console.print("  2. Start API: make demo-api")
    console.print("  3. Start UI: make demo-ui")
    console.print("  4. Try CLI: rfq2boq extract data/samples/sample_rfq_simple.pdf -o output.xlsx")


if __name__ == "__main__":
    main()
