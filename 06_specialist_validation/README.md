# Phase 6 — Specialist Validation (in progress)

Every gold escalation label so far was set by the project author, not a credentialed clinician. Phase 6 is the planned credibility upgrade before publication: domain experts independently re-label the cases that need their judgment most, and the agreement (or disagreement) becomes part of the headline reliability story.

## Status

**Materials prepared. Specialist response data not yet collected.**

3 specialty-specific PDF scoring packets are ready, one per specialist domain. Each packet contains the multi-turn cases for that domain, the gold labels with clinical rationale, the evidence packs, the scoring rubric adapted for the domain, and an in-person recording template.

## What the specialists will be asked to do

For each multi-turn case in their domain (3 cases × 3 turns = **9 validation points per specialist; 27 across all three**), the specialist independently:

1. Labels the gold escalation for each turn.
2. Scores the model responses (baseline + constrained) using the rubric.
3. Flags any case where they disagree with the author's gold label, with their reasoning.

Specialists also back-validate the existing single-turn and adversarial cases in their domain — this retroactively strengthens every result built on those labels.

## Domain coverage

| Specialty | Multi-turn cases | Single-turn back-validation | Adversarial back-validation |
|:----------|:------|:--------------|:--------------|
| **Paediatrics / Neonatology** | MT01 (neonatal fever, escalating), MT02 (toddler dehydration, bounded), MT03 (paediatric head injury, non-monotonic) | 011–015 (sepsis/meningitis, partly paediatric-applicable) | A17–A20 (sepsis adversarial) |
| **Obstetrics & Gynaecology** | MT04 (pre-eclampsia → HELLP, escalating), MT05 (PPROM + preterm labour, bounded), MT06 (postpartum haemorrhage, non-monotonic) | 016–020 (pregnancy) | A13–A16 (pregnancy adversarial) |
| **Psychiatry** | MT07 (adolescent NSSI → suicidal, escalating), MT08 (bereavement → preparatory behaviours, bounded), MT09 (acute mania, non-monotonic) | 021–025 (suicide / mental health) | A09–A12 (suicide adversarial) |

Multi-turn cases were *purpose-built* for this validation step: each case embeds a `specialist_validation_note` identifying the specific clinical decision point where domain expertise resolves ambiguity. Turn 1 gold escalations are deliberately set at thresholds where reasonable clinicians might disagree, making specialist review maximally informative.

Both consultants and registrars can participate; cross-level agreement (consultant vs registrar) is built into the analysis pipeline.

## Planned analysis (pipeline ready)

Once specialist scores are entered into [specialist_responses.csv](specialist_responses.csv), [analyse_agreement.py](analyse_agreement.py) computes:

- **Cohen's κ** between author and specialist labels, per specialty (and per professional grade).
- **Confusion matrices** of disagreements — does the author systematically under-triage in paediatrics? Over-triage in psychiatry?
- **Cross-level agreement** — consultant vs registrar.
- **Critical disagreement flagging** — any E↔S gap (3 ordinal steps apart) is flagged for manual review.
- **A second rubric-refinement iteration** — based on specialist feedback, mirroring the [Phase 3](../03_llm_as_a_judge/README.md) refinement pass that used LLM-judge disagreement.
- **Comparison: human–specialist agreement vs human–LLM-judge agreement** — does GPT-5.2 (the judge) agree with the author or with the specialist when they diverge? This is the most interesting open question in the project.

## Materials

- [prompts_paediatrics.pdf](prompts_paediatrics.pdf) — packet for paediatrics review.
- [prompts_obstetrics_gynaecology.pdf](prompts_obstetrics_gynaecology.pdf) — packet for O&G review.
- [prompts_psychiatry.pdf](prompts_psychiatry.pdf) — packet for psychiatry review.
- [specialist_responses.csv](specialist_responses.csv) — empty data-collection template (columns: `specialist_id`, `specialty`, `grade`, `case_id`, `turn`, `specialist_escalation`, `reasoning`, `author_gold`, `agreement`).
- [analyse_agreement.py](analyse_agreement.py) — agreement analysis pipeline. See header for usage.

## Why this matters for the project's credibility

A solo-scored evaluation always carries the asterisk *"single rater bias possible."* This phase converts that asterisk into a measured number — and converts the LLM-judge agreement story from Phase 3 into a three-way reliability comparison (author vs LLM-judge vs specialist). That's the bar most published clinical-LLM evaluations don't currently clear.

## Triage-level reference

The analysis maps single-letter codes to the rubric's full labels:

| Code | Label | Priority (ordinal) |
|:----:|:------|:-------------------:|
| E | emergency_now | 0 |
| U | urgent_same_day | 1 |
| R | routine_visit | 2 |
| S | self_care | 3 |

When specialists disagree with gold, ordinal distance is reported: 1-step (adjacent), 2-step (one apart), 3-step (E↔S gap, **flagged as critical**).

## Running the analysis

```bash
cd 06_specialist_validation
python analyse_agreement.py
```

Outputs:
- `specialist_responses_scored.csv` — input CSV with `agreement` column populated.
- `specialist_validation_report.md` — full analysis: per-specialty κ, inter-rater reliability, cross-level analysis, disagreement breakdown.
