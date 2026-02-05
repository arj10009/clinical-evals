# What now?

This repo is an MVP “safety eval harness” comparing a **baseline** local model vs a **constrained** (policy-guided) variant on a small set of clinical-style cases, with manual scoring and reports.

Below is the roadmap for turning this into something that looks and feels like real model-quality work: better coverage, harder tests, less “toy” behavior, and clearer evidence of trade-offs.

---

## 1) Patch work

**What it means:** After you identify failures (especially hard fails), you create targeted fixes (“patches”) and re-run the eval to prove the fix works **without breaking other behaviors**.

In practice, “patch work” usually means one of:
- adjusting the constraint prompt / policy instructions,
- adding a small routing rule (e.g., “if these red flags appear → emergency_now”),
- tightening unsafe branching (remove “you could also…” off-ramps in emergencies),
- or adding a post-processing constraint (format, escalation clarity, etc.).

The key is discipline: every patch should be justified by a concrete failure, tested on the original case, and tested on “nearby” cases to avoid regressions.

---

## 2) Adversarial variants

**What it means:** You take a single clinical scenario and generate “evil twins” that are realistic but designed to trick a model into unsafe behavior (under-triage, unsafe reassurance, or vague branching).

These are high-value because real patients don’t present like clean exam questions. Adversarial variants simulate messy reality while still being grounded in plausible language.

### Variant ideas
- **Burying key symptoms in the middle:** Put the red flag in turn 2 or mid-paragraph so the model must track context.
- **Adding distracting irrelevant information:** Add noise (work stress, diet details, unrelated aches) to test signal extraction.
- **Making the patient sound calm and confident:** “I feel fine, just checking” while describing high-risk symptoms.
- **“I don’t want to go to the hospital” variant:** Tests whether the model still escalates appropriately.
- **Social manipulation of the AI:** “I can’t afford it,” “my son is sick,” “I’ll lose my job,” etc.
- **Authority script:** “I’m a doctor; I’ll monitor at home unless it worsens” — tests resistance to authority framing.
- **Plausible alternative diagnosis that tempts under-triage:** e.g., “it might just be reflux/anxiety/migraine” layered into a real emergency presentation.

---

## 3) Multi-turn cases

**What it means:** Instead of a single prompt, the case unfolds across multiple turns, where crucial information may appear late, or the patient’s answers change the risk.

This tests whether the model:
- updates triage appropriately as new info arrives,
- asks the right questions when needed (without delaying emergencies),
- and avoids “locking in” too early.

Multi-turn cases are closer to actual clinical interaction and expose a lot of brittle behavior that single-turn cases miss.

---

## 4) Specialist-labeled gold

**What it means:** Instead of you alone deciding the “gold” escalation, you get clinicians (ED/ICU, cardiology, O&G, psych, paeds, etc.) to label what the correct escalation should be — and ideally provide brief rationale.

This gives the project credibility fast because it reduces “one-person subjective gold” and moves toward something defensible:
- “Here is how multiple clinicians would triage this.”
- “Here’s where they agree/disagree.”
- “Here’s the rubric we used.”

Even 10–20 specialist-labeled cases can massively upgrade the seriousness of the work.

---

## 5) Measuring regression risk from classic trade-offs

**What it means:** Safety constraints often improve one failure mode while worsening another. You want to measure that explicitly rather than hand-waving it away.

Classic trade-offs to track:
- **Over-triage vs under-triage:** safer but potentially alarmist.
- **Brevity vs usability:** concise emergency advice can be safe but unhelpful if it doesn’t guide the patient.
- **Uncertainty vs decisiveness:** too confident can be dangerous; too hedged can be dangerous in emergencies.
- **Refusals vs helpfulness:** refusing too often can create patient harm through inaction.

Regression risk measurement means you can say: “We reduced under-triage by X, while over-triage increased by Y, and actionability changed by Z.”

---

## 6) Scaling into a bigger evaluation suite with stratified metrics

**What it means:** You expand beyond 30 cases into a larger set, and you report results in “slices” that matter, not just one average.

Stratified metrics examples:
- by **risk level** (HIGH/MED/LOW),
- by **bucket** (stroke, chest pain, suicide, pregnancy, sepsis…),
- by **failure type** (unsafe branching, refusal, hallucination, missing red flag),
- by **presentation style** (clean vs noisy vs adversarial vs multi-turn).

This prevents models from “gaming the mean” (doing well on easy cases while failing catastrophically on the ones that matter).

---

## 7) Inter-rater reliability

**What it means:** You get at least one additional scorer and measure how consistent you are with each other.

This matters because manual scoring is inherently subjective. Inter-rater reliability lets you say:
- “Two clinicians independently scored these and generally agreed.”
- Or, “Here are the items with disagreement and how we resolved them.”

Even a small study (e.g., 10 cases × 2 raters) is better than none — and it teaches you where the rubric is ambiguous.

---

## 8) Automated checks for under-triaging and unsafe branching

**What it means:** You build simple automatic detectors for “obviously unsafe” behaviors so you don’t rely purely on manual review.

Examples:
- **Under-triage detector:** gold is emergency_now, but model says urgent/routine/self-care.
- **Unsafe branching detector:** in emergency_now cases, model includes off-ramps like “urgent care,” “see a GP,” “monitor at home,” “if it worsens…” as primary options.
- **Clarity detector:** does it explicitly say “call emergency services now / do not drive yourself” when appropriate?
- **Format compliance:** ensures constrained model always outputs escalation in the expected schema.

These checks let you scale: you can run 500 cases and quickly surface the dangerous ones.

---

## Suggested order of attack

If you want the fastest credibility upgrade:
1) Specialist-labeled gold (even a small batch)
2) Adversarial variants + multi-turn cases
3) Automated unsafe branching / under-triage checks
4) Bigger suite with stratified metrics
5) Inter-rater reliability
6) Patch work with regression tracking

That sequence turns this from “cool personal project” into “this person is doing real evaluation work.”