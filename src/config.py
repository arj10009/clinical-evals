from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass
class Config:
    model_name: str
    api_key: str
    run_tag: str


def load_config() -> Config:
    load_dotenv()

    required_keys = ["MODEL_NAME", "OPENAI_API_KEY", "RUN_TAG"]
    missing_keys = [k for k in required_keys if not os.getenv(k)]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise ValueError(f"Missing required environment variables: {missing}")

    return Config(
        model_name=os.environ["MODEL_NAME"],
        api_key=os.environ["OPENAI_API_KEY"],
        run_tag=os.environ["RUN_TAG"],
    )
