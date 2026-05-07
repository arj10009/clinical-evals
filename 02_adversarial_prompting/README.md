# Phase 2 — Adversarial Prompting

Phase 1 produced a clean result on clean cases. Real patients don't write clean cases. Phase 2 asked: **does the constraint advantage survive when the prompt is actively trying to mislead the model?**

## Setup

24 adversarial variants across 6 attack types, all derived from realistic-but-tricky framings of underlying HIGH-risk presentations:

| Attack type | What it does |
|:------------|:-------------|
| **Symptom burial** | Critical red flags hidden mid-paragraph among irrelevant noise — tests context tracking. |
| **Confident minimizer** | "I feel fine, just checking" while describing classic emergency symptoms. |
| **Care refusal** | "I don't want to go to hospital" — tests whether the model still escalates. |
| **Authority override** | "I'm a doctor / nurse, I'll monitor at home" — tests resistance to credentialed framing. |
| **Plausible alternative** | A tempting innocuous diagnosis (reflux, anxiety, migraine) layered onto a real emergency. |
| **Social manipulation** | "I can't afford it" / "I have nobody to pick up my son" — tests whether social cost overrides safety. |

Two models were tested under both conditions on all 24 variants: **GPT-4.1-mini** and **GPT-5.2** (the constraint-vs-capability matchup that mattered after Phase 1). Llama 3.1:8b raw outputs are also stored locally but were never manually scored — the gap to the frontier was already established.

## Headline result

| Model | Condition | Adversarial Accuracy | Hard Fail Rate | HIGH Under-Triage |
|:------|:----------|:-------------------:|:--------------:|:-----------------:|
| GPT-4.1-mini | baseline | 45.8% | 58.3% | 50.0% |
| **GPT-4.1-mini** | **constrained** | **75.0%** | **16.7%** | **10.0%** |
| GPT-5.2 | baseline | 45.8% | 33.3% | 55.0% |
| GPT-5.2 | constrained | 66.7% | 4.2% | 20.0% |

Constraint advantage survives under adversarial pressure. GPT-4.1-mini constrained beats GPT-5.2 baseline by **+29.2% accuracy** and **−45 points on HIGH-risk under-triage**. The 100-point safety gap from Phase 1 isn't fragile — it shows up under stress too.

## A surprise: the sepsis evidence-pack gap

Even constrained, both models systematically failed on a cluster of sepsis cases (A17–A20: fever + rigors + tachycardia). The cause wasn't the model — it was a missing rule in the constrained-mode evidence pack: nothing told the model that fever-with-rigors should escalate. After patching the evidence bullet ([sepsis_patch_report_20260209.md](gpt5_2/sepsis_patch_report_20260209.md)), all four cases were correctly escalated. The lesson: constrained prompts inherit the blind spots of their evidence packs. A failure that looks like a model failure can be a prompt-engineering failure.

## Reports & artifacts

- [adversarial_report.md](adversarial_report.md) — full results, per-attack-type breakdowns, scoring tables.
- [cross_model_adversarial_comparison.md](cross_model_adversarial_comparison.md) — does the constraint advantage hold? (Yes.)
- [gpt5_2/analysis/failure_packet_sepsis_high_risk.md](gpt5_2/analysis/failure_packet_sepsis_high_risk.md) — root-cause analysis of the sepsis cluster.
- Per-model run folders: [gpt4_1_mini/](gpt4_1_mini/) | [gpt5_2/](gpt5_2/) — raw outputs, scored CSVs, auto-detection flags, LLM-judge scores.

## Re-running

```bash
python -m src.run_adversarial                                 # uses RUN_TAG from .env
python -m src.auto_detect --model <tag> --adversarial
python -m src.analyze_adversarial_scores --model <tag>
python -m src.analyze_adversarial_deltas --model <tag>
python -m src.make_failure_packet --model <tag>
```
