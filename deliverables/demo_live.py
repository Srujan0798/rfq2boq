from src.pipeline import Pipeline
import sys, time

path = sys.argv[1] if len(sys.argv) > 1 else "data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf"

print(f"\n>>> Running RFQ2BOQ pipeline on: {path}\n")
t0 = time.time()
result = Pipeline().run(path)
elapsed = time.time() - t0

print(f"Extracted {len(result.boq_items)} BOQ line items in {elapsed:.2f}s\n")
print(f"{'#':<4}{'Material':<45}{'Qty':<10}{'Unit':<8}{'GeM Match':<10}")
print("-" * 80)
for item in result.boq_items:
    gem = "YES" if item.catalog_match and not item.catalog_match.get('is_unmatched') else "-"
    mat = item.material[:42] + "..." if len(item.material) > 42 else item.material
    print(f"{item.item_no:<4}{mat:<45}{str(item.quantity):<10}{item.unit:<8}{gem:<10}")
