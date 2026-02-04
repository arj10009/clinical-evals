from __future__ import annotations

import os
from typing import Any

_LAST_USAGE: dict[str, int] | None = None


def get_last_usage() -> dict[str, int] | None:
    return _LAST_USAGE


def _set_last_usage(usage: dict[str, int] | None) -> None:
    global _LAST_USAGE
    _LAST_USAGE = usage


def call_model(
    model_name: str, api_key: str, messages: list[dict], dry_run: bool = False
) -> str:
    if dry_run:
        _set_last_usage(None)
        return "DRY_RUN_NO_MODEL_CALL"

    backend = os.getenv("LLM_BACKEND", "openai").lower()
    if backend == "ollama":
        try:
            import json
            import urllib.request

            payload = json.dumps(
                {"model": model_name, "messages": messages, "stream": False}
            ).encode("utf-8")
            req = urllib.request.Request(
                "http://localhost:11434/api/chat",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req) as resp:
                data: dict[str, Any] = json.load(resp)
            _set_last_usage(None)
            return data["message"]["content"]
        except Exception as exc:  # pragma: no cover - passthrough
            raise RuntimeError("Ollama API call failed") from exc

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        usage = None
        if getattr(response, "usage", None):
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        _set_last_usage(usage)
        return content
    except ImportError:
        pass
    except Exception as exc:  # pragma: no cover - passthrough
        raise RuntimeError("OpenAI API call failed") from exc


def ollama_healthcheck() -> bool:
    try:
        import urllib.request

        with urllib.request.urlopen("http://localhost:11434/api/tags") as resp:
            return resp.status == 200
    except Exception:
        return False

    try:
        import json
        import urllib.error
        import urllib.request

        payload = json.dumps(
            {"model": model_name, "messages": messages, "temperature": 0}
        ).encode("utf-8")
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            data: dict[str, Any] = json.load(resp)
        _set_last_usage(data.get("usage"))
        return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="ignore")
        body = body[:500]
        raise RuntimeError(f"OpenAI API error {exc.code}: {body}") from exc
    except Exception as exc:  # pragma: no cover - passthrough
        raise RuntimeError("OpenAI API call failed") from exc
