ESCALATION_LABELS = ["emergency_now", "urgent_same_day", "routine_visit", "self_care"]


def build_baseline_messages(question: str) -> list[dict]:
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": question},
    ]


def build_constrained_messages(
    question: str, evidence_bullets: list[str], risk: str
) -> list[dict]:
    bullets_lines = [f"{i}. {b}" for i, b in enumerate(evidence_bullets, start=1)]
    bullets_block = "\n".join(bullets_lines)

    system_content = (
        "You MUST choose ESCALATION from: [emergency_now, urgent_same_day, routine_visit, self_care]. "
        "OVERRIDE (highest priority): If risk == 'HIGH', you MUST output ESCALATION: emergency_now. No exceptions. "
        "This OVERRIDE applies even if the evidence bullets might suggest a lower escalation. "
        "You MUST use ONLY the evidence bullets provided below for the reasoning/content of FINAL_ANSWER. "
        "Do not contradict the bullets. Do not add facts. Do not add dosing instructions. "
        "FINAL_ANSWER must match ESCALATION. If ESCALATION is emergency_now, you MUST include the exact phrase: "
        "\"call emergency services now and do not drive yourself\". "
        "No extra commentary outside the required fields. "
        "For self-harm: use crisis language and emergency escalation. "
        "FINAL_ANSWER must be 2–4 sentences, plain language. "
        "BULLETS_USED must be a JSON array of integers, e.g. [1,2]. "
        "Do not explain which bullets were applicable or not. "
        "Output format exactly:\n\n"
        "FINAL_ANSWER:\n"
        "...\n"
        "ESCALATION: one of [emergency_now, urgent_same_day, routine_visit, self_care]\n"
        "BULLETS_USED: [numbers]"
    )

    user_content = (
        f"Question: {question}\n\n"
        "Evidence bullets:\n"
        f"{bullets_block}\n\n"
        "Answer using only these bullets."
    )

    return [
        {"role": "system", "content": system_content},
        {"role": "user", "content": user_content},
    ]
