# Phase 3 — LLM as a Judge (Inter-Rater Reliability + Rubric Refinement)

Single-rater scoring is a known weakness in evaluation work. Phase 3 turned that weakness into a feature: have a frontier model independently re-score every output using the same rubric, treat agreement as a measure of rubric quality, and rewrite the rubric where the disagreements concentrate.

## What was done

1. **Automated rule-based detectors** were built for the four obvious-bad behaviors that don't need a human eye: under-triage on emergency cases, unsafe branching ("urgent care or ER or GP" as co-equal options), missing the mandatory emergency phrase under constrained mode, and grounding violations against evidence bullets. These flag candidates for review at scale (see `auto_flags.csv` in each per-model folder).
2. **GPT-5.2 was used as an LLM-as-a-judge** to re-score every output across 5 dimensions (safety, grounding, actionability, uncertainty, hard fail), independently of the human scorer. The judge was given the same rubric the human used.
3. **Cohen's κ** was computed between human and judge for each dimension across 198 outputs. Where κ was weak, the rubric was rewritten — sharper anchors, clearer thresholds, explicit examples of borderline cases.
4. **The judge was re-run** with the refined rubric and the κ recomputed.

## Headline result

The rubric refinement was the load-bearing contribution. Across 198 outputs:

| Dimension | κ before | κ after | Change | Interpretation |
|:----------|:--------:|:-------:|:------:|:---------------|
| Actionability | 0.286 | 0.463 | **+0.177** | Fair → Moderate |
| Hard fail | 0.198 | 0.423 | **+0.225** | Slight → Fair |
| Safety | 0.412 | 0.448 | +0.036 | Moderate (sharpened) |
| Grounding | — | (mixed) | — | per-condition variance |
| Uncertainty | — | (mixed) | — | per-condition variance |

For the GPT-4.1-mini adversarial set specifically, hard-fail κ reached **0.765 (Substantial)** after refinement. The core finding from Phase 1 is being scored consistently — by a human and by an independent model rater — once the rubric was sharp enough.

## What this means for the project's reliability story

The rubric isn't just one person's opinion. Two raters (a human and a strong LLM) now agree to a measurable degree, and the points where they don't agree are mapped. Combined with the upcoming specialist validation ([Phase 6](../06_specialist_validation/README.md)), this gives a multi-method reliability story rather than "trust me, I scored carefully."

## Artifacts

- [synthesis_report.md](synthesis_report.md) — the full Phase 3 writeup. Methodology, κ tables per dimension, disagreement analysis, rubric refinement diff, scaling-strategy recommendations.
- The per-model judge scores and agreement reports live alongside each phase's run artifacts (so each `model_outputs.jsonl` sits next to its `llm_judge_scores.csv` and `llm_judge_agreement.md`):
  - Single-turn: [gpt5_2](../01_single_turn/gpt5_2/llm_judge_agreement.md), [gpt4_1_mini](../01_single_turn/gpt4_1_mini/llm_judge_agreement.md), [llama3_1_8b](../01_single_turn/llama3_1_8b/llm_judge_agreement.md)
  - Adversarial: [gpt5_2](../02_adversarial_prompting/gpt5_2/llm_judge_agreement.md), [gpt4_1_mini](../02_adversarial_prompting/gpt4_1_mini/llm_judge_agreement.md)

## Re-running

```bash
python -m src.auto_detect --model gpt5_2                      # rule-based flags
python -m src.auto_detect_multiturn --model gpt5_2
python -m src.llm_judge --model gpt5_2                        # judge re-scores
python -m src.llm_judge --model gpt5_2 --adversarial
python -m src.llm_judge_multiturn --model gpt5_2
python -m src.judge_agreement --all                           # κ tables, per-dim agreement
```
