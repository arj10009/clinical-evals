from __future__ import annotations

"""Generate markdown failure packet for constrained HIGH-risk rule failures.

This packet is data-driven:
- Reads 02_adversarial_prompting/{model}/analysis/constrained_high_risk_rule_failures.csv
  (written by src.analyze_adversarial_deltas)
- For each failing case_id, includes:
  - adversarial prompt
  - evidence bullets for its bucket
  - baseline output
  - constrained output
  - recorded contract checks

Usage:
    python -m src.make_failure_packet --model gpt5_2
    python -m src.make_failure_packet --model gpt4_1_mini
"""

import argparse
import csv
import json
from pathlib import Path


CASES_CSV = Path("data/adversarial_cases.csv")
EVIDENCE_JSON = Path("data/evidence_packs.json")


def load_cases() -> dict[str, dict]:
    out: dict[str, dict] = {}
    with CASES_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            out[row["id"].strip()] = row
    return out


def load_evidence() -> dict[str, list[str]]:
    with EVIDENCE_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_scores(path: Path) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            out[(row["case_id"].strip(), row["condition"].strip())] = row
    return out


def load_outputs(path: Path) -> dict[tuple[str, str], dict]:
    out: dict[tuple[str, str], dict] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            key = (rec["case_id"], rec["condition"])
            out[key] = rec
    return out


def load_high_risk_failures(path: Path) -> list[str]:
    """Return failing case_ids in sorted order."""
    if not path.exists():
        raise SystemExit(
            f"Missing failures CSV: {path}\n"
            f"Run: python -m src.analyze_adversarial_deltas --model <model>"
        )

    df: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            df.append(row)

    case_ids = sorted({(row.get("case_id") or "").strip() for row in df if (row.get("case_id") or "").strip()})
    return case_ids


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HIGH-risk rule failure packet (data-driven)")
    parser.add_argument("--model", required=True, help="Model tag, e.g. gpt5_2 or gpt4_1_mini")
    args = parser.parse_args()

    scores_csv = Path(f"02_adversarial_prompting/{args.model}/scored_results.csv")
    outputs_jsonl = Path(f"02_adversarial_prompting/{args.model}/model_outputs.jsonl")
    failures_csv = Path(f"02_adversarial_prompting/{args.model}/analysis/constrained_high_risk_rule_failures.csv")

    out_md = Path(f"02_adversarial_prompting/{args.model}/analysis/failure_packet_high_risk_rule_failures.md")

    cases = load_cases()
    evidence = load_evidence()
    scores = load_scores(scores_csv)
    outputs = load_outputs(outputs_jsonl)

    failing_case_ids = load_high_risk_failures(failures_csv)

    out_md.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append(f"# HIGH-risk rule failures — {args.model}\n")

    if not failing_case_ids:
        lines.append("No constrained HIGH-risk rule failures were found.\n")
        out_md.write_text("\n".join(lines), encoding="utf-8")
        print("Wrote:", out_md)
        return

    lines.append(
        "These are the constrained-run cases where risk == HIGH but the output did NOT escalate to emergency_now.\n"
    )
    lines.append(f"Failing case_ids: {', '.join(failing_case_ids)}\n")

    for cid in failing_case_ids:
        if cid not in cases:
            # Should not happen, but keep packet robust
            lines.append("\n---\n")
            lines.append(f"## {cid}\n")
            lines.append("WARNING: case_id not found in data/adversarial_cases.csv\n")
            continue

        c = cases[cid]
        bucket = c.get("bucket", "")
        risk = c.get("risk", "")
        gold = c.get("gold_escalation", "")
        variant = c.get("variant_type", "")
        question = c.get("question", "")

        cons_out = outputs.get((cid, "constrained"), {}).get("model_response_text", "")
        base_out = outputs.get((cid, "baseline"), {}).get("model_response_text", "")

        cons_score = scores.get((cid, "constrained"), {})
        contract = {
            "Format OK": cons_score.get("Format OK", ""),
            "High risk ==> emergency_now (if applicable)": cons_score.get(
                "High risk ==> emergency_now (if applicable)", ""
            ),
            "Exact emergency phrase present when emergency_now": cons_score.get(
                "Exact emergency phrase present when emergency_now", ""
            ),
            "No dosing / no extra info beyond bullets": cons_score.get(
                "No dosing / no extra info beyond bullets", ""
            ),
        }

        lines.append("\n---\n")
        lines.append(f"## {cid} ({bucket} | {variant} | risk={risk} | gold={gold})\n")

        lines.append("### Adversarial prompt\n")
        lines.append(question.strip() + "\n")

        lines.append("### Evidence bullets for this bucket\n")
        bullets = evidence.get(bucket, [])
        if bullets:
            for i, b in enumerate(bullets, start=1):
                lines.append(f"{i}. {b}")
        else:
            lines.append("(No evidence bullets found for this bucket.)")
        lines.append("")

        lines.append("### Baseline output\n")
        lines.append("```")
        lines.append(base_out.strip())
        lines.append("```\n")

        lines.append("### Constrained output\n")
        lines.append("```")
        lines.append(cons_out.strip())
        lines.append("```\n")

        lines.append("### Contract checks you recorded\n")
        for k, v in contract.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    out_md.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote:", out_md)


if __name__ == "__main__":
    main()