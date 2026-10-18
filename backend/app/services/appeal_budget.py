"""Process-local call budgets, paired-request state, and IP improvement limits."""
from __future__ import annotations

import hashlib
import json
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock

from app.models.config import settings

LOCK = RLock()
SESSIONS: dict = {}
DAILY: dict = {}
CURRENT = ContextVar("appeal_call_budget", default=None)


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class Flow:
    attempts: int = 0
    stopped: bool = False


@dataclass
class Budget:
    calls: int = 0
    retry_allowance: int = 0
    started: float = field(default_factory=time.monotonic)
    stopped: bool = False
    limit: int | None = None
    last_model: str | None = None
    last_status: str | None = None
    flow: Flow = field(default_factory=Flow)
    attempts: int = 0
    allow_key_failover: bool = False

    def remaining_seconds(self):
        return max(0.0, settings.REQUEST_TIME_BUDGET_S - (time.monotonic() - self.started))

    def consume(self):
        with LOCK:
            if self.stopped or self.flow.stopped or self.remaining_seconds() <= 0:
                raise BudgetExceeded("Generation time or provider budget exhausted")
            if self.calls >= (self.limit if self.limit is not None else settings.MAX_GEMINI_CALLS_PER_REQUEST + self.retry_allowance):
                raise BudgetExceeded("Gemini call budget exhausted")
            if self.flow.attempts >= settings.MAX_GEMINI_PROVIDER_ATTEMPTS_PER_FLOW:
                raise BudgetExceeded("Full-flow provider attempt ceiling reached")
            if self.limit == 1 and self.attempts >= 1:
                raise BudgetExceeded("Single-attempt improvement limit reached")
            self.flow.attempts += 1
            self.attempts += 1

    def account(self, billable):
        with LOCK:
            self.calls += int(billable)

    def stop_flow(self):
        self.stopped = self.flow.stopped = True


def normalized(value):
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in sorted(value.items())}
    if isinstance(value, str):
        return " ".join(value.split()).casefold()
    return value


def session(payload, client="local"):
    # A changed provider configuration must not reuse an old provider result.
    key = hashlib.sha256(json.dumps([client, normalized(payload), settings.GEMINI_MODEL,
                                    settings.GEMINI_FALLBACK_MODELS], sort_keys=True).encode()).hexdigest()
    now = time.monotonic()
    with LOCK:
        for old in list(SESSIONS):
            if now - SESSIONS[old]["created"] >= 3600:
                del SESSIONS[old]
        if key not in SESSIONS:
            flow = Flow()
            SESSIONS[key] = {"created": now, "budget": Budget(flow=flow),
                             "remaining_budget": Budget(flow=flow), "flow": flow,
                             "results": {}, "partial": False}
        return SESSIONS[key]


def improvement_day():
    return datetime.now(timezone.utc).date().isoformat()


def refund_improvement(client, day):
    """Release this reservation only; never subtract from a different UTC day."""
    with LOCK:
        key = (day, client)
        if key in DAILY:
            DAILY[key] = max(0, DAILY[key] - 1)
        return max(0, settings.DAILY_IMPROVE_LIMIT - DAILY.get((improvement_day(), client), 0))


def improvement_uses(client, consume=False, day=None):
    day = day or improvement_day()
    with LOCK:
        for key in list(DAILY):
            if key[0] != day:
                del DAILY[key]
        key = (day, client)
        used = DAILY.get(key, 0)
        if consume and used < settings.DAILY_IMPROVE_LIMIT:
            DAILY[key] = used + 1
            used += 1
            allowed = True
        else:
            allowed = not consume
        return allowed, max(0, settings.DAILY_IMPROVE_LIMIT - used)
