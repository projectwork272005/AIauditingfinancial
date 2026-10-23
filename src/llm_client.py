"""Minimal client for OpenAI-compatible chat-completions APIs.

Works with Volcano Engine Ark (including the Agent Plan endpoint used in this
project) and other OpenAI-compatible providers (DeepSeek, Alibaba, OpenAI, Gemini, OpenRouter):
only the base URL, model name and key differ. Uses `requests` only.

Two robustness rules, both recorded in the call log:
* If the key's environment variable is empty, the request is sent without an
  Authorization header, for set-ups where the network proxy injects the key
  (a "network secret"). A 401 then reports the missing key clearly.
* If the provider rejects an optional parameter (response_format, thinking,
  reasoning_effort) with HTTP 400, that parameter is dropped once and the call
  is retried; the dropped parameter names are logged in `dropped_params`.

The client never invents output. A failed call returns an error record, which
the runner logs; it is retried on a later run, never filled in.
"""

import os
import random
import time

import requests

RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504}


OPTIONAL_PARAMS = ("response_format", "thinking", "reasoning_effort", "reasoning", "enable_thinking")


def key_env_names(model_cfg: dict) -> list[str]:
    names = model_cfg["api_key_env"]
    return [names] if isinstance(names, str) else list(names)


def api_key_for(model_cfg: dict) -> str:
    """Key from the first listed environment variable that is set; empty string
    if none is set (the network proxy may inject the key)."""
    for name in key_env_names(model_cfg):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return ""


def auth_headers(model_cfg: dict) -> dict:
    key = api_key_for(model_cfg)
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    return headers


def list_models(model_cfg: dict, timeout: int = 30) -> list[str]:
    url = model_cfg["base_url"].rstrip("/") + "/models"
    resp = requests.get(url, headers=auth_headers(model_cfg), timeout=timeout)
    resp.raise_for_status()
    return sorted(m.get("id", "") for m in resp.json().get("data", []))


def build_payload(model_cfg: dict, gen_cfg: dict, system: str, user: str) -> dict:
    payload = {
        "model": model_cfg["model"],
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        model_cfg.get("max_tokens_param", "max_tokens"): gen_cfg["max_output_tokens"],
    }
    if model_cfg.get("temperature") is not None:
        payload["temperature"] = model_cfg["temperature"]
    if gen_cfg.get("json_mode"):
        payload["response_format"] = {"type": "json_object"}
    payload.update(model_cfg.get("extra_body", {}))
    return payload


def chat(model_cfg: dict, gen_cfg: dict, system: str, user: str) -> dict:
    """Send one request with retries. Returns a dict that always contains
    'ok' (bool), 'attempts', 'latency_s', and either the response fields or 'error'."""
    url = model_cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = auth_headers(model_cfg)
    payload = build_payload(model_cfg, gen_cfg, system, user)
    dropped = []
    last_error = None
    t0 = time.time()
    for attempt in range(1, gen_cfg["max_retries"] + 1):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=gen_cfg["timeout_s"])
            if resp.status_code == 200:
                data = resp.json()
                choice = data["choices"][0]
                content = (choice.get("message") or {}).get("content") or ""
                return {
                    "ok": bool(content.strip()),
                    "error": None if content.strip() else "empty content",
                    "content": content,
                    "finish_reason": choice.get("finish_reason"),
                    "model_returned": data.get("model"),
                    "response_id": data.get("id"),
                    "system_fingerprint": data.get("system_fingerprint"),
                    "usage": data.get("usage") or {},
                    "attempts": attempt,
                    "latency_s": round(time.time() - t0, 2),
                    "http_status": 200,
                    "request_params": {k: v for k, v in payload.items() if k != "messages"},
                    "dropped_params": dropped,
                }
            last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
            if resp.status_code == 401:
                last_error += (f" (none of {key_env_names(model_cfg)} is set in the environment)"
                               if not api_key_for(model_cfg) else "")
                break
            if resp.status_code == 400:
                rejected = [p for p in OPTIONAL_PARAMS if p in payload and p in resp.text]
                if rejected:
                    for p in rejected:
                        payload.pop(p)
                        dropped.append(p)
                    continue  # retry at once without the rejected optional parameter(s)
            if resp.status_code not in RETRYABLE:
                break
        except (requests.RequestException, ValueError, KeyError, IndexError) as exc:
            last_error = f"{type(exc).__name__}: {exc}"
        time.sleep(min(2 ** attempt, 60) + random.uniform(0, 1))
    return {"ok": False, "error": last_error, "attempts": attempt,
            "latency_s": round(time.time() - t0, 2), "dropped_params": dropped,
            "request_params": {k: v for k, v in payload.items() if k != "messages"}}
