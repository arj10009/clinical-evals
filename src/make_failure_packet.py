from __future__ import annotations

import csv
import json
from pathlib import Path

CASES_CSV = Path("data/adversarial_cases.csv")
EVIDENCE_JSON = Path("data/evidence_packs.json")
SCORES_CSV = Path("runs/adversarial/gpt5_2/scored_results.csv")
OUTPUTS_JSONL = Path("runs/adversarial/gpt5_2/model_outputs.jsonl")
OUT_MD = Path("runs/adversarial/gpt5_2/analysis/failure_packet_sepsis_high_risk.md")

TARGET_CASES = {"A17","A18","A19","A20"}

def load_cases() -> dict[str, dict]:
    out = {}
    with CASES_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            out[row["id"].strip()] = row
    return out

def load_evidence() -> dict[str, list[str]]:
    with EVIDENCE_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)

def load_scores() -> dict[tuple[str,str], dict]:
    # keyed by (case_id, condition)
    out = {}
    with SCORES_CSV.open("r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            out[(row["case_id"].strip(), row["condition"].strip())] = row
    return out

def load_outputs() -> dict[tuple[str,str], dict]:
    out = {}
    with OUTPUTS_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            key = (rec["case_id"], rec["condition"])
            out[key] = rec
    return out

def main() -> None:
    cases = load_cases()
    evidence = load_evidence()
    scores = load_scores()
    outputs = load_outputs()

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append("# Sepsis high-risk rule failures (A17–A20)\n")
    lines.append("These are the four adversarial sepsis cases where the constrained run did NOT escalate to emergency_now.\n")

    for cid in ["A17","A18","A19","A20"]:
        c = cases[cid]
        bucket = c["bucket"]
        risk = c["risk"]
        gold = c["gold_escalation"]
        variant = c["variant_type"]
        question = c["question"]

        cons_out = outputs.get((cid,"constrained"), {}).get("model_response_text","")
        base_out = outputs.get((cid,"baseline"), {}).get("model_response_text","")

        cons_score = scores.get((cid,"constrained"), {})
        # contract checks as recorded
        contract = {
            "Format OK": cons_score.get("Format OK",""),
            "High risk ==> emergency_now (if applicable)": cons_score.get("High risk ==> emergency_now (if applicable)",""),
            "Exact emergency phrase present when emergency_now": cons_score.get("Exact emergency phrase present when emergency_now",""),
            "No dosing / no extra info beyond bullets": cons_score.get("No dosing / no extra info beyond bullets",""),
        }

        lines.append("\n---\n")
        lines.append(f"## {cid} ({bucket} | {variant} | risk={risk} | gold={gold})\n")
        lines.append("### Adversarial prompt\n")
        lines.append(question.strip() + "\n\n")

        lines.append("### Evidence bullets for this bucket\n")
        bullets = evidence.get(bucket, [])
        for i, b in enumerate(bullets, start=1):
            lines.append(f"{i}. {b}")
        lines.append("\n")

        lines.append("### Baseline output\n")
        lines.append("```")
        lines.append(base_out.strip())
        lines.append("```\n")

        lines.append("### Constrained output\n")
        lines.append("```")
        lines.append(cons_out.strip())
        lines.append("```\n")

        lines.append("### Contract checks you recorded\n")
        for k,v in contract.items():
            lines.append(f"- {k}: {v}")
        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print("Wrote:", OUT_MD)

if __name__ == "__main__":
    main()
