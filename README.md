# Clinical Evals — Can a smaller model, properly constrained, beat a frontier one on clinical safety?

> *Not medical advice. Synthetic scenarios only. This is an evaluation harness, not a clinical product.*

---

## The premise

A patient is messaging a clinical chatbot. They're sweating, their chest hurts, they're "just checking" before they go to bed. The model has one job that matters: don't tell them to sleep it off.

Most evaluation work on clinical LLMs is some flavour of "is the bigger model better?" That framing skips the question that actually decides whether a system is safe to deploy: **how much of safety is capability, and how much is the prompt?** If the answer is "mostly the prompt," then a cheaper model with the right guardrails is not a compromise — it's the design.

This project tested that hypothesis on 30 synthetic cases, then beat on it with adversarial framings, multi-turn trajectories, automated detectors, an LLM-as-a-judge for inter-rater reliability, five iterative patches, and (in progress) credentialed specialist validation.

The headline:

> **A constrained mid-tier model (GPT-4.1-mini) beat an unconstrained frontier model (GPT-5.2) on every safety metric measured. The result held under adversarial pressure. The constraint is doing the work.**

---

## The setup in 30 seconds

- **30 synthetic cases**, 5 medical buckets (chest pain, stroke, sepsis/meningitis, pregnancy, suicide/mental health, plus medications/overdose), each case labeled with a single correct escalation: emergency_now (E) / urgent_same_day (U) / routine_visit (R) / self_care (S).
- **3 models**: Llama 3.1:8b, GPT-4.1-mini, GPT-5.2.
- **2 prompt conditions per model**: a plain "respond like a clinician" baseline, and a *constrained* prompt with evidence bullets, a strict E/U/R/S output schema, no-diagnosis/no-treatment guardrails, and a safety-first style rule.
- **5-dimension manual rubric**: safety, grounding, actionability, uncertainty, hard fail. Refined later in [Phase 3](03_llm_as_a_judge/README.md) using LLM-judge disagreement analysis.

Full details in [METHODOLOGY.md](METHODOLOGY.md).

---

## Headline finding (single-turn, 30 cases)

| Model | Condition | Composite | Safety | Hard Fail Rate | HIGH-Risk Under-Triage |
|:------|:----------|:---------:|:------:|:--------------:|:----------------------:|
| Llama 3.1:8b | baseline | 1.442 | 0.900 | 36.7% | 55.6% |
| Llama 3.1:8b | constrained | 1.550 | 1.433 | 26.7% | 16.7% |
| GPT-4.1-mini | baseline | 1.558 | 1.100 | 20.0% | 33.3% |
| **GPT-4.1-mini** | **constrained** | **1.842** | **1.767** | **3.3%** | **0%** |
| GPT-5.2 | baseline | 1.700 | 1.467 | 6.7% | 11.1% |
| GPT-5.2 | constrained | 1.750 | 1.633 | 6.7% | 0% |

GPT-4.1-mini constrained: **0% under-triage on emergencies**. GPT-5.2 baseline: 11.1%. The cheaper model with the better prompt is the safer model.

The temptation is to read this as "constraint always wins." It's narrower than that: when the constraint encodes the right *medical* intuition (escalate on red flags, no diagnosis, mandatory emergency phrase, no off-ramps), capability buys you decreasing returns. When the constraint is wrong, capability can't save you — which is the next part of the story.

---

## How the story unfolds

### [Phase 1 — Single-Turn](01_single_turn/README.md)

The clean test set. 180 outputs, manually scored. Establishes the result above.

### [Phase 2 — Adversarial Prompting](02_adversarial_prompting/README.md)

Real patients don't write clean cases. 24 adversarial variants — symptom burial, confident minimizers, care refusal, authority override, plausible alternatives, social manipulation — were thrown at the two best contenders. **The constraint advantage held.** GPT-4.1-mini constrained beat GPT-5.2 baseline by +29.2 points on adversarial accuracy and -45 points on HIGH-risk under-triage.

The interesting part was where it *didn't* hold: a cluster of sepsis cases (fever + rigors) that both constrained models systematically failed. The cause wasn't the model — it was a missing rule in the constrained-mode evidence bullets. After patching the bullet, all four cases were correctly escalated. The lesson stuck: **constrained prompts inherit the blind spots of their evidence packs.** This is the kind of failure capability doesn't fix.

### [Phase 3 — LLM as a Judge (rubric refinement)](03_llm_as_a_judge/README.md)

A solo-scored evaluation has a credibility ceiling. So GPT-5.2 was given the same rubric the human had used and asked to re-score every output across 198 outputs. Cohen's κ was computed per dimension. Where κ was low, the rubric was rewritten and the judge re-run.

Actionability κ went from **0.286 to 0.463** (Fair to Moderate). Hard fail κ went **0.198 to 0.423** (Slight to Fair). For the GPT-4.1-mini adversarial set, hard-fail κ reached **0.765** (Substantial). The rubric isn't "trust me" any more — there's a measured second rater, and the points where the two raters disagree are mapped.

### [Phase 4 — Multi-Turn](04_multi_turn/README.md)

Single-turn tests sensitivity. It does not test **calibration**. A model that shouts "EMERGENCY" at every patient passes a sensitivity test and fails the deployment test (alert fatigue, ignored alarms, real harm).

So 9 multi-turn cases × 3 turns each were built across three deliberate trajectory types: emergencies that *unfold* (Type A), worsening that stays *bounded* below the emergency threshold (Type B), and clinical pictures that *de-escalate* after professional review (Type C). The gold-label distribution mirrored realistic clinical work: 30% emergency, 41% urgent, 26% routine, 4% self-care — not a 100%-emergency stress test.

This phase surfaced two specific failure modes neither single-turn nor adversarial caught:

1. GPT-5.2 sometimes claimed it would "break confidentiality" or "contact parents" in psychiatry cases (a chatbot can do neither).
2. GPT-4.1-mini sometimes accepted "I have a GP appointment next week" as a valid reason to downgrade an urgent case to routine.

Both of these were patched in the next phase.

### [Phase 5 — Iterative Patching](05_iterative_patching/README.md)

Five targeted patches based on the multi-turn failures: chatbot-medium constraint (you cannot break confidentiality), future-appointment anti-downgrade rule, paediatric-adapted emergency phrase, context-aware unsafe-phrase detection, scorer-override mechanism.

Re-run. Re-detect. Manually spot-check 22 high-stakes outputs.

| Model | Pre-patch flags | Post-patch flags | Net |
|:------|:---------------:|:----------------:|:----|
| GPT-5.2 | 7 | 3 | -4 |
| **GPT-4.1-mini** | **2** | **0** | **clean sweep** |

GPT-4.1-mini constrained accuracy: 81.5% to 85.2%. Manual spot-check: **18/22 pass, zero regressions**. The 4 failures are residual pre-existing weaknesses (GPT-5.2 MT07 confidentiality framing, GPT-4.1-mini baseline vague-timeline weakness), not patch-induced.

The point isn't that the patches fixed everything. The point is that they fixed measurable failures **without introducing new ones**. That is the actual hard part of safety-critical evaluation.

### [Phase 6 — Specialist Validation (in progress)](06_specialist_validation/README.md)

The ceiling on this entire project's credibility is "one author, scoring synthetic cases against a self-written rubric." Specialist validation pierces it. Three specialty packets are prepared (paediatrics, O&G, psychiatry — each containing 3 multi-turn cases × 3 turns = 9 validation points; 27 total), with the analysis pipeline ready to compute Cohen's κ per specialty, cross-level agreement (consultant vs registrar), confusion matrices, and — most interestingly — a **three-way reliability comparison**: does the LLM-judge agree with the author or with the specialist when they diverge?

This is the work that converts the project from "rigorous evaluation" to "publishable methodology."

---

## The repo, in narrative order

| | Folder | What's inside |
|:-:|:-------|:--------------|
| 1 | [`01_single_turn/`](01_single_turn/) | 30-case eval, 3 models × 2 conditions, scored gallery + cross-model report |
| 2 | [`02_adversarial_prompting/`](02_adversarial_prompting/) | 24 adversarial variants, 6 attack types, sepsis evidence-pack patch |
| 3 | [`03_llm_as_a_judge/`](03_llm_as_a_judge/) | 198-output IRR analysis, κ tables, rubric-refinement diff |
| 4 | [`04_multi_turn/`](04_multi_turn/) | 9 cases × 3 turns × 3 trajectory types — calibration, not just sensitivity |
| 5 | [`05_iterative_patching/`](05_iterative_patching/) | 5 patches, before/after auto-detection, manual spot-check (zero regressions) |
| 6 | [`06_specialist_validation/`](06_specialist_validation/) | Specialist packets ready; data collection in progress |

Plus the supporting infrastructure:

- [`data/`](data/) — case sets (`cases.csv`, `adversarial_cases.csv`, `multiturn_cases.csv`) and evidence packs.
- [`src/`](src/) — eval runners (single-turn, adversarial, multi-turn), detectors, LLM-judge, agreement analysis, cross-model comparison generator.
- [`METHODOLOGY.md`](METHODOLOGY.md) — full scoring rubric, case design, prompt construction, multi-turn design, specialist validation design, known limitations.

---

## What I'd do next

1. **Collect the specialist data and run the agreement pipeline.** This is the publication blocker.
2. **Scale the suite.** 30 cases finds patterns; it does not produce statistical power. The path is: more cases written under the same rubric, run automated detectors + LLM-judge as first-pass scoring, reserve human review for the flagged subset.
3. **Stratified metrics**, not averages. Report by risk level, by bucket, by failure type, by presentation style — not just composite scores. A model that "averages well" while failing catastrophically on the cases that matter is the failure mode evaluation work is supposed to catch.

---

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in MODEL_NAME, OPENAI_API_KEY, RUN_TAG in .env
```

## Common commands

```bash
# Single-turn eval (uses RUN_TAG from .env)
python -m src.run_eval

# Adversarial eval
python -m src.run_adversarial

# Multi-turn eval
DRY_RUN=0 python -m src.run_multiturn_eval

# Automated detection
python -m src.auto_detect --model gpt5_2
python -m src.auto_detect_multiturn --model gpt5_2

# LLM-as-judge scoring
python -m src.llm_judge --model gpt5_2
python -m src.llm_judge_multiturn --model gpt5_2

# Cohen's κ across all combos
python -m src.judge_agreement --all

# Per-run reports (after manual scoring)
python -m src.run_reports 01_single_turn/<model>

# Cross-model comparison
python -m src.generate_cross_model_comparison

# Specialist agreement analysis
cd 06_specialist_validation && python analyse_agreement.py
```

---

## Ethics & limitations

- All cases are **synthetic** — no real patient data.
- This is an evaluation harness, **not** medical advice and **not** for clinical use.
- Single-rater manual scoring, validated with LLM-as-judge inter-rater reliability (Cohen's κ ranges from 0.2 to 0.5 by metric pre-refinement; 0.4 to 0.77 post-refinement on the dimensions where it was retested).
- 30-case sample is directional, not statistically powered.
- Specialist validation is the planned credibility upgrade, not yet collected.
- English only.

The project's design takes these limitations seriously: every limitation has a planned mitigation, and most of those mitigations are already implemented or in flight.
