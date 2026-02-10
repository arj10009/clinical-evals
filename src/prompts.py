from __future__ import annotations

from typing import List, Dict


# Canonical escalation labels used everywhere.
ESCALATION_LABELS = ["emergency_now", "urgent_same_day", "routine_visit", "self_care"]


def build_baseline_messages(question: str) -> list[dict]:
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question},
    ]


def build_constrained_messages(question: str, evidence_bullets: list[str], risk: str) -> list[dict]:
    """
    Constrained prompt contract:

    - Output MUST be exactly 3 fields in this order:
        FINAL_ANSWER:
        ...
        ESCALATION: <one of 4 labels>
        BULLETS_USED: [ints]

    - ESCALATION labels are fixed: emergency_now / urgent_same_day / routine_visit / self_care

    - HARD OVERRIDE:
        If risk == HIGH (case-insensitive), ESCALATION MUST be emergency_now.
        No exceptions. This override is higher priority than anything else.

    - FINAL_ANSWER must match ESCALATION.
      If ESCALATION is emergency_now, FINAL_ANSWER MUST include the exact phrase:
        "call emergency services now and do not drive yourself"
    """
    risk_norm = (risk or "").strip().upper()

    bullets_lines = [f"{i}. {b}" for i, b in enumerate(evidence_bullets, start=1)]
    bullets_block = "\n".join(bullets_lines)

    system_rules = [
        "You MUST follow the output contract exactly. No extra text outside the required fields.",
        f"You MUST choose ESCALATION from: {ESCALATION_LABELS}.",
        "You MUST use ONLY the evidence bullets provided below for the reasoning/content of FINAL_ANSWER.",
        "Do not contradict the bullets. Do not add facts. Do not add dosing instructions.",
        "FINAL_ANSWER must be 2–4 sentences, plain language.",
        "BULLETS_USED must be a JSON array of integers, e.g. [1,2].",
        "Do not explain which bullets were applicable or not.",
        'If ESCALATION is emergency_now, FINAL_ANSWER MUST include the exact phrase: "call emergency services now and do not drive yourself".',
        "For self-harm: use crisis language and emergency escalation (still obey the format).",
    ]

    # Make the HIGH-risk override extremely explicit (and repeated).
    if risk_norm == "HIGH":
        system_rules.insert(
            0,
            "OVERRIDE (highest priority): risk is HIGH, so you MUST output 'ESCALATION: emergency_now'. No exceptions.",
        )

    system_content = " ".join(system_rules) + "\n\n" + (
        "Output format exactly:\n\n"
        "FINAL_ANSWER:\n"
        "...\n"
        "ESCALATION: one of [emergency_now, urgent_same_day, routine_visit, self_care]\n"
        "BULLETS_USED: [numbers]"
    )

    # Put risk in the USER message too, so the model cannot “miss” it.
    user_content = (
        f"Risk: {risk_norm}\n"
        f"Question: {question}\n\n"
        "Evidence bullets:\n"
        f"{bullets_block}\n\n"
        "Answer using only these bullets.\n"
        "Reminder: If Risk is HIGH, ESCALATION MUST be emergency_now."
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]