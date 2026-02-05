# Clinical Evals

## Start here
- **Read the results:** [Final report (PDF)](./reports/final_report.pdf)
- **See concrete failures + deltas:** [Case gallery](./reports/scored_case_gallery.md)
- **Where this goes next:** [WHAT_NOW roadmap](./WHAT_NOW.md)

## 30-second pitch
This repo is a small clinical safety evaluation harness to practice the exact job I’m aiming for: **measuring whether a model under-triages or gives unsafe guidance in high-risk presentations**.

- 30 curated synthetic cases across 6 buckets (chest pain, stroke, sepsis/meningitis, pregnancy, meds, suicide)
- Baseline vs constrained prompting
- Manual scoring for safety, grounding, uncertainty, actionability + hard-fail
- Printable scoring packet + final report summarizing failure modes and deltas

It’s an MVP, but already usable for iterating toward a real evaluation suite (adversarial variants, multi-turn cases, specialist gold labels, automated checks).

This repository is a lightweight evaluation harness for clinical conversation safety and escalation behavior. It runs a fixed set of synthetic cases through baseline and constrained prompts, then prepares outputs for manual scoring and reporting. The goal is to test safety-focused response behavior without making medical recommendations.

## What It Measures
- Safety (avoids harmful guidance, prioritizes escalation when needed)
- Escalation correctness (matches expected urgency)
- Grounding to evidence bullets (for constrained runs)
- Uncertainty vs. overconfidence
- Actionability of next steps

## Ethics And Limitations
- Synthetic scenarios only
- Not medical advice and not for clinical use
- Evaluation harness only; no diagnosis or treatment

## Setup (Mac)
```bash
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Fill in `.env` with `MODEL_NAME`, `OPENAI_API_KEY`, and `RUN_TAG`. The current workflow is still a dry-run (no model calls).

## How To Run (MVP)
```bash
python -m src.run_eval
python -m src.make_scoring_template
python -m src.report
```

## Outputs
- `outputs/model_outputs.jsonl`
- `scoring/scoring_template.csv`
- `reports/summary.md`

## What now?
Roadmap: [WHAT_NOW.md](./WHAT_NOW.md)

## Results
- [Final report (PDF)](./reports/final_report.pdf)
- [Case gallery (selected examples)](./reports/scored_case_gallery.md)
- [Score summary](./reports/scored_summary.md)
