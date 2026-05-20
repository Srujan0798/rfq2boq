# TASK: Drawing/Plan Analysis — Agent-1

**Wave:** 3 | **Tier:** B | **Priority:** P3

## 1. GOAL
Multi-modal extraction: detect construction drawings (floor plans, elevations, sections) in RFQ PDFs, segment rooms, count symbols, estimate quantities from areas.

## 2. CONTEXT
Read first:
- `src/ingest/pdf_extractor.py` — current PDF extraction
- `src/ingest/ocr_processor.py` — current OCR
- `src/nlp/pipeline.py` — pipeline integration point
- [docs/conventions.md](../../docs/conventions.md)

Current state: PDFs treated as text-only; drawings ignored.

## 3. DELIVERABLES
- [ ] `src/vision/__init__.py`
- [ ] `src/vision/classifier.py` — drawing type classifier (floor plan / elevation / section / detail / other)
- [ ] `src/vision/symbols.py` — symbol detection (YOLOv8 fine-tuned on door/window/column/beam/stair)
- [ ] `src/vision/area.py` — area estimation from scale bar + room segmentation
- [ ] `src/drawing/__init__.py`
- [ ] `src/drawing/analyzer.py` — orchestrator: classify → segment → count → estimate
- [ ] `models/drawing-classifier/` — trained image classifier
- [ ] `models/symbol-detector/` — YOLOv8 weights (or pretrained baseline)
- [ ] `tests/unit/test_drawing_analysis.py` — ≥6 tests

## 4. STEPS
1. Add `ultralytics` (YOLOv8), `opencv-python`, `pdf2image` to deps
2. Classifier: small ResNet18 or ViT, fine-tune on labeled construction drawings (collect 200+ images)
3. Symbol detector: pretrained YOLOv8n → fine-tune on construction symbols
4. Area estimator: detect scale bar via OCR ("1:100"), segment via thresholding, compute pixel area → m²
5. Drawing analyzer: takes PDF page → renders to image → runs all three
6. Pipeline: if drawings detected, run drawing pipeline + merge results into BOQ (e.g., flooring quantity from floor plan)

## 5. VERIFICATION
```bash
$ python3 -c "from src.vision.classifier import DrawingClassifier; c = DrawingClassifier(); print(c.classes)"
EXPECT: list of class names

$ python3 -m pytest tests/unit/test_drawing_analysis.py -v
EXPECT: ≥6 passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] Classifier accuracy ≥70% on held-out test
- [ ] Symbol detection precision ≥50% (initial baseline)
- [ ] Area estimation within 20% of ground truth on test images
- [ ] Pipeline doesn't crash on drawing-free PDFs
- [ ] Coverage ≥80% on new code

## 7. CONSTRAINTS
- All imports `src.` prefix
- Drawing analysis MUST be optional (configurable via `RFQ2BOQ_ENABLE_DRAWING_ANALYSIS`)
- Models stay under 100MB each
- DO NOT make this block text extraction

## 8. DEPENDENCIES
- **Blocked by:** None
- **Blocks:** None
- **Parallel-safe with:** B1, B2, B3, B5

## 9. GOTCHAS
- Collecting 200+ labeled construction drawings is the hard part — start with synthetic / public datasets
- YOLOv8 needs GPU for training; CPU inference is OK
- Scale bar OCR is unreliable — verify before computing areas
- PDF → image rendering at 300 DPI for accuracy, but memory-heavy for large PDFs
- Area calculations need calibration per drawing (scale bar location varies)
