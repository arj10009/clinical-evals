from __future__ import annotations

import csv
import json
import re
from pathlib import Path


ESCALATION_RE = re.compile(
    r"^ESCALATION:\s*(emergency_now|urgent_same_day|routine_visit|self_care)\b",
    re.MULTILINE,
)


def _extract_escalation(text: str) -> str:
    if not text:
        return ""
    match = ESCALATION_RE.search(text)
    if not match:
        return ""
    return match.group(1)


def main() -> None:
    input_path = Path("outputs/model_outputs.jsonl")
    output_path = Path("scoring/scoring_template.csv")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "case_id",
        "condition",
        "bucket",
        "risk",
        "gold_escalation",
        "model_escalation",
        "score_safety",
        "score_grounding",
        "score_uncertainty",
        "score_actionability",
        "hard_fail",
        "notes",
    ]

    with input_path.open("r", encoding="utf-8") as f_in, output_path.open(
        "w", encoding="utf-8", newline=""
    ) as f_out:
        writer = csv.DictWriter(f_out, fieldnames=fieldnames)
        writer.writeheader()

        for line in f_in:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            model_text = record.get("model_response_text", "")
            model_escalation = _extract_escalation(model_text)

            writer.writerow(
                {
                    "case_id": record.get("case_id", ""),
                    "condition": record.get("condition", ""),
                    "bucket": record.get("bucket", ""),
                    "risk": record.get("risk", ""),
                    "gold_escalation": record.get("gold_escalation", ""),
                    "model_escalation": model_escalation,
                    "score_safety": "",
                    "score_grounding": "",
                    "score_uncertainty": "",
                    "score_actionability": "",
                    "hard_fail": "",
                    "notes": "",
                }
            )


if __name__ == "__main__":
    main()
