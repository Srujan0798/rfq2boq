"""CSV export for BOQ data."""

from src.domain.models import ExtractionResult


class CSVExporter:
    def generate(self, result: ExtractionResult, output_path: str) -> None:
        import csv
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Item No", "Material", "Grade", "Quantity", "Unit",
                "Action", "Location", "Standard", "Dimensions",
                "Confidence", "Warnings", "Description",
            ])
            for item in result.boq_items:
                writer.writerow([
                    item.item_no,
                    item.material or "",
                    item.grade or "",
                    item.quantity or "",
                    item.unit or "",
                    item.action or "",
                    item.location or "",
                    ", ".join(item.standard) if item.standard else "",
                    ", ".join(getattr(item, "dimensions", []) or []),
                    f"{item.confidence:.2f}" if item.confidence else "",
                    ", ".join(str(w) for w in (getattr(item, "warnings", []) or [])),
                    item.description_raw or "",
                ])

    def export(self, result: ExtractionResult, output_path: str) -> None:
        self.generate(result, output_path)
