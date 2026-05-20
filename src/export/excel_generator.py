"""CPWD-format Excel BOQ generator — polished professional output."""

import json
from datetime import datetime
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

INDIAN_NUMBER_FORMAT = '₹#,##,##0.00'
INDIAN_QTY_FORMAT = '#,##,##0.00'


class CPWDExcelGenerator:
    TRADE_GROUPS = {
        "excavation": ["excavation", "earthwork", "cutting", "filling"],
        "concrete": ["concrete", "cement concrete", "rcc", "pcc", "casting"],
        "brickwork": ["brickwork", "brick masonry", "aac", "blockwork", "masonry"],
        "plaster": ["plaster", "pointing", "finishing", "ceiling"],
        "flooring": ["flooring", "tile", "marble", "granite", "dado", "skirting"],
        "steel": ["steel", "reinforcement", "fabrication", "tor steel"],
        "woodwork": ["woodwork", "door", "window", "shutter"],
        "painting": ["painting", "distemper", "white wash", "colour", "varnish"],
        "plumbing": ["plumbing", "pipe", "gi", "pvc", "water", "drainage"],
        "electrical": ["electrical", "wiring", "conduit", "cable", "switch"],
        "waterproofing": ["waterproofing", "torching", "membrane"],
        "finishing": ["finishing", "polishing", "grinding"],
        "general": [],
    }

    def __init__(self, template_path: str | None = None, dsr_rates_path: str | None = None):
        self.template_path = template_path
        self.dsr_rates = self._load_dsr_rates(dsr_rates_path)

    def _load_dsr_rates(self, path: str | None) -> dict[str, dict]:
        if path is None:
            path = "data/rates/cpwd_dsr_2023.json"
        p = Path(path)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
                return {item["description"].lower(): item for item in data.get("items", [])}
        return {}

    def _detect_trade(self, description: str) -> str:
        desc_lower = description.lower()
        for trade, keywords in self.TRADE_GROUPS.items():
            if trade == "general":
                continue
            for kw in keywords:
                if kw in desc_lower:
                    return trade
        return "general"

    def _lookup_dsr(self, description: str) -> tuple[str | None, float | None]:
        desc_lower = description.lower()
        best_key = None
        for key in self.dsr_rates:
            if (key in desc_lower or desc_lower in key) and (best_key is None or len(key) > len(best_key)):
                best_key = key
        if best_key:
            item = self.dsr_rates[best_key]
            return item.get("code"), item.get("rate_inr")
        return None, None

    def _as_dict(self, item) -> dict:
        if isinstance(item, dict):
            return item
        if hasattr(item, "model_dump"):
            return item.model_dump()  # type: ignore
        if hasattr(item, "__dict__"):
            return dict(item.__dict__)
        return {}

    def _get_amount(self, item: dict) -> float:
        amount = item.get("amount")
        if amount is not None:
            try:
                return float(amount)
            except (ValueError, TypeError):
                pass
        quantity = float(item.get("quantity", 0) or 0)
        rate = item.get("rate") or item.get("rate_source")
        if isinstance(rate, str):
            try:
                rate = float(rate.replace(",", "").replace("₹", "").strip())
            except (ValueError, AttributeError):
                rate = 0.0
        if rate is None:
            rate = 0.0
        return quantity * float(rate)

    def export(
        self,
        boq_items: list,
        output_path: str,
        project_metadata: dict | None = None,
    ) -> None:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BOQ"

        if project_metadata is None:
            project_metadata = {}

        self._write_header(ws, project_metadata)
        row = self._write_column_headers(ws, 9)

        items_start_row = row

        boq_dicts = [self._as_dict(it) for it in boq_items]

        trade_map: dict[str, list[dict]] = {}
        for item in boq_dicts:
            trade = self._detect_trade(item.get("material", item.get("description", "")))
            trade_map.setdefault(trade, []).append(item)

        serial = 1
        trade_rows: dict[str, tuple[int, int]] = {}

        for trade in sorted(trade_map.keys()):
            trade_start = row
            for item in sorted(trade_map[trade], key=lambda x: x.get("description", "").lower()):
                row = self._write_item_row(ws, row, serial, item)
                serial += 1
            trade_rows[trade] = (trade_start, row - 1)
            row = self._write_trade_subtotal(ws, row, trade, trade_start, row - 1)

        items_end_row = row - 1

        grand_total_row = self._write_grand_total(ws, row, items_start_row, items_end_row)
        row = self._write_gst_and_net(ws, grand_total_row + 1, grand_total_row)
        row = self._write_notes(ws, row)
        self._write_signatures(ws, row + 1)

        self._set_column_widths(ws)
        ws.freeze_panes = f"A{items_start_row}"

        _output = Path(output_path)
        _output.parent.mkdir(parents=True, exist_ok=True)
        wb.save(_output)

    def _write_header(self, ws, meta: dict) -> int:
        title_font = Font(bold=True, size=14, color="1F4E78")
        label_font = Font(bold=True, size=10)
        value_font = Font(size=10)

        ws.cell(row=1, column=1, value="BILL OF QUANTITIES (CPWD FORMAT)")
        ws.cell(row=1, column=1).font = title_font
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)
        ws.row_dimensions[1].height = 22

        row = 2
        meta_fields = [
            ("Project Name:", meta.get("project_name", meta.get("project", "N/A"))),
            ("Location:", meta.get("location", "N/A")),
            ("Date:", datetime.now().strftime("%d-%b-%Y")),
            ("RFQ Reference:", meta.get("reference", "N/A")),
            ("Contractor:", meta.get("contractor", "N/A")),
        ]
        for label, value in meta_fields:
            ws.cell(row=row, column=1, value=label).font = label_font
            ws.cell(row=row, column=2, value=value).font = value_font
            ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=8)
            ws.row_dimensions[row].height = 16
            row += 1

        ws.row_dimensions[row].height = 8
        row += 1

        return row

    def _write_column_headers(self, ws, start_row: int = 9) -> int:
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=10)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="double"),
        )
        col_headers = ["S.No", "DSR Code", "Description", "Unit", "Quantity", "Rate (₹)", "Amount (₹)", "Notes"]
        for col, header in enumerate(col_headers, 1):
            cell = ws.cell(row=start_row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        ws.row_dimensions[start_row].height = 28
        return start_row + 1

    def _write_item_row(
        self,
        ws,
        row: int,
        serial: int,
        item: dict,
    ) -> int:
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        description = item.get("material") or item.get("description", "")
        unit = item.get("unit", "no.")
        quantity = float(item.get("quantity", 0) or 0)
        dsr_code, dsr_rate = self._lookup_dsr(description)

        rate = item.get("rate") or item.get("rate_source")
        if dsr_rate and dsr_rate > 0:
            rate = dsr_rate
            note = ""
        else:
            if isinstance(rate, str):
                try:
                    rate = float(rate.replace(",", "").replace("₹", "").strip())
                except (ValueError, AttributeError):
                    rate = 0.0
            elif rate is None:
                rate = 0.0
            note = "rate estimated" if not dsr_code else ""

        amount = float(quantity) * float(rate) if rate else 0.0

        ws.cell(row=row, column=1, value=serial).border = thin_border
        ws.cell(row=row, column=1).alignment = Alignment(horizontal="center")

        code_cell = ws.cell(row=row, column=2, value=dsr_code or "")
        code_cell.border = thin_border
        code_cell.alignment = Alignment(horizontal="center")
        if dsr_code:
            code_cell.number_format = "@"

        desc_cell = ws.cell(row=row, column=3)
        desc_cell.value = description.title() if description else "Unknown Item"
        desc_cell.border = thin_border
        desc_cell.alignment = Alignment(wrap_text=True, vertical="top")

        ws.cell(row=row, column=4, value=unit).border = thin_border
        ws.cell(row=row, column=4).alignment = Alignment(horizontal="center")

        qty_cell = ws.cell(row=row, column=5, value=quantity)
        qty_cell.border = thin_border
        qty_cell.number_format = INDIAN_QTY_FORMAT
        qty_cell.alignment = Alignment(horizontal="right")

        rate_cell = ws.cell(row=row, column=6, value=float(rate) if rate else 0)
        rate_cell.border = thin_border
        rate_cell.number_format = INDIAN_NUMBER_FORMAT
        rate_cell.alignment = Alignment(horizontal="right")

        amt_cell = ws.cell(row=row, column=7, value=amount)
        amt_cell.border = thin_border
        amt_cell.number_format = INDIAN_NUMBER_FORMAT
        amt_cell.alignment = Alignment(horizontal="right")

        ws.cell(row=row, column=8, value=note).border = thin_border
        ws.cell(row=row, column=8).alignment = Alignment(horizontal="center")

        ws.row_dimensions[row].height = 18
        return row + 1

    def _write_trade_subtotal(
        self,
        ws,
        row: int,
        trade: str,
        start: int,
        end: int,
    ) -> int:
        subtotal_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        subtotal_font = Font(bold=True, size=10, color="1F4E78")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )
        label_cell = ws.cell(row=row, column=1)
        label_cell.value = f"Subtotal — {trade.title()}"
        label_cell.font = subtotal_font
        label_cell.fill = subtotal_fill
        label_cell.border = thin_border
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        for c in range(2, 7):
            ws.cell(row=row, column=c).border = thin_border
            ws.cell(row=row, column=c).fill = subtotal_fill

        amt_cell = ws.cell(row=row, column=7, value=f"=SUM(G{start}:G{end})")
        amt_cell.font = subtotal_font
        amt_cell.fill = subtotal_fill
        amt_cell.number_format = INDIAN_NUMBER_FORMAT
        amt_cell.border = thin_border
        ws.cell(row=row, column=8).fill = subtotal_fill
        ws.cell(row=row, column=8).border = thin_border
        ws.row_dimensions[row].height = 18
        return row + 1

    def _write_grand_total(
        self,
        ws,
        row: int,
        items_start: int,
        items_end: int,
    ) -> int:
        grand_fill = PatternFill(start_color="2E4057", end_color="2E4057", fill_type="solid")
        grand_font = Font(bold=True, color="FFFFFF", size=11)
        double_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="medium"),
            bottom=Side(style="double"),
        )

        label_cell = ws.cell(row=row, column=1)
        label_cell.value = "GRAND TOTAL"
        label_cell.font = grand_font
        label_cell.fill = grand_fill
        label_cell.border = double_border
        ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        for c in range(2, 7):
            ws.cell(row=row, column=c).fill = grand_fill
            ws.cell(row=row, column=c).border = double_border

        amt_cell = ws.cell(row=row, column=7, value=f"=SUM(G{items_start}:G{items_end})")
        amt_cell.font = grand_font
        amt_cell.fill = grand_fill
        amt_cell.number_format = INDIAN_NUMBER_FORMAT
        amt_cell.border = double_border
        ws.cell(row=row, column=8).fill = grand_fill
        ws.cell(row=row, column=8).border = double_border
        ws.row_dimensions[row].height = 22
        return row

    def _write_gst_and_net(self, ws, row: int, grand_total_row: int) -> int:
        label_font = Font(bold=True, size=10)
        net_font = Font(bold=True, size=12, color="1F4E78")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin"),
        )

        gst_cell = ws.cell(row=row, column=6, value="Add GST 18%:")
        gst_cell.font = label_font
        gst_cell.border = thin_border
        gst_amt = ws.cell(row=row, column=7, value=f"=G{grand_total_row}*0.18")
        gst_amt.number_format = INDIAN_NUMBER_FORMAT
        gst_amt.border = thin_border
        ws.cell(row=row, column=8).border = thin_border
        ws.row_dimensions[row].height = 18
        row += 1

        net_label = ws.cell(row=row, column=6, value="NET TOTAL (incl. GST):")
        net_label.font = net_font
        net_label.border = thin_border
        net_amt = ws.cell(row=row, column=7, value=f"=G{grand_total_row}+G{row-1}")
        net_amt.font = net_font
        net_amt.number_format = INDIAN_NUMBER_FORMAT
        net_amt.border = thin_border
        ws.cell(row=row, column=8).border = thin_border
        ws.row_dimensions[row].height = 22
        row += 2
        return row

    def _write_notes(self, ws, row: int) -> int:
        note_font = Font(size=9, italic=True, color="595959")
        ws.cell(row=row, column=1, value="Notes:").font = Font(bold=True, size=10)
        row += 1
        notes = [
            "1. Rates are as per CPWD DSR 2023 unless otherwise mentioned.",
            "2. Items without DSR code are estimated based on available data and subject to verification.",
            "3. Quantities are as extracted from the RFQ tender document; re-measurement at site shall prevail.",
            "4. All rates are in INR and inclusive of all taxes, duties, and delivery to site.",
        ]
        for note in notes:
            ws.cell(row=row, column=1, value=note).font = note_font
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=8)
            ws.row_dimensions[row].height = 14
            row += 1
        return row + 1

    def _write_signatures(self, ws, row: int) -> None:
        sig_font = Font(size=10)
        ws.cell(row=row, column=1, value="Prepared by: ___________________").font = sig_font
        ws.cell(row=row, column=4, value="Checked by: ___________________").font = sig_font
        ws.cell(row=row, column=7, value="Approved by: ___________________").font = sig_font
        ws.row_dimensions[row].height = 20

    def _set_column_widths(self, ws) -> None:
        widths = [6, 11, 42, 8, 10, 13, 14, 20]
        for col, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(col)].width = w


def create_cpwd_exporter() -> CPWDExcelGenerator:
    return CPWDExcelGenerator()


class ExcelGenerator(CPWDExcelGenerator):
    def generate(self, result, output_path: str, project_metadata: dict | None = None) -> None:
        self.export(result, output_path, project_metadata)


if __name__ == "__main__":
    gen = CPWDExcelGenerator()
    print(f"CPWD Excel generator ready with {len(gen.dsr_rates)} DSR rates")
    print(f"Trade groups: {[k for k in gen.TRADE_GROUPS if k != 'general']}")
