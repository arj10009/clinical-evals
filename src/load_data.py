from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = ["id", "bucket", "risk", "question", "gold_escalation", "notes"]

def load_cases() -> pd.DataFrame:
    repo_root = Path(__file__).resolve().parents[1]
    cases_path = repo_root / "data" / "cases.csv"

    df = pd.read_csv(cases_path, dtype=str)

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"cases.csv missing columns: {missing}")

    if len(df) != 30:
        raise ValueError(f"Expected 30 cases, found {len(df)}")

    return df

if __name__ == "__main__":
    df = load_cases()
    print(f"Loaded {len(df)} cases")

import json
from typing import Dict, List

def load_evidence_packs() -> Dict[str, List[str]]:
    """
    Load bucket-level evidence bullets from data/evidence_packs.json.
    Returns: dict[bucket] -> list of bullet strings
    """
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "data" / "evidence_packs.json"
    with open(path, "r", encoding="utf-8") as f:
        packs = json.load(f)

    if not isinstance(packs, dict):
        raise ValueError("evidence_packs.json must be a JSON object keyed by bucket")

    # basic validation: each value is a list of strings
    for k, v in packs.items():
        if not isinstance(v, list) or not all(isinstance(x, str) for x in v):
            raise ValueError(f"evidence_packs['{k}'] must be a list of strings")

    return packs
