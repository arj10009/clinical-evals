from __future__ import annotations

"""Multi-turn clinical evaluation runner.

Processes multi-turn cases where clinical information unfolds across
multiple patient messages.  For each turn the model sees the full
conversation history and must produce an updated response.

Usage:
    python -m src.run_multiturn_eval                  # dry-run (default)
    DRY_RUN=0 python -m src.run_multiturn_eval        # live API calls
    CASE_ID=MT01 python -m src.run_multiturn_eval     # single case

Output:
    04_multi_turn/{run_tag}/model_outputs.jsonl
"""

import csv
import json
import os
import re
from datetime import datetime
from pathlib import Path

from src.config import load_config
from src.llm_client import call_model, get_last_usage
from src.prompts_multiturn import (
    build_multiturn_baseline_messages,
    build_multiturn_constrained_messages,
)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_multiturn_cases(path: Path) -> dict[str, list[dict]]:
    """Load multi-turn cases grouped by case_id.

    Returns a dict mapping case_id -> list of turn dicts, sorted by turn number.
    """
    cases: dict[str, list[dict]] = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            case_id = row["case_id"].strip()
            cases.setdefault(case_id, []).append(row)

    # Sort turns within each case
    for case_id in cases:
        cases[case_id].sort(key=lambda r: int(r["turn"]))

    return cases


def load_multiturn_evidence(path: Path) -> dict[str, dict[str, list[str]]]:
    """Load turn-specific evidence packs.

    Returns dict mapping bucket -> {turn_N: [bullets]}.
    """
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Escalation extraction
# ---------------------------------------------------------------------------

_ESC_PAT = re.compile(
    r"^\s*ESCALATION:\s*(emergency_now|urgent_same_day|routine_visit|self_care)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def extract_escalation(text: str) -> str | None:
    """Extract ESCALATION label from constrained output."""
    m = _ESC_PAT.search(text or "")
    return m.group(1).lower() if m else None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    config = load_config()
    cases_path = Path("data/multiturn_cases.csv")
    evidence_path = Path("data/evidence_packs_multiturn.json")

    output_path = Path(f"04_multi_turn/{config.run_tag}/model_outputs.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dry_run = os.getenv("DRY_RUN", "1") == "1"
    case_id_filter = os.getenv("CASE_ID")

    cases = load_multiturn_cases(cases_path)
    evidence = load_multiturn_evidence(evidence_path)

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    with output_path.open("w", encoding="utf-8") as f:
        for case_id, turns in sorted(cases.items()):
            if case_id_filter and case_id != case_id_filter:
                continue

            bucket = turns[0]["bucket"]
            risk = turns[0]["risk"]
            bucket_evidence = evidence.get(bucket, {})

            # Track conversation history and escalation per condition
            history: dict[str, list[dict]] = {
                "baseline": [],
                "constrained": [],
            }
            prior_escalation: dict[str, str | None] = {
                "baseline": None,
                "constrained": None,
            }

            for turn_data in turns:
                turn_num = int(turn_data["turn"])
                patient_text = turn_data["text"]
                gold_at_turn = turn_data["gold_escalation_at_turn"]

                # Get turn-specific evidence bullets
                turn_key = f"turn_{turn_num}"
                turn_bullets = bucket_evidence.get(turn_key, [])

                for condition in ("baseline", "constrained"):
                    if condition == "baseline":
                        messages = build_multiturn_baseline_messages(
                            conversation_history=history["baseline"],
                            current_turn_text=patient_text,
                        )
                    else:
                        messages = build_multiturn_constrained_messages(
                            conversation_history=history["constrained"],
                            current_turn_text=patient_text,
                            evidence_bullets=turn_bullets,
                            risk=risk,
                            turn_num=turn_num,
                            prior_escalation=prior_escalation["constrained"],
                            bucket=bucket,
                            speaker=turn_data.get("speaker", ""),
                        )

                    if dry_run:
                        model_response_text = f"DRY_RUN_NO_MODEL_CALL [turn {turn_num}]"
                        usage = None
                    else:
                        model_response_text = call_model(
                            config.model_name,
                            config.api_key,
                            messages,
                            dry_run=False,
                        )
                        usage = get_last_usage()
                        if usage:
                            total_prompt_tokens += usage.get("prompt_tokens", 0)
                            total_completion_tokens += usage.get("completion_tokens", 0)
                            total_tokens += usage.get("total_tokens", 0)

                    # Extract escalation from constrained output
                    model_esc = None
                    if condition == "constrained":
                        model_esc = extract_escalation(model_response_text)
                        prior_escalation["constrained"] = model_esc

                    # Determine gold_final_escalation (last turn's gold)
                    gold_final = turns[-1]["gold_escalation_at_turn"]

                    # Check contract violation
                    contract_violation = (
                        condition == "constrained"
                        and risk.strip().upper() == "HIGH"
                        and model_esc is not None
                        and model_esc != "emergency_now"
                    )

                    record = {
                        "run_tag": config.run_tag,
                        "model_name": config.model_name,
                        "timestamp": datetime.now().isoformat(),
                        "case_id": case_id,
                        "turn_num": turn_num,
                        "total_turns": len(turns),
                        "bucket": bucket,
                        "risk": risk,
                        "gold_escalation_at_turn": gold_at_turn,
                        "gold_final_escalation": gold_final,
                        "condition": condition,
                        "prompt_version": "v2_multiturn_patched",
                        "model_response_text": model_response_text,
                        "model_escalation_extracted": model_esc,
                        "prior_escalation": prior_escalation.get(condition),
                        "contract_violation_high_risk_override": contract_violation,
                        "escalation_change_rationale": turn_data.get("escalation_change_rationale", ""),
                        "prompt_tokens": None if not usage else usage.get("prompt_tokens"),
                        "completion_tokens": None if not usage else usage.get("completion_tokens"),
                        "total_tokens": None if not usage else usage.get("total_tokens"),
                    }
                    f.write(json.dumps(record) + "\n")

                    # Update conversation history for next turn
                    history[condition].append(
                        {"role": "user", "content": patient_text}
                    )
                    history[condition].append(
                        {"role": "assistant", "content": model_response_text}
                    )

            print(f"{case_id} done ({len(turns)} turns)")

    # Cost estimation
    price_map = {
        "gpt-5.2": {"prompt_per_1k": 2.0, "completion_per_1k": 6.0},
        "gpt-5-mini": {"prompt_per_1k": 0.3, "completion_per_1k": 1.0},
        "gpt-4.1-mini": {"prompt_per_1k": 0.4, "completion_per_1k": 1.2},
    }
    if config.model_name in price_map:
        rates = price_map[config.model_name]
        cost = (
            total_prompt_tokens * rates["prompt_per_1k"]
            + total_completion_tokens * rates["completion_per_1k"]
        ) / 1000.0
        print(
            f"\nToken usage: prompt={total_prompt_tokens}, "
            f"completion={total_completion_tokens}, total={total_tokens}"
        )
        print(f"Estimated cost (USD): {cost:.6f}")
    else:
        print(
            f"\nToken usage: prompt={total_prompt_tokens}, "
            f"completion={total_completion_tokens}, total={total_tokens}"
        )
        print("Estimated cost (USD): unknown cost")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
