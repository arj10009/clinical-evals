# Phase 4 — Multi-Turn Evaluation

Single-turn cases test sensitivity: does the model catch an emergency? They don't test **calibration**: does the model know when *not* to escalate? A model that shouts "EMERGENCY" at every patient is useless in practice — alert fatigue kills people. Phase 4 was designed around that failure mode.

## Setup

9 multi-turn cases × 3 turns each = **27 turns, 54 outputs per model**, deliberately spread across three trajectory types so that a "shout EMERGENCY at everything" strategy fails:

| Type | Cases | What it tests |
|:-----|:------|:--------------|
| **A — Escalate to emergency** | MT01, MT04, MT07 | Risk worsens to `emergency_now` across turns. Does the model catch genuine emergencies unfolding? |
| **B — Bounded worsening** | MT02, MT05, MT08 | Symptoms get worse but never cross the emergency line. Does the model resist over-escalation? |
| **C — Non-monotonic** | MT03, MT06, MT09 | New information *reduces* risk after professional medical review. Does the model de-escalate when warranted, or stick to its prior alarm? |

Cases were also aligned to **three specialist domains** for [Phase 6](../06_specialist_validation/README.md) — paediatrics (MT01–MT03), obstetrics & gynaecology (MT04–MT06), psychiatry (MT07–MT09). Gold-label distribution across all 27 turns: emergency_now 30%, urgent_same_day 41%, routine_visit 26%, self_care 4% — a realistic mix, not an emergency-loaded test set.

Two new scoring dimensions were added on top of the standard 5: **context integration** (does the model update on new information?) and **escalation consistency** (is the trajectory clinically defensible?). Three new automated detectors were added: escalation flip-flop, delayed escalation, final-turn mismatch.

## Headline result (pre-patch)

GPT-4.1-mini constrained: 81.5% escalation accuracy across all 27 turns, safety κ vs LLM-judge = 0.49, escalation-consistency κ = 0.58 — both Moderate. Both models cleanly caught Type A emergencies but stumbled in different ways: GPT-5.2 sometimes claimed it would "break confidentiality" or "contact parents" in psychiatry cases (a chatbot can't do either), and GPT-4.1-mini sometimes accepted "I have a GP appointment next week" as a valid reason to downgrade `urgent_same_day` to `routine_visit`. These observed failures drove the patches in [Phase 5](../05_iterative_patching/README.md).

## What this phase changed about the rubric

Multi-turn surfaced calibration failures that single-turn cases couldn't: holding a correct emergency call when the patient pleads cost, refusing to downgrade on a future appointment, distinguishing "the patient is reassured" (not a valid downgrade reason) from "the patient was clinically reassessed by a professional" (a valid one). All three are now explicit in the constrained prompt and the rubric.

## Reports & artifacts

- [multiturn_analysis.md](multiturn_analysis.md) — composite scores, safety, hard-fails, trajectory-type accuracy, confusion matrices, inter-rater reliability.
- [gpt5_2/case_gallery.md](gpt5_2/case_gallery.md) | [gpt4_1_mini/case_gallery.md](gpt4_1_mini/case_gallery.md) — turn-by-turn case galleries.
- Per-model run folders: `model_outputs.jsonl`, `scored_results.csv`, `auto_flags.csv`, `llm_judge_scores.csv`, `scoring_sheet.pdf`.

## Re-running

```bash
DRY_RUN=0 python -m src.run_multiturn_eval         # uses RUN_TAG from .env
python -m src.auto_detect_multiturn --model gpt5_2
python -m src.llm_judge_multiturn --model gpt5_2
```
