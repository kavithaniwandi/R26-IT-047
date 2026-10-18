import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pathlib import Path
from threading import RLock

from app.models.config import settings


STATE_FILE = Path(__file__).resolve().with_name("credit_monitor_state.json")

_key_state: dict[str, dict] = {}
_STATE_LOCK = RLock()


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
    return [(index, key) for index, key in keys if key or _key_label(index) in _key_state]


def _provider_state(provider: str) -> dict:
    if provider not in _key_state:
        _key_state[provider] = _default_state()
    return _key_state[provider]


def is_exhausted(provider: str) -> bool:
    state = _key_state.get(provider, {})
    if state.get("retry_after"):
        try:
            deadline = datetime.fromisoformat(state["retry_after"])
            if datetime.now(timezone.utc) < deadline:
                return True
        except (ValueError, TypeError):
            pass
        state.update(retry_after=None, exhausted=False, exhausted_at=None)
        _save_state()
    if not state.get("exhausted", False):
        return False
    now = datetime.now(timezone.utc)
    try:
        exhausted_at = datetime.fromisoformat(state["exhausted_at"])
        if exhausted_at.tzinfo is None:
            exhausted_at = exhausted_at.replace(tzinfo=timezone.utc)
    except (KeyError, TypeError, ValueError):
        # Legacy records get a finite cooldown instead of remaining dead forever.
        state["exhausted_at"] = now.isoformat()
        _save_state()
        return True
    try:
        local = exhausted_at.astimezone(ZoneInfo("America/Los_Angeles"))
        deadline = (local + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        deadline = deadline.astimezone(timezone.utc)
    except (ZoneInfoNotFoundError, ValueError, OverflowError, OSError):
        deadline = exhausted_at + timedelta(hours=24)
    if now < deadline:
        return True
    state["exhausted"] = False
    state["exhausted_at"] = None
    _save_state()
    return False


def record_success(provider: str) -> None:
    """Record a successful provider generation in persistent state."""
    state = _provider_state(provider)
    state["calls"] += 1
    state["exhausted"] = False
    state["last_success"] = datetime.now(timezone.utc).isoformat()
    state.update(last_status="200", last_checked=state["last_success"], retry_after=None, exhausted_at=None)
    _save_state()


def record_result(provider: str, status: str, cooldown_seconds: float | None = None) -> None:
    """Persist fixed diagnostics only, never provider bodies or credentials."""
    with _STATE_LOCK:
        state = _provider_state(provider)
        now = datetime.now(timezone.utc)
        today = now.date().isoformat()
        if state.get("usage_date") != today:
            state.update(calls=0, failures=0, attempts_today=0, usage_date=today)
        state["attempts_today"] = state.get("attempts_today", 0) + 1
        state.update(last_status=str(status), last_checked=now.isoformat())
        if str(status) == "200":
            state["calls"] += 1
            state.update(last_success=now.isoformat(), exhausted=False, exhausted_at=None, retry_after=None)
        else:
            state["failures"] += 1
            state["last_failure"] = str(status)
            if cooldown_seconds:
                state.update(exhausted=True, exhausted_at=now.isoformat(),
                             retry_after=(now + timedelta(seconds=cooldown_seconds)).isoformat())
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
    state["retry_after"] = None
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
    for index, _ in gemini_keys:
        is_exhausted(_key_label(index))
    hf_configured = bool(getattr(settings, "HF_API_KEY", None))

    providers = []
    for index, _key in gemini_keys:
        label = _key_label(index)
        state = _key_state.get(label, {})
        current_usage = state.get("usage_date", datetime.now(timezone.utc).date().isoformat()) == datetime.now(timezone.utc).date().isoformat()

        if state.get("exhausted", False):
            status_label = "Rate limited" if state.get("last_status") == "429" else "Rejected" if state.get("last_status") in ("401", "403") else "Exhausted"
        elif state.get("last_status") == "200":
            status_label = "Last request OK"
        elif state.get("last_status") in ("401", "403", "429"):
            status_label = "Retry available"
        elif state.get("last_status"):
            status_label = "Last request failed"
        else:
            status_label = "Not checked"

        providers.append({
            "provider": label.upper(),
            "type": "gemini",
            "configured": True,
            "calls_today": state.get("calls", 0) if current_usage else 0,
            "failures": state.get("failures", 0),
            "exhausted": state.get("exhausted", False),
            "status_label": status_label,
            "exhausted_at": state.get("exhausted_at"),
            "last_success": state.get("last_success"),
            "last_failure": state.get("last_failure"),
            "last_status": state.get("last_status"),
            "last_checked": state.get("last_checked"),
            "retry_after": state.get("retry_after"),
            "attempts_today": state.get("attempts_today", 0) if current_usage else 0,
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
        message = "All configured providers have recorded failures; a local template may be used."
    elif gemini_exhausted:
        health = "warning"
        message = "All Gemini keys are currently marked unavailable; this is recorded status, not a live quota check."
    elif any(_key_state.get(_key_label(index), {}).get("exhausted", False) for index, _key in gemini_keys):
        health = "degraded"
        message = "Some keys are unavailable; other configured keys can be tried. Status reflects recorded requests."
    else:
        health = "healthy"
        health = "healthy" if any(_key_state.get(_key_label(index), {}).get("last_status") == "200" for index, _ in gemini_keys) else "unknown"
        message = "Status reflects recorded requests, not a live quota check."

    return {
        "health": health,
        "message": message,
        "providers": providers,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
