from __future__ import annotations

"""Compute inter-rater agreement between human scores and LLM judge scores.

Reads llm_judge_scores.csv files and computes:
  - Exact agreement rate per metric
  - Cohen's kappa per metric
  - Confusion matrices
  - Disagreement case listings

Usage:
    python -m src.judge_agreement --model gpt5_2
    python -m src.judge_agreement --model gpt4_1_mini --adversarial
    python -m src.judge_agreement --all   # runs on all available judge score files
"""

import argparse
import csv
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone


# ---------------------------------------------------------------------------
# Cohen's Kappa
# ---------------------------------------------------------------------------

def cohens_kappa(y_human: list[int], y_judge: list[int], labels: list[int]) -> float:
    """Compute Cohen's kappa for two raters.

    Returns kappa in [-1, 1]. 1 = perfect agreement, 0 = chance agreement.
    """
    n = len(y_human)
    if n == 0:
        return float("nan")

    # Build confusion matrix
    matrix = Counter()
    for h, j in zip(y_human, y_judge):
        matrix[(h, j)] += 1

    # Observed agreement
    p_o = sum(matrix[(l, l)] for l in labels) / n

    # Expected agreement by chance
    p_e = 0.0
    for l in labels:
        row_sum = sum(matrix[(l, j)] for j in labels)
        col_sum = sum(matrix[(h, l)] for h in labels)
        p_e += (row_sum / n) * (col_sum / n)

    if p_e == 1.0:
        return 1.0  # both raters agree on everything
    return (p_o - p_e) / (1.0 - p_e)


def confusion_matrix_str(y_human: list[int], y_judge: list[int], labels: list[int]) -> str:
    """Build a confusion matrix as a formatted string."""
    matrix = Counter()
    for h, j in zip(y_human, y_judge):
        matrix[(h, j)] += 1

    lines = []
    # Header
    header = "Human\\Judge | " + " | ".join(str(l) for l in labels) + " |"
    lines.append(header)
    lines.append("|" + "---|" * (len(labels) + 1))

    for h in labels:
        row = f"| **{h}** |"
        for j in labels:
            count = matrix.get((h, j), 0)
            row += f" {count} |"
        lines.append(row)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Kappa interpretation
# ---------------------------------------------------------------------------

def interpret_kappa(k: float) -> str:
    if k < 0:
        return "Poor (worse than chance)"
    elif k < 0.20:
        return "Slight"
    elif k < 0.40:
        return "Fair"
    elif k < 0.60:
        return "Moderate"
    elif k < 0.80:
        return "Substantial"
    else:
        return "Almost perfect"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_judge_scores(model: str, adversarial: bool) -> list[dict]:
    if adversarial:
        path = Path(f"02_adversarial_prompting/{model}/llm_judge_scores.csv")
    else:
        path = Path(f"01_single_turn/{model}/llm_judge_scores.csv")

    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def safe_int(v) -> int | None:
    try:
        return int(v)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

METRICS = ["safety", "grounding", "actionability", "uncertainty", "hard_fail"]
METRIC_LABELS = {
    "safety": [0, 1, 2],
    "grounding": [0, 1, 2],
    "actionability": [0, 1, 2],
    "uncertainty": [0, 1, 2],
    "hard_fail": [0, 1],
}


def analyze(rows: list[dict], model: str, adversarial: bool) -> str:
    """Run agreement analysis, return markdown report string."""
    tag = f"{model} ({'adversarial' if adversarial else 'original 30-case'})"
    lines = []
    lines.append(f"# LLM Judge Agreement Report — {tag}\n")
    lines.append(f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    lines.append(f"Judge model: GPT-5.2")
    lines.append(f"Total scored outputs: {len(rows)}\n")

    # Filter to rows where human scores exist
    valid = []
    for r in rows:
        h_scores = {m: safe_int(r.get(f"human_{m}")) for m in METRICS}
        j_scores = {m: safe_int(r.get(f"judge_{m}")) for m in METRICS}
        if all(v is not None for v in h_scores.values()) and all(v is not None for v in j_scores.values()):
            valid.append(r)

    lines.append(f"Valid comparisons (both human and judge scored): {len(valid)}\n")

    if not valid:
        lines.append("No valid comparisons found.\n")
        return "\n".join(lines)

    # --- Overall agreement table ---
    lines.append("## Overall Agreement\n")
    lines.append("| Metric | Exact Agreement | Cohen's Kappa | Interpretation |")
    lines.append("|--------|----------------|---------------|----------------|")

    for metric in METRICS:
        h_vals = [int(r[f"human_{metric}"]) for r in valid]
        j_vals = [int(r[f"judge_{metric}"]) for r in valid]
        labels = METRIC_LABELS[metric]

        exact = sum(1 for h, j in zip(h_vals, j_vals) if h == j)
        rate = exact / len(valid)

        kappa = cohens_kappa(h_vals, j_vals, labels)
        interp = interpret_kappa(kappa)

        lines.append(f"| {metric} | {exact}/{len(valid)} ({rate:.1%}) | {kappa:.3f} | {interp} |")

    lines.append("")

    # --- Confusion matrices ---
    lines.append("## Confusion Matrices\n")
    lines.append("Rows = Human score, Columns = Judge score\n")

    for metric in METRICS:
        h_vals = [int(r[f"human_{metric}"]) for r in valid]
        j_vals = [int(r[f"judge_{metric}"]) for r in valid]
        labels = METRIC_LABELS[metric]

        lines.append(f"### {metric.title()}\n")
        lines.append(confusion_matrix_str(h_vals, j_vals, labels))
        lines.append("")

    # --- Disagreement listings ---
    lines.append("## Disagreements\n")
    lines.append("Cases where human and judge gave different scores.\n")

    for metric in METRICS:
        disagreements = []
        for r in valid:
            h = int(r[f"human_{metric}"])
            j = int(r[f"judge_{metric}"])
            if h != j:
                disagreements.append({
                    "case_id": r["case_id"],
                    "condition": r["condition"],
                    "bucket": r.get("bucket", ""),
                    "risk": r.get("risk", ""),
                    "human": h,
                    "judge": j,
                    "reasoning": r.get("judge_reasoning", ""),
                })

        lines.append(f"### {metric.title()} ({len(disagreements)} disagreements)\n")
        if not disagreements:
            lines.append("Perfect agreement.\n")
        else:
            for d in disagreements:
                lines.append(
                    f"- **{d['case_id']}** ({d['condition']} | {d['bucket']} | {d['risk']}): "
                    f"Human={d['human']}, Judge={d['judge']}"
                )
                if d["reasoning"]:
                    lines.append(f"  - Judge reasoning: {d['reasoning']}")
            lines.append("")

    # --- Agreement by condition ---
    lines.append("## Agreement by Condition\n")
    for cond in ["baseline", "constrained"]:
        cond_rows = [r for r in valid if r["condition"] == cond]
        if not cond_rows:
            continue
        lines.append(f"### {cond.title()} ({len(cond_rows)} outputs)\n")
        lines.append("| Metric | Exact Agreement | Cohen's Kappa |")
        lines.append("|--------|----------------|---------------|")
        for metric in METRICS:
            h_vals = [int(r[f"human_{metric}"]) for r in cond_rows]
            j_vals = [int(r[f"judge_{metric}"]) for r in cond_rows]
            labels = METRIC_LABELS[metric]
            exact = sum(1 for h, j in zip(h_vals, j_vals) if h == j)
            rate = exact / len(cond_rows)
            kappa = cohens_kappa(h_vals, j_vals, labels)
            lines.append(f"| {metric} | {exact}/{len(cond_rows)} ({rate:.1%}) | {kappa:.3f} |")
        lines.append("")

    # --- Rubric feedback ---
    lines.append("## Rubric Quality Assessment\n")
    lines.append("Metrics are ranked by agreement strength to identify which parts of the rubric are clearest vs. most ambiguous.\n")

    metric_kappas = []
    for metric in METRICS:
        h_vals = [int(r[f"human_{metric}"]) for r in valid]
        j_vals = [int(r[f"judge_{metric}"]) for r in valid]
        labels = METRIC_LABELS[metric]
        kappa = cohens_kappa(h_vals, j_vals, labels)
        metric_kappas.append((metric, kappa))

    metric_kappas.sort(key=lambda x: x[1], reverse=True)

    lines.append("| Rank | Metric | Kappa | Assessment |")
    lines.append("|------|--------|-------|------------|")
    for i, (metric, kappa) in enumerate(metric_kappas, 1):
        interp = interpret_kappa(kappa)
        if kappa >= 0.60:
            assessment = "Rubric is clear — scores are reproducible"
        elif kappa >= 0.40:
            assessment = "Rubric is adequate — some subjectivity"
        else:
            assessment = "Rubric needs refinement — too ambiguous"
        lines.append(f"| {i} | {metric} | {kappa:.3f} | {assessment} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute LLM judge agreement statistics")
    parser.add_argument("--model", help="Model tag, e.g. gpt5_2 or gpt4_1_mini")
    parser.add_argument("--adversarial", action="store_true")
    parser.add_argument("--all", action="store_true", help="Run on all available judge score files")
    args = parser.parse_args()

    if args.all:
        combos = []
        for model in ["gpt5_2", "gpt4_1_mini", "llama3_1_8b"]:
            for adv in [False, True]:
                rows = load_judge_scores(model, adv)
                if rows:
                    combos.append((model, adv, rows))
    elif args.model:
        rows = load_judge_scores(args.model, args.adversarial)
        if not rows:
            raise SystemExit(f"No judge scores found for {args.model} ({'adversarial' if args.adversarial else 'original'})")
        combos = [(args.model, args.adversarial, rows)]
    else:
        raise SystemExit("Specify --model or --all")

    for model, adversarial, rows in combos:
        report = analyze(rows, model, adversarial)

        if adversarial:
            out_path = Path(f"02_adversarial_prompting/{model}/llm_judge_agreement.md")
        else:
            out_path = Path(f"01_single_turn/{model}/llm_judge_agreement.md")

        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"Wrote: {out_path}")

        # Console summary
        print(f"\n{'='*60}")
        tag = f"{model} ({'adversarial' if adversarial else 'original'})"
        print(f"Agreement Summary — {tag}")
        print(f"{'='*60}")

        valid = [r for r in rows
                 if all(safe_int(r.get(f"human_{m}")) is not None for m in METRICS)
                 and all(safe_int(r.get(f"judge_{m}")) is not None for m in METRICS)]

        if not valid:
            print("No valid comparisons.\n")
            continue

        for metric in METRICS:
            h_vals = [int(r[f"human_{metric}"]) for r in valid]
            j_vals = [int(r[f"judge_{metric}"]) for r in valid]
            labels = METRIC_LABELS[metric]
            exact = sum(1 for h, j in zip(h_vals, j_vals) if h == j)
            rate = exact / len(valid)
            kappa = cohens_kappa(h_vals, j_vals, labels)
            print(f"  {metric:16s}: {exact}/{len(valid)} ({rate:.1%})  κ={kappa:.3f} ({interpret_kappa(kappa)})")
        print()


if __name__ == "__main__":
    main()
