# SWA Demo Guide (S6, honest, real PDFs/XLSX only)

1. Env: python3 (3.11-13 preferred per CLAUDE; MPS only).
2. Install: python3 -m pip install -e ".[dev]"
3. Smoke (unpriced, real): python3 -c "
from src.pipeline import Pipeline
p=Pipeline()
for e in ['02_isro_vssc/VSSC_BOQ_with_qty.xlsx', '03_zydus_matoda_osd/Zydus_Matoda_Insulation_Enquiry.xlsx']:
  r=p.run('data/real_rfqs/swa_enquiries/' + e)
  print(e.split('/')[0], ':', len(r.boq_items), 'rows')
"  # expect 8 / 33 etc exact
4. UI: streamlit run ui/app.py ; upload real from data/real_rfqs/swa_enquiries/ (e.g. 05 strongest 48 rows, 03 100% honest).
5. Honest eval: python3 scripts/validate_product.py --enquiry all (rowgold preferred for XLSX; independent for PDF); Kimi overlap for quick XLSX view.
6. 10 SWA: lead XLSX (02/03/05/08 exact your table); PDFs (04/06/07 human gold; 01/09/10 weak — do NOT live demo 09/10).

No rates/pricing (S1). No samples (S2). Real corpus only (S3). PDF improved (S4). Gold owner (S5). Numbers honest (32.3% row, no 100% fakes).

See EXECUTIVE_SUMMARY.md, HANDOFF_FINAL_BRUTAL.md, results/.
