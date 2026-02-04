from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


def _load_records(path: Path) -> list[dict]:
    records = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def main() -> None:
    input_path = Path("outputs/model_outputs.jsonl")
    output_path = Path("reports/summary.md")

    records = _load_records(input_path)
    if not records:
        raise ValueError("No records found in outputs/model_outputs.jsonl")

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

    output_path.parent.mkdir(parents=True, exist_ok=True)

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

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Wrote reports/summary.md")


if __name__ == "__main__":
    main()
