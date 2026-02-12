# Clinical Evals

A lightweight evaluation harness for **clinical conversation safety + escalation behavior** using a fixed set of 30 synthetic cases (baseline vs constrained prompting), manual scoring, and reporting.

> Not medical advice. Synthetic scenarios only. Evaluation harness only.

---

## Key Finding

**Constraint engineering on a mid-tier model outperforms a frontier model running without constraints.**

| Model | Condition | Composite | Safety | Hard Fail Rate | HIGH-Risk Under-Triage |
|:------|:----------|:---------:|:------:|:--------------:|:----------------------:|
| Llama 3.1:8b | baseline | 1.442 | 0.900 | 36.7% | 55.6% |
| Llama 3.1:8b | constrained | 1.550 | 1.433 | 26.7% | 16.7% |
| GPT-4.1-mini | baseline | 1.558 | 1.100 | 20.0% | 33.3% |
| **GPT-4.1-mini** | **constrained** | **1.842** | **1.767** | **3.3%** | **0%** |
| GPT-5.2 | baseline | 1.700 | 1.467 | 6.7% | 11.1% |
| GPT-5.2 | constrained | 1.750 | 1.633 | 6.7% | 0% |

GPT-4.1-mini with evidence-bullet constraints achieves the highest composite score and 0% under-triage on emergency cases, outperforming GPT-5.2 baseline across every safety metric.

### Adversarial Robustness

This finding holds under adversarial conditions. 24 adversarial variants (symptom burial, confident minimizers, care refusal, authority override, plausible alternatives, ambiguity injection) were tested on GPT-5.2 and GPT-4.1-mini:

| Model | Condition | Adversarial Accuracy | Hard Fail Rate | HIGH Under-Triage |
|:------|:----------|:-------------------:|:--------------:|:-----------------:|
| GPT-4.1-mini | baseline | 45.8% | 58.3% | 50.0% |
| **GPT-4.1-mini** | **constrained** | **75.0%** | **16.7%** | **10.0%** |
| GPT-5.2 | baseline | 45.8% | 33.3% | 55.0% |
| GPT-5.2 | constrained | 66.7% | 4.2% | 20.0% |

GPT-4.1-mini constrained outperforms GPT-5.2 baseline by +29.2% accuracy and −45.0% HIGH-risk under-triage under adversarial pressure. The evaluation also identified an evidence pack gap in sepsis (missing catch-all rule for fever with rigors), which was patched and validated.

---

## Start here (results)

### Per-model results (single-turn)
- **Llama 3.1 8B:** [Final Report](./runs/singleturn/llama3_1_8b/final_report.md) | [Case Gallery](./runs/singleturn/llama3_1_8b/scored_case_gallery.md) | [Summary](./runs/singleturn/llama3_1_8b/scored_summary.md)
- **GPT-4.1-mini:** [Final Report](./runs/singleturn/gpt4_1_mini/final_report.md) | [Case Gallery](./runs/singleturn/gpt4_1_mini/scored_case_gallery.md) | [Summary](./runs/singleturn/gpt4_1_mini/scored_summary.md)
- **GPT-5.2:** [Final Report](./runs/singleturn/gpt5_2/final_report.md) | [Case Gallery](./runs/singleturn/gpt5_2/scored_case_gallery.md) | [Summary](./runs/singleturn/gpt5_2/scored_summary.md)

Each run folder also contains `model_outputs.jsonl` (raw responses) and `scored_results.csv` (manually scored).

### Cross-model comparison
- [Cross-model report](./cross_model/cross_model_report.md) — capability vs. constraint analysis, per-bucket safety breakdowns, hard fail overlap, escalation accuracy

### Adversarial evaluation (24 cases)
- [Adversarial report](./runs/adversarial/adversarial_report.md) — 24 adversarial variants across 6 attack types, scored for GPT-5.2 and GPT-4.1-mini
- [Cross-model adversarial comparison](./runs/adversarial/cross_model_adversarial_comparison.md) — does the constraint advantage survive adversarial pressure?
- [Sepsis evidence gap analysis](./runs/adversarial/gpt5_2/analysis/failure_packet_sepsis_high_risk.md) — root cause analysis of systematic constrained failure

### Automated detection, rubric validation & refinement (Phase 3)
- [Phase 3 Synthesis Report](./runs/phase3_synthesis_report.md) — rule-based detectors + LLM-as-judge inter-rater reliability + rubric refinement based on disagreement analysis
- Per-model auto-detection: [GPT-5.2](./runs/singleturn/gpt5_2/auto_flags_summary.md) | [GPT-4.1-mini](./runs/singleturn/gpt4_1_mini/auto_flags_summary.md) | [Llama 3.1:8b](./runs/singleturn/llama3_1_8b/auto_flags_summary.md) | [GPT-4.1-mini adversarial](./runs/adversarial/gpt4_1_mini/auto_flags_summary.md) | [GPT-5.2 adversarial](./runs/adversarial/gpt5_2/auto_flags_summary.md)
- Per-model LLM judge agreement: [GPT-5.2](./runs/singleturn/gpt5_2/llm_judge_agreement.md) | [GPT-4.1-mini](./runs/singleturn/gpt4_1_mini/llm_judge_agreement.md) | [GPT-4.1-mini adversarial](./runs/adversarial/gpt4_1_mini/llm_judge_agreement.md) | [Llama 3.1:8b](./runs/singleturn/llama3_1_8b/llm_judge_agreement.md)

### Multi-turn evaluation (Phase 4 — scored and analysed)
- 9 specialist-aligned multi-turn cases across 3 trajectory types: escalate-to-emergency (3), stay-in-urgent/routine (3), non-monotonic with de-escalation (3)
- 3 turns each (27 turns total, 54 outputs per model) — gold label distribution: emergency_now 30%, urgent_same_day 41%, routine_visit 26%, self_care 4%
- Trajectory variability tests calibration, not just sensitivity: does the model catch emergencies AND resist over-escalation AND de-escalate appropriately after medical review?
- [Multi-turn Analysis](./runs/multiturn/multiturn_analysis.md) — composite scores, safety, hard fails, trajectory-type accuracy, confusion matrices, inter-rater reliability (safety κ=0.49, escalation consistency κ=0.58)
- Per-model results: [GPT-5.2 Case Gallery](./runs/multiturn/gpt5_2/case_gallery.md) | [GPT-4.1-mini Case Gallery](./runs/multiturn/gpt4_1_mini/case_gallery.md)

### Patch work (Phase 5 — complete)
- 5 targeted patches based on manual scoring failures: chatbot medium constraint (MT07), future appointment anti-downgrade (MT08), paediatric emergency phrase, context-aware unsafe phrase detection, scorer override integration
- Both models re-run with patched prompts (`v2_multiturn_patched`): GPT-5.2 and GPT-4.1-mini (54 outputs each)
- Auto-detection noise reduced: GPT-5.2 7→4 flags, GPT-4.1-mini 2→0 flags (clean sweep)
- GPT-4.1-mini constrained escalation accuracy improved: 81.5% → 85.2%
- Manual spot-check scoring: 18/22 pass (81.8%), zero regressions — all failures are pre-existing weaknesses or residual model-specific behaviour
- [Patch Comparison Report](./runs/patch_work/patch_comparison_report.md) — before/after analysis, auto-detection comparison, and manual scoring results
- [Scoring Analysis](./runs/patch_work/scoring_analysis.md) — detailed per-patch analysis with regression assessment
- Pre/post-patch baselines archived in `runs/patch_work/`
- See [METHODOLOGY.md](./METHODOLOGY.md) for full patch descriptions

### Methodology
- [METHODOLOGY.md](./METHODOLOGY.md) — full scoring rubric, case design, prompt construction, multi-turn design, specialist validation design, known limitations

---

## Repo structure

- `data/` — case sets (`cases.csv`, `adversarial_cases.csv`, `multiturn_cases.csv`), evidence bullets (`evidence_packs.json`, `evidence_packs_multiturn.json`)
- `src/` — evaluation harness, adversarial runner, multi-turn runner, analysis scripts, auto-detection, LLM-as-judge, and reporting
- `runs/singleturn/<model>/` — per-model single-turn run artifacts (outputs, scores, reports, auto-flags, LLM judge scores)
- `runs/adversarial/<model>/` — adversarial variant results and analysis
- `runs/multiturn/<model>/` — multi-turn evaluation results
- `runs/patch_work/` — pre-patch baselines and post-patch comparison artifacts
- `cross_model/` — cross-model comparison script and generated report

---

## Setup (Mac)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in MODEL_NAME, OPENAI_API_KEY, RUN_TAG in .env
```

## Running

```bash
# Run single-turn evaluation
python -m src.run_eval

# Run adversarial evaluation
python -m src.run_adversarial

# Run multi-turn evaluation
python -m src.run_multiturn_eval

# Run auto-detection
python -m src.auto_detect --model gpt5_2
python -m src.auto_detect_multiturn --model gpt5_2

# Run LLM-as-judge scoring
python -m src.llm_judge --model gpt5_2
python -m src.llm_judge_multiturn --model gpt5_2

# Compute judge agreement
python -m src.judge_agreement --all

# Generate per-run reports (after manual scoring)
python -m src.run_reports runs/<run_folder>

# Generate cross-model comparison
python -m cross_model.generate_comparison
```

## Roadmap

See [WHAT_NOW.md](./WHAT_NOW.md) — multi-turn evaluation scored and analysed, patch work implemented; next steps are re-running with patched prompts, specialist validation with domain experts (paediatrics, O&G, psychiatry), and scaling the suite.

## Ethics and Limitations

- All cases are synthetic — not real patient data
- Not medical advice and not for clinical use
- Single-rater manual scoring, validated with LLM-as-judge inter-rater reliability (Cohen's κ ranges from 0.2–0.5 by metric)
- 30-case sample size is directional, not statistically powered
