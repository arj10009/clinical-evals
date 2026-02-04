import os
import json
from datetime import datetime
from typing import Any, Dict, List, Tuple

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from src.load_data import load_cases, load_evidence_packs
from src.prompts import build_baseline_messages, build_constrained_messages


def messages_to_text(messages: List[Dict[str, str]], include_system: bool = False) -> str:
    """
    Turn chat-style messages into a printable prompt block.
    By default, excludes SYSTEM text (we put that in an appendix).
    """
    lines = []
    for m in messages:
        role = (m.get("role", "") or "").strip().lower()
        if (role == "system") and (not include_system):
            continue
        content = (m.get("content") or "").rstrip()
        if not content:
            continue
        lines.append(f"[{role.upper()}]\n{content}\n")
    return "\n".join(lines).strip()


def scoring_table() -> Table:
    """
    Blank scoring table the user can fill by hand.
    Uses wrapped labels so long fields (e.g. score_actionability) fit.
    """
    styles = getSampleStyleSheet()
    lbl = ParagraphStyle(
        "lbl_cell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=11,
    )

    def L(s: str) -> Paragraph:
        return Paragraph(s.replace("_", "_"), lbl)

    data = [
        [L("model_escalation"), "", L("score_safety"), "", L("hard_fail"), ""],
        [L("score_grounding"), "", L("score_uncertainty"), "", L("score_actionability"), ""],
    ]

    # Make the right-side label a bit wider
    col_widths = [34*mm, 44*mm, 34*mm, 44*mm, 34*mm, 10*mm]
    t = Table(data, colWidths=col_widths)

    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
            ]
        )
    )
    return t


def notes_box(height_mm: float = 35.0) -> Table:
    """
    A big empty box for handwritten notes.
    """
    t = Table([[""]], colWidths=[190*mm], rowHeights=[height_mm*mm])
    t.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.8, colors.black),
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
            ]
        )
    )
    return t


def main() -> None:
    cases = load_cases()
    evidence = load_evidence_packs()

    # We generate prompts fresh to ensure they match the run_eval logic.
    # Answers come from the latest outputs/model_outputs.jsonl by default.
    outputs_path = os.path.join("outputs", "model_outputs.jsonl")
    if not os.path.exists(outputs_path):
        raise FileNotFoundError(f"Missing {outputs_path}. Run the eval first.")

    # Load outputs keyed by (case_id, condition)
    outputs: Dict[Tuple[str, str], Dict[str, Any]] = {}
    with open(outputs_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            key = (str(obj["case_id"]), str(obj["condition"]))
            outputs[key] = obj

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_pdf = os.path.join("reports", f"print_packet_scoring_{ts}.pdf")
    os.makedirs("reports", exist_ok=True)

    styles = getSampleStyleSheet()
    base = ParagraphStyle(
        "base",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=13,
        spaceAfter=6,
    )
    h = ParagraphStyle(
        "h",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12.5,
        leading=15,
        spaceAfter=8,
    )
    mono = ParagraphStyle(
        "mono",
        parent=base,
        fontName="Courier",
        fontSize=9.5,
        leading=12,
        spaceAfter=6,
    )

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=A4,
        leftMargin=12*mm,
        rightMargin=12*mm,
        topMargin=12*mm,
        bottomMargin=12*mm,
    )

    story = []
    system_prompts_seen = set()

    # Sort by numeric case_id if possible
    def case_sort_key(row: Dict[str, Any]) -> int:
        try:
            return int(str(row["id"]))
        except Exception:
            return 10**9

    for row in sorted(cases.to_dict("records"), key=case_sort_key):
        case_id = str(row["id"])
        bucket = str(row["bucket"])
        risk = str(row["risk"])
        gold = str(row["gold_escalation"])
        question = str(row["question"])

        bullets = evidence.get(bucket, [])
        # Build prompts exactly like the evaluator does
        baseline_msgs = build_baseline_messages(question=question)
        constrained_msgs = build_constrained_messages(
            question=question,
            evidence_bullets=bullets,
            risk=risk,
        )

        baseline_prompt_text = messages_to_text(baseline_msgs)
        constrained_prompt_text = messages_to_text(constrained_msgs)

        baseline_out = outputs.get((case_id, "baseline"), {})
        constrained_out = outputs.get((case_id, "constrained"), {})

        baseline_answer = str(baseline_out.get("model_response_text", "")).strip()
        constrained_answer = str(constrained_out.get("model_response_text", "")).strip()

                # --- Case header ---
        story.append(Paragraph(f"CASE {case_id} | {bucket} | risk: {risk} | gold: {gold}", h))

        # Capture SYSTEM prompt text for appendix (baseline + constrained)
        baseline_system = messages_to_text(baseline_msgs, include_system=True)
        constrained_system = messages_to_text(constrained_msgs, include_system=True)

        # Display prompts WITHOUT system blocks (cleaner for scoring)
        baseline_prompt_text = messages_to_text(baseline_msgs, include_system=False)
        constrained_prompt_text = messages_to_text(constrained_msgs, include_system=False)

        # For the print packet, we don't need the Evidence bullets block to score answers.
        constrained_prompt_display = constrained_prompt_text
        if "Evidence bullets:" in constrained_prompt_display:
            constrained_prompt_display = constrained_prompt_display.split("Evidence bullets:")[0].rstrip()

        # --- Section 1: Baseline prompt ---
        story.append(Paragraph("1) BASELINE PROMPT", ParagraphStyle("sec", parent=h, fontSize=11.5)))
        story.append(Paragraph(baseline_prompt_text.replace("\n", "<br/>"), mono))
        story.append(Spacer(1, 4*mm))

        # --- Section 2: Baseline answer + scoring table ---
        story.append(Paragraph("2) BASELINE ANSWER (verbatim)", ParagraphStyle("sec3", parent=h, fontSize=11.5)))
        story.append(Paragraph(baseline_answer.replace("\n", "<br/>"), base))
        story.append(Paragraph("Baseline scoring", ParagraphStyle("lbl", parent=base, fontName="Helvetica-Bold")))
        story.append(scoring_table())
        story.append(Spacer(1, 6*mm))

        # --- Section 3: Constrained prompt ---
        story.append(Paragraph("3) CONSTRAINED PROMPT", ParagraphStyle("sec2", parent=h, fontSize=11.5)))
        story.append(Paragraph(constrained_prompt_display.replace("\n", "<br/>"), mono))
        story.append(Spacer(1, 4*mm))

        # --- Section 4: Constrained answer + scoring table ---
        story.append(Paragraph("4) CONSTRAINED ANSWER (verbatim)", ParagraphStyle("sec4", parent=h, fontSize=11.5)))
        story.append(Paragraph(constrained_answer.replace("\n", "<br/>"), base))
        story.append(Paragraph("Constrained scoring", ParagraphStyle("lbl2", parent=base, fontName="Helvetica-Bold")))
        story.append(scoring_table())
        story.append(Spacer(1, 6*mm))

        # --- Section 5: Notes (no box; just whitespace to write on) ---
        story.append(Paragraph("5) NOTES", ParagraphStyle("sec5", parent=h, fontSize=11.5)))
        story.append(Spacer(1, 55*mm))

        # Stash the system prompts for appendix at the end (unique set)
        system_prompts_seen.add(baseline_system.strip())
        system_prompts_seen.add(constrained_system.strip())

        # IMPORTANT: never start the next case on the same page.
        story.append(PageBreak())

    
    # --- Appendix: SYSTEM prompt text (for reference; not needed for scoring most of the time) ---
    story.append(PageBreak())
    story.append(Paragraph("APPENDIX: SYSTEM PROMPTS (reference)", h))
    story.append(Paragraph(
        "These are the system instructions used in the run. They are excluded from the case pages to keep scoring clean.",
        base
    ))
    story.append(Spacer(1, 4*mm))

    for i, sp in enumerate(sorted([s for s in system_prompts_seen if s.strip()]), start=1):
        story.append(Paragraph(f"System prompt #{i}", ParagraphStyle("apph", parent=h, fontSize=11.5)))
        story.append(Paragraph(sp.replace("\n", "<br/>"), mono))
        story.append(Spacer(1, 6*mm))

    doc.build(story)
    print(f"Wrote {os.path.abspath(out_pdf)}")


if __name__ == "__main__":
    main()
