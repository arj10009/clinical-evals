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

### Per-model results
- **Llama 3.1 8B:** [Final Report](./runs/llama3_1_8b/final_report.md) | [Case Gallery](./runs/llama3_1_8b/scored_case_gallery.md) | [Summary](./runs/llama3_1_8b/scored_summary.md)
- **GPT-4.1-mini:** [Final Report](./runs/gpt4_1_mini/final_report.md) | [Case Gallery](./runs/gpt4_1_mini/scored_case_gallery.md) | [Summary](./runs/gpt4_1_mini/scored_summary.md)
- **GPT-5.2:** [Final Report](./runs/gpt5_2/final_report.md) | [Case Gallery](./runs/gpt5_2/scored_case_gallery.md) | [Summary](./runs/gpt5_2/scored_summary.md)

Each run folder also contains `model_outputs.jsonl` (raw responses) and `scored_results.csv` (manually scored).

### Cross-model comparison
- [Cross-model report](./cross_model/cross_model_report.md) — capability vs. constraint analysis, per-bucket safety breakdowns, hard fail overlap, escalation accuracy

### Adversarial evaluation (24 cases)
- [Adversarial report](./runs/adversarial/adversarial_report.md) — 24 adversarial variants across 6 attack types, scored for GPT-5.2 and GPT-4.1-mini
- [Cross-model adversarial comparison](./runs/adversarial/cross_model_adversarial_comparison.md) — does the constraint advantage survive adversarial pressure?
- [Sepsis evidence gap analysis](./runs/adversarial/gpt5_2/analysis/failure_packet_sepsis_high_risk.md) — root cause analysis of systematic constrained failure

### Methodology
- [METHODOLOGY.md](./METHODOLOGY.md) — full scoring rubric, case design, prompt construction, known limitations

---

## Repo structure

- `data/` — case set (`cases.csv`), adversarial cases (`adversarial_cases.csv`), and evidence bullets (`evidence_packs.json`)
- `src/` — evaluation harness, adversarial runner, analysis scripts, and reporting
- `runs/<model>/` — per-model run artifacts (outputs, scores, reports)
- `runs/adversarial/<model>/` — adversarial variant results and analysis
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
# Run evaluation
python -m src.run_eval

# Generate per-run reports (after manual scoring)
python -m src.run_reports runs/<run_folder>

# Generate cross-model comparison
python -m cross_model.generate_comparison
```

## Roadmap

See [WHAT_NOW.md](./WHAT_NOW.md) — next steps include automated under-triage detection, multi-turn cases, and specialist gold labels.

## Ethics and Limitations

- All cases are synthetic — not real patient data
- Not medical advice and not for clinical use
- Single-rater manual scoring (inter-rater reliability planned)
- 30-case sample size is directional, not statistically powered
