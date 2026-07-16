"""RFQ2BOQ CLI entry point."""

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

cli = typer.Typer(help="RFQ2BOQ - Extract BOQ from RFQ documents")
console = Console()


@cli.command()
def extract(
    input_file: str = typer.Option(..., help="Path to RFQ PDF or text file"),
    output: str = typer.Option("output.json", help="Output JSON file path"),
    format: str = typer.Option("json", help="Output format: json, excel, csv"),
):
    """Extract BOQ from a single RFQ document."""
    from src.pipeline import Pipeline

    path = Path(input_file)
    if not path.exists():
        console.print(f"[red]Error: File not found: {input_file}[/red]")
        raise typer.Exit(1)

    console.print(f"[cyan]Processing: {input_file}[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running extraction pipeline...", total=None)

        pipeline = Pipeline()
        result = pipeline.run(str(path))

        progress.update(task, description="Exporting results...")

        pipeline.export(result, output, format)

    console.print(f"[green]✅ Done! Output saved to: {output}[/green]")


@cli.command()
def batch(
    input_dir: str = typer.Option(..., help="Directory containing RFQ files"),
    output_dir: str = typer.Option("batch_output", help="Output directory"),
    format: str = typer.Option("json", help="Output format: json, excel, csv"),
):
    """Process multiple RFQ files from a directory."""
    from src.pipeline import Pipeline

    in_path = Path(input_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        console.print(f"[red]Error: Directory not found: {input_dir}[/red]")
        raise typer.Exit(1)

    files = (
        list(in_path.glob("*.pdf"))
        + list(in_path.glob("*.txt"))
        + list(in_path.glob("*.xlsx"))
        + list(in_path.glob("*.xls"))
    )
    if not files:
        console.print(f"[yellow]No files found in: {input_dir}[/yellow]")
        raise typer.Exit(0)

    console.print(f"[cyan]Found {len(files)} files to process[/cyan]")

    pipeline = Pipeline()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Processing {len(files)} files...", total=len(files))

        for f in files:
            console.print(f"  Processing: {f.name}")
            try:
                result = pipeline.run(str(f))
                out_file = out_path / f"{f.stem}_boq.{format}"
                pipeline.export(result, str(out_file), format)
                console.print(f"    [green]→ {out_file.name}[/green]")
            except Exception as e:
                console.print(f"    [red]✗ Error: {e}[/red]")
            progress.update(task, advance=1)

    console.print(f"[green]✅ Batch complete: {len(files)} files processed to {output_dir}[/green]")


@cli.command()
def serve(
    host: str = "0.0.0.0",
    port: int = 8000,
):
    """Start the RFQ2BOQ API server."""
    import uvicorn

    from src.api.main import app

    console.print(f"[green]Starting API server at http://{host}:{port}[/green]")
    uvicorn.run(app, host=host, port=port)


@cli.command()
def validate(
    input_file: str = typer.Option(..., help="Path to BOQ JSON file"),
):
    """Validate a BOQ JSON file."""
    import json

    from src.domain.models import BoqRow
    from src.domain.validator import DomainValidator

    path = Path(input_file)
    if not path.exists():
        console.print(f"[red]Error: File not found: {input_file}[/red]")
        raise typer.Exit(1)

    with open(path) as f:
        data = json.load(f)

    items = []
    for item_data in data.get("boq_items", data.get("boq", {}).get("items", [])):
        items.append(
            BoqRow(
                item_no=item_data.get("item_no", 0),
                material=item_data.get("material", ""),
                grade=item_data.get("grade", ""),
                quantity=item_data.get("quantity", 0),
                unit=item_data.get("unit", ""),
                action=item_data.get("action", ""),
                location=item_data.get("location", ""),
                standard=item_data.get("standard", []),
                dimensions=item_data.get("dimensions", []),
                confidence=item_data.get("confidence", 0.5),
                warnings=[],
            )
        )

    validator = DomainValidator()
    warnings = validator.validate_boq(items)

    if not warnings:
        console.print("[green]✅ No validation issues found[/green]")
    else:
        console.print(f"[yellow]⚠️ {len(warnings)} validation warnings:[/yellow]")
        for w in warnings:
            console.print(f"  - [{w.type.value}] Item {w.item_no}: {w.message}")


if __name__ == "__main__":
    cli()
