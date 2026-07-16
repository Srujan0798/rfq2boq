# Validation Checklist (YOU run this after each agent returns)

```bash
cd /Users/srujansai/Desktop/rfq2boq

# 1. Check nothing unexpected changed
git status --short
# Should only show files the agent was supposed to modify

# 2. Check gold files were NOT modified (for Tasks 1 and 3)
git diff --name-only | grep "data/real_rfqs/gold"
# Should be EMPTY for Tasks 1 and 3
# For Task 2, ONLY swa_01_gsecl and swa_02_isro should show

# 3. Run tests
make verify
# MUST pass

# 4. Run evaluation
python3 scripts/eval_honest.py

# 5. Check the specific file they fixed
# Task 1:
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/04_adani/BOQ PAGE2adani proj.pdf'); print(f'Items: {len(r.boq_items)}'); [print(f'  {row.material[:50]}') for row in r.boq_items]"

# Task 2:
python3 scripts/eval_honest_rows.py

# Task 3:
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/06_avante_kirloskar_pune/Insulation Boq_132.pdf'); print(f'Items: {len(r.boq_items)}')"
python3 -c "from src.pipeline import Pipeline; p=Pipeline(); r=p.run('data/real_rfqs/swa_enquiries/07_grew_solar_narmadapuram/108, BOQ compliance, Grew Energy.pdf'); print(f'Items: {len(r.boq_items)}')"
```

## Reject Criteria

If ANY of these fail, REJECT the agent's work:
- `make verify` fails
- Gold files were modified (for Tasks 1, 3)
- Agent claims 100% but can't show eval output
- True positives decreased (recall dropped)
- `git status` shows files not related to the task

## Accept Criteria

If ALL pass:
```bash
git add -A
git commit -m "fix: [task description]"
```
Then move to next task.
