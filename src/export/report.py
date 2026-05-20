"""Report generator for BOQ output."""

from src.domain.models import ExtractionResult


class ReportGenerator:
    def generate(self, result: ExtractionResult) -> str:
        lines = [
            f"Project: {result.project_name}",
            f"Document: {result.source_file}",
            f"Extraction Date: {result.extraction_date.isoformat() if result.extraction_date else 'N/A'}",
            "",
            f"Total Items: {len(result.boq_items)}",
            f"Average Confidence: {result.metadata.avg_confidence:.2f}",
            "",
            "Bill of Quantities:",
            "-" * 80,
        ]

        if not result.boq_items:
            return "\n".join(lines)

        for item in result.boq_items:
            lines.append(f"\nItem #{item.item_no}")
            lines.append(f"  Material: {item.material}")
            lines.append(f"  Quantity: {item.quantity} {item.unit}")
            lines.append(f"  Action: {item.action}")
            if item.grade:
                lines.append(f"  Grade: {item.grade}")
            if item.standard:
                lines.append(f"  Standard: {', '.join(item.standard)}")
            if item.location:
                lines.append(f"  Location: {item.location}")
            lines.append(f"  Confidence: {item.confidence:.2f}")
            if item.description_raw:
                lines.append(f"  Description: {item.description_raw}")

        return "\n".join(lines)
