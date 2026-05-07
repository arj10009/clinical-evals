from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd


def _load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def _write_summary(records: list[dict], out_path: Path) -> None:
    if not records:
        raise ValueError("No records found")

    run_tag = records[0].get("run_tag", "")
    model_name = records[0].get("model_name", "")
    total_records = len(records)
    cases_count = total_records // 2

    condition_counts = Counter(r.get("condition", "") for r in records)

    bucket_risk_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for r in records:
        bucket = r.get("bucket", "")
        risk = r.get("risk", "")
        bucket_risk_counts[bucket][risk] += 1

    lines: list[str] = []
    lines.append("# Summary")
    lines.append("")
    lines.append(f"- Run tag: {run_tag}")
    lines.append(f"- Model name: {model_name}")
    lines.append(f"- Total records: {total_records}")
    lines.append(f"- Inferred cases: {cases_count}")
    lines.append("")
    lines.append("## Counts by condition")
    lines.append("")
    for condition, count in sorted(condition_counts.items()):
        lines.append(f"- {condition}: {count}")
    lines.append("")
    lines.append("## Counts by bucket and risk")
    lines.append("")
    lines.append("| bucket | risk | count |")
    lines.append("| --- | --- | --- |")
    for bucket in sorted(bucket_risk_counts.keys()):
        for risk, count in sorted(bucket_risk_counts[bucket].items()):
            lines.append(f"| {bucket} | {risk} | {count} |")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _load_scored_csv(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str).fillna("")
    for c in ["score_safety", "score_grounding", "score_uncertainty", "score_actionability", "hard_fail"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _write_scored_summary(df: pd.DataFrame, out_path: Path) -> None:
    if df.empty:
        raise ValueError("scored_results.csv is empty")

    lines: list[str] = []
    lines.append("# Scored summary")
    lines.append("")
    lines.append(f"- Rows: {len(df)}")
    lines.append(f"- Cases (inferred): {df['case_id'].nunique() if 'case_id' in df.columns else 'unknown'}")
    lines.append("")

    def block(title: str, sub: pd.DataFrame) -> None:
        lines.append(f"## {title}")
        lines.append("")
        for metric in ["score_safety", "score_grounding", "score_uncertainty", "score_actionability"]:
            if metric in sub.columns:
                lines.append(f"- {metric}: mean={sub[metric].mean():.3f} (n={sub[metric].notna().sum()})")
        if "hard_fail" in sub.columns:
            hf = sub["hard_fail"]
            lines.append(f"- hard_fail rate: {(hf==1).mean():.3f} (n={hf.notna().sum()})")
        if "model_escalation" in sub.columns:
            lines.append(f"- model_escalation counts: {sub['model_escalation'].value_counts(dropna=False).to_dict()}")
        lines.append("")

    if "condition" in df.columns:
        for cond in ["baseline", "constrained"]:
            sub = df[df["condition"] == cond]
            if len(sub) > 0:
                block(cond, sub)

    if set(["case_id", "condition"]).issubset(df.columns):
        pivot = df.pivot_table(
            index="case_id",
            columns="condition",
            values=["score_safety", "score_grounding", "score_uncertainty", "score_actionability", "hard_fail"],
            aggfunc="first",
        )
        lines.append("## Deltas (constrained - baseline)")
        lines.append("")
        for metric in ["score_safety", "score_grounding", "score_uncertainty", "score_actionability", "hard_fail"]:
            if (metric, "baseline") in pivot.columns and (metric, "constrained") in pivot.columns:
                delta = pivot[(metric, "constrained")] - pivot[(metric, "baseline")]
                lines.append(f"- {metric} delta mean: {delta.mean():.3f} (n={delta.notna().sum()})")
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir", help="Run folder, e.g. 01_single_turn/gpt5_2")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    model_outputs = run_dir / "model_outputs.jsonl"
    scored_results = run_dir / "scored_results.csv"

    if not model_outputs.exists():
        raise FileNotFoundError(f"Missing {model_outputs}")
    if not scored_results.exists():
        raise FileNotFoundError(f"Missing {scored_results}")

    records = _load_jsonl(model_outputs)
    _write_summary(records, run_dir / "summary.md")

    df = _load_scored_csv(scored_results)
    _write_scored_summary(df, run_dir / "scored_summary.md")

    print(f"Wrote {run_dir / 'summary.md'}")
    print(f"Wrote {run_dir / 'scored_summary.md'}")


if __name__ == "__main__":
    main()
