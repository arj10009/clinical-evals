# Phase 1 — Single-Turn Evaluation

The starting question: **does prompt-level constraint matter more than raw model capability for clinical safety?**

## Setup

30 synthetic clinical cases were written across 5 medical buckets — chest pain, stroke, sepsis/meningitis, pregnancy, suicide & mental health, plus a medications/overdose bucket — covering a mix of HIGH-risk and MEDIUM-risk presentations. Each case has a single correct escalation level out of four:

| Code | Level | Meaning |
|:----:|:------|:--------|
| E | emergency_now | Call emergency services. Do not drive. |
| U | urgent_same_day | Same-day clinician — walk-in or urgent care. |
| R | routine_visit | See a doctor when you can. |
| S | self_care | Manageable at home. |

Three models were each run **twice** per case — once with a plain "respond like a clinician" prompt (**baseline**), once with evidence bullets, a strict E/U/R/S output schema, no-diagnosis/no-treatment guardrails, and a safety-first style rule (**constrained**). Three models × two conditions × 30 cases = **180 outputs**, all manually scored by the project author against a five-dimension rubric (safety, grounding, actionability, uncertainty, hard fail). The rubric is in [METHODOLOGY.md](../METHODOLOGY.md).

## Headline result

| Model | Condition | Composite | Safety | Hard Fail Rate | HIGH-Risk Under-Triage |
|:------|:----------|:---------:|:------:|:--------------:|:----------------------:|
| Llama 3.1:8b | baseline | 1.442 | 0.900 | 36.7% | 55.6% |
| Llama 3.1:8b | constrained | 1.550 | 1.433 | 26.7% | 16.7% |
| GPT-4.1-mini | baseline | 1.558 | 1.100 | 20.0% | 33.3% |
| **GPT-4.1-mini** | **constrained** | **1.842** | **1.767** | **3.3%** | **0%** |
| GPT-5.2 | baseline | 1.700 | 1.467 | 6.7% | 11.1% |
| GPT-5.2 | constrained | 1.750 | 1.633 | 6.7% | 0% |

The mid-tier model, properly constrained, beats the frontier model running unconstrained on every safety axis. **0%** under-triage on emergencies for GPT-4.1-mini constrained. The constraint isn't dressing — it does the work that capability alone won't.

## Per-model results

| Model | Final report | Case gallery | Summary | Raw outputs |
|:------|:-------------|:-------------|:--------|:------------|
| Llama 3.1:8b | [final_report.md](llama3_1_8b/final_report.md) | [scored_case_gallery.md](llama3_1_8b/scored_case_gallery.md) | [scored_summary.md](llama3_1_8b/scored_summary.md) | [model_outputs.jsonl](llama3_1_8b/model_outputs.jsonl) |
| GPT-4.1-mini | [final_report.md](gpt4_1_mini/final_report.md) | [scored_case_gallery.md](gpt4_1_mini/scored_case_gallery.md) | [scored_summary.md](gpt4_1_mini/scored_summary.md) | [model_outputs.jsonl](gpt4_1_mini/model_outputs.jsonl) |
| GPT-5.2 | [final_report.md](gpt5_2/final_report.md) | [scored_case_gallery.md](gpt5_2/scored_case_gallery.md) | [scored_summary.md](gpt5_2/scored_summary.md) | [model_outputs.jsonl](gpt5_2/model_outputs.jsonl) |

## Cross-model comparison

[cross_model_comparison.md](cross_model_comparison.md) — capability-vs-constraint analysis, per-bucket safety breakdowns, hard fail overlap, escalation accuracy across all six conditions.

A consolidated PDF of the per-model reports for printing/sharing: [reports_all_models.pdf](reports_all_models.pdf).

## Re-running

```bash
python -m src.run_eval                            # generates outputs/model_outputs.jsonl
python -m src.run_reports 01_single_turn/<model>  # after manual scoring
python -m src.generate_cross_model_comparison     # writes cross_model_comparison.md
```

## What this phase doesn't tell you

A clean test set says nothing about messy reality (→ [Phase 2](../02_adversarial_prompting/README.md)) or how trustworthy a single human scorer is (→ [Phase 3](../03_llm_as_a_judge/README.md)).
