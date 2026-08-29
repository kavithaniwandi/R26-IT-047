import json
from datetime import datetime, timezone
from pathlib import Path

from app.models.config import settings


STATE_FILE = Path(__file__).resolve().with_name("credit_monitor_state.json")

_key_state: dict[str, dict] = {}


def _default_state() -> dict:
    return {
        "calls": 0,
        "failures": 0,
        "exhausted": False,
        "last_success": None,
        "last_failure": None,
        "exhausted_at": None,
    }


def _save_state() -> None:
    try:
        STATE_FILE.write_text(json.dumps(_key_state, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"Credit monitor save failed: {exc}")


def _load_state() -> None:
    global _key_state
    try:
        if STATE_FILE.exists():
            _key_state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            print(f"Credit monitor state loaded from {STATE_FILE}")
    except Exception as exc:
        print(f"Credit monitor load failed - starting fresh: {exc}")
        _key_state = {}


_load_state()


def _key_label(index: int) -> str:
    return f"gemini_key_{index}"


def _gemini_keys_indexed() -> list[tuple[int, str]]:
    keys = [
        (1, getattr(settings, "GEMINI_API_KEY", "")),
        (2, getattr(settings, "GEMINI_API_KEY2", "")),
        (3, getattr(settings, "GEMINI_API_KEY3", "")),
        (4, getattr(settings, "GEMINI_API_KEY4", "")),
        (5, getattr(settings, "GEMINI_API_KEY5", "")),
        (6, getattr(settings, "GEMINI_API_KEY6", "")),
        (7, getattr(settings, "GEMINI_API_KEY7", "")),
        (8, getattr(settings, "GEMINI_API_KEY8", "")),
        (9, getattr(settings, "GEMINI_API_KEY9", "")),
        (10, getattr(settings, "GEMINI_API_KEY10", "")),
        (11, getattr(settings, "GEMINI_API_KEY11", "")),
    ]
    return [(index, key) for index, key in keys if key]


def _provider_state(provider: str) -> dict:
    if provider not in _key_state:
        _key_state[provider] = _default_state()
    return _key_state[provider]


def record_success(provider: str) -> None:
    """Record a successful provider generation in persistent state."""
    state = _provider_state(provider)
    state["calls"] += 1
    state["exhausted"] = False
    state["last_success"] = datetime.now(timezone.utc).isoformat()
    _save_state()


def record_failure(provider: str, reason: str = "") -> None:
    """Record a provider failure in persistent state."""
    state = _provider_state(provider)
    state["failures"] += 1
    state["last_failure"] = reason
    _save_state()


def mark_exhausted(provider: str) -> None:
    """Mark a provider as exhausted after quota or rate-limit failures."""
    state = _provider_state(provider)
    state["exhausted"] = True
    state["exhausted_at"] = datetime.now(timezone.utc).isoformat()
    _save_state()
    print(f"[CreditMonitor] {provider} marked exhausted")


def reset_provider(provider: str) -> None:
    """Reset one provider after daily quota refresh or manual recovery."""
    state = _provider_state(provider)
    state["exhausted"] = False
    state["exhausted_at"] = None
    state["failures"] = 0
    _save_state()
    print(f"[CreditMonitor] {provider} manually reset")


def reset_all() -> None:
    """Reset all provider state."""
    global _key_state
    _key_state = {}
    _save_state()
    print("[CreditMonitor] All providers reset")


def get_status() -> dict:
    """Return current provider health and usage state."""
    gemini_keys = _gemini_keys_indexed()
    hf_configured = bool(getattr(settings, "HF_API_KEY", None))

    providers = []
    for index, _key in gemini_keys:
        label = _key_label(index)
        state = _key_state.get(label, {})

        if state.get("exhausted", False):
            status_label = "Exhausted"
        elif state.get("calls", 0) > 0:
            status_label = "Active"
        else:
            status_label = "Standby"

        providers.append({
            "provider": label.upper(),
            "type": "gemini",
            "configured": True,
            "calls_today": state.get("calls", 0),
            "failures": state.get("failures", 0),
            "exhausted": state.get("exhausted", False),
            "status_label": status_label,
            "exhausted_at": state.get("exhausted_at"),
            "last_success": state.get("last_success"),
            "last_failure": state.get("last_failure"),
        })

    hf_state = _key_state.get("huggingface-featherless", {})
    if hf_state.get("exhausted", False):
        hf_status = "Exhausted"
    elif hf_state.get("calls", 0) > 0:
        hf_status = "Active"
    elif hf_configured:
        hf_status = "Standby"
    else:
        hf_status = "Not configured"

    providers.append({
        "provider": "HUGGINGFACE_LLAMA",
        "type": "huggingface",
        "configured": hf_configured,
        "calls_today": hf_state.get("calls", 0),
        "failures": hf_state.get("failures", 0),
        "exhausted": hf_state.get("exhausted", False),
        "status_label": hf_status,
        "exhausted_at": hf_state.get("exhausted_at"),
        "last_success": hf_state.get("last_success"),
        "last_failure": hf_state.get("last_failure"),
    })

    gemini_exhausted = bool(gemini_keys) and all(
        _key_state.get(_key_label(index), {}).get("exhausted", False)
        for index, _key in gemini_keys
    )
    hf_exhausted = hf_state.get("exhausted", False)

    if gemini_exhausted and hf_exhausted:
        health = "critical"
        message = "All providers exhausted - only template fallback available"
    elif gemini_exhausted:
        health = "warning"
        message = "All Gemini keys exhausted - running on HuggingFace fallback"
    elif any(_key_state.get(_key_label(index), {}).get("exhausted", False) for index, _key in gemini_keys):
        health = "degraded"
        message = "Some Gemini keys exhausted - remaining keys active"
    else:
        health = "healthy"
        message = "All providers operational"

    return {
        "health": health,
        "message": message,
        "providers": providers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
