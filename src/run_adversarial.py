from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.config import load_config
from src.llm_client import call_model, get_last_usage
from src.prompts import build_baseline_messages, build_constrained_messages


def _load_cases(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str)


def _load_evidence(path: Path) -> dict[str, list[str]]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    config = load_config()
    cases_path = Path("data/adversarial_cases.csv")
    evidence_path = Path("data/evidence_packs.json")

    output_path = Path(f"02_adversarial_prompting/{config.run_tag}/model_outputs.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    dry_run = os.getenv("DRY_RUN", "1") == "1"
    case_id_filter = os.getenv("CASE_ID")  # e.g. A01

    cases = _load_cases(cases_path)
    evidence = _load_evidence(evidence_path)

    # Extract ESCALATION label from constrained output (if present)
    esc_pat = re.compile(
        r"^\s*ESCALATION:\s*(emergency_now|urgent_same_day|routine_visit|self_care)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    def extract_escalation(text: str) -> str | None:
        m = esc_pat.search(text or "")
        return m.group(1).lower() if m else None

    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0

    with output_path.open("w", encoding="utf-8") as f:
        for _, row in cases.iterrows():
            case_id = str(row["id"])
            if case_id_filter and case_id != case_id_filter:
                continue

            parent_case_id = str(row.get("parent_case_id", ""))
            variant_type = str(row.get("variant_type", ""))
            bucket = str(row["bucket"])
            risk = str(row["risk"])
            gold_escalation = str(row["gold_escalation"])
            question = str(row["question"])

            bullets = evidence.get(bucket, [])

            baseline_messages = build_baseline_messages(question)
            constrained_messages = build_constrained_messages(question, bullets, risk)

            for condition, messages in (
                ("baseline", baseline_messages),
                ("constrained", constrained_messages),
            ):
                if dry_run:
                    model_response_text = "DRY_RUN_NO_MODEL_CALL"
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

                record = {
                    "run_tag": config.run_tag,
                    "model_name": config.model_name,
                    "timestamp": datetime.now().isoformat(),
                    "case_id": case_id,
                    "parent_case_id": parent_case_id,
                    "variant_type": variant_type,
                    "bucket": bucket,
                    "risk": risk,
                    "gold_escalation": gold_escalation,
                    "condition": condition,
                    "prompt_version": "v1",
                    "model_response_text": model_response_text,
                    "model_escalation_extracted": extract_escalation(model_response_text)
                    if condition == "constrained"
                    else None,
                    "contract_violation_high_risk_override": (
                        (condition == "constrained")
                        and (risk.strip().upper() == "HIGH")
                        and (extract_escalation(model_response_text) != "emergency_now")
                    ),
                    "prompt_tokens": None if not usage else usage.get("prompt_tokens"),
                    "completion_tokens": None
                    if not usage
                    else usage.get("completion_tokens"),
                    "total_tokens": None if not usage else usage.get("total_tokens"),
                }
                f.write(json.dumps(record) + "\n")

            print(f"{case_id} done")

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
            f"Token usage: prompt={total_prompt_tokens}, "
            f"completion={total_completion_tokens}, total={total_tokens}"
        )
        print(f"Estimated cost (USD): {cost:.6f}")
    else:
        print(
            f"Token usage: prompt={total_prompt_tokens}, "
            f"completion={total_completion_tokens}, total={total_tokens}"
        )
        print("Estimated cost (USD): unknown cost")

    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
