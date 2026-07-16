# TASK: Voice Input for On-Site BOQ Editing — Agent-3

**Wave:** 3 | **Tier:** B | **Priority:** P3

## 1. GOAL
Voice-driven BOQ editing for site engineers. Speak edits like "add 50 bags of cement to ground floor" → system parses → applies to BOQ.

## 2. CONTEXT
Read first:
- `src/nlp/pipeline.py` — entity extraction reused for intent parsing
- `src/domain/boq_assembler.py` — BoqRow construction
- `web/components/` — for React integration
- [docs/conventions.md](../../../docs/conventions.md)

## 3. DELIVERABLES
- [ ] `src/voice/__init__.py`
- [ ] `src/voice/transcriber.py` — Whisper-small wrapper
- [ ] `src/voice/input.py` — `VoiceInputProcessor` (audio → intent → action)
- [ ] `src/voice/intents.py` — intent grammar (AddItem, UpdateItem, DeleteItem, Query)
- [ ] `src/api/routes/voice.py` — `POST /v1/voice/input` (audio file upload)
- [ ] `web/components/VoiceInput.tsx` — record mic, send, display result
- [ ] `tests/unit/test_voice.py` — ≥6 tests (mocked audio)

## 4. STEPS
1. Add `openai-whisper` to deps (or `faster-whisper` for speed)
2. Transcriber: WAV/MP3 → text via whisper-small
3. Intent parser:
   - "add X of Y to Z" → AddItem(quantity=X, material=Y, location=Z)
   - "remove item N" → DeleteItem(item_no=N)
   - "change quantity of item N to X" → UpdateItem(item_no=N, quantity=X)
   - Reuse NER pipeline for entity extraction in transcribed text
4. Action executor: applies intent to current BOQ
5. API endpoint: multipart upload audio → returns intent + result
6. React component: MediaRecorder API → POST audio → display

## 5. VERIFICATION
```bash
$ python3 -c "from src.voice.transcriber import Transcriber; t = Transcriber(); print(t.model_name)"
EXPECT: "whisper-small" or similar

$ python3 -c "from src.voice.intents import parse_intent; i = parse_intent('add 50 bags of cement to ground floor'); assert i['type'] == 'AddItem'"
EXPECT: no AssertionError

$ python3 -m pytest tests/unit/test_voice.py -v
EXPECT: ≥6 passed
```

## 6. ACCEPTANCE CRITERIA
- [ ] Transcription accuracy ≥80% on clear English speech
- [ ] Intent parser handles 4 intent types
- [ ] API gracefully rejects non-audio uploads
- [ ] Coverage ≥80% on new code (mocked)
- [ ] React component works on Chrome + Safari

## 7. CONSTRAINTS
- All imports `src.` prefix
- Audio file size limit 25MB
- Process voice synchronously, < 10s for short clips
- Confirm-before-commit pattern for destructive intents (Delete)

## 8. DEPENDENCIES
- **Blocked by:** S5 (React frontend)
- **Blocks:** None
- **Parallel-safe with:** B1, B2, B4, B5

## 9. GOTCHAS
- whisper-small: ~500MB model, downloaded on first use
- MediaRecorder API differs between browsers — test Chrome + Safari + Firefox
- Background noise on construction sites — accept lower transcription accuracy
- Hindi voice input: separate prompt; current scope is English only
