"""
Severity queue sanity test - no MongoDB needed.

Run from backend/:
    .\venv\Scripts\python.exe test_severity_queue.py

It feeds hand-written cases with expected severities through the same
classifier wrapper the app uses, then reports over-/under-triage and a
"bare symptom" probe to check whether any symptom text pushes to HIGH.
"""
import asyncio
import importlib
import inspect
import sys

MODULE = "app.models.severity_service"
CANDIDATES = [
    "classify_note",
    "classify_severity",
    "predict_severity",
    "classify",
    "predict",
    "get_severity",
]

mod = importlib.import_module(MODULE)
fn = next((getattr(mod, name) for name in CANDIDATES if hasattr(mod, name)), None)
if fn is None:
    print(f"Could not find a classifier function in {MODULE}. Public callables:")
    for name, obj in inspect.getmembers(mod, callable):
        if not name.startswith("_"):
            print("  ", name, inspect.signature(obj))
    print("\nAdd the right name to CANDIDATES at the top of this script.")
    sys.exit(1)

PARAMS = inspect.signature(fn).parameters
HAS_MODE = "mode" in PARAMS
print(f"Using {MODULE}.{fn.__name__}{inspect.signature(fn)}\n")


def classify(note, age, mode):
    kwargs = {}
    if "age" in PARAMS:
        kwargs["age"] = age
    if HAS_MODE:
        kwargs["mode"] = mode
    out = fn(note, **kwargs)
    if inspect.isawaitable(out):
        out = asyncio.run(out)
    return out


RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

# (label, note, age, expected)
CASES = [
    # LOW
    ("low: mild headache", "mild headache since this morning", 30, "LOW"),
    ("low: cold", "runny nose and sore throat for two days", 25, "LOW"),
    ("low: minor cut", "minor cut on finger, bleeding stopped", 35, "LOW"),
    ("low: mild cough", "mild cough, no fever", 40, "LOW"),
    ("low: itchy rash", "itchy rash on arm", 22, "LOW"),
    ("low: muscle ache", "mild muscle ache after work", 33, "LOW"),
    ("low: refill", "requesting medication refill, no complaints", 55, "LOW"),
    # Negation traps
    ("neg: mild headache", "no chest pain, no shortness of breath, mild headache", 30, "LOW"),
    ("neg: sore throat", "denies fever or vomiting, sore throat only", 26, "LOW"),
    # MEDIUM
    ("med: fever+aches", "fever 38.5 for two days with body aches", 28, "MEDIUM"),
    ("med: vomiting", "vomiting three times since yesterday, able to drink fluids", 34, "MEDIUM"),
    ("med: sprain", "sprained ankle, swollen, can bear some weight", 27, "MEDIUM"),
    ("med: wheeze", "persistent cough for a week with mild wheeze", 45, "MEDIUM"),
    ("med: diarrhoea", "diarrhoea for two days, mild dehydration", 30, "MEDIUM"),
    ("med: abd pain", "moderate abdominal pain for a day, no vomiting", 38, "MEDIUM"),
    ("med: raised BP", "high blood pressure reading, mild headache, no other symptoms", 60, "MEDIUM"),
    # HIGH
    ("high: SOB+chest", "shortness of breath and chest tightness, dizziness", 45, "HIGH"),
    ("high: severe abd", "severe abdominal pain with vomiting and fever", 52, "HIGH"),
    ("high: stiff neck", "fever with stiff neck and severe headache", 19, "HIGH"),
    ("high: heavy bleed", "deep wound with heavy bleeding, pressure applied", 30, "HIGH"),
    ("high: elderly confused", "elderly patient confused, fever, not eating", 82, "HIGH"),
    ("high: child breathing", "child with high fever and difficulty breathing", 3, "HIGH"),
    ("high: pregnant bleed", "pregnant woman with severe abdominal pain and bleeding", 29, "HIGH"),
    # CRITICAL
    ("crit: unconscious", "unconscious, not responding", 50, "CRITICAL"),
    ("crit: arrest", "not breathing, cardiac arrest", 60, "CRITICAL"),
    ("crit: MI", "severe chest pain radiating to left arm, sweating, collapsed", 58, "CRITICAL"),
    ("crit: seizure", "seizure ongoing, unresponsive", 12, "CRITICAL"),
    ("crit: massive bleed", "massive bleeding, cannot stop", 35, "CRITICAL"),
]

BARE = [
    "headache",
    "cough",
    "fever",
    "pain",
    "dizziness",
    "nausea",
    "tired",
    "sore throat",
    "rash",
    "back pain",
    "cold",
    "vomiting",
]


def pick(result, key, default=None):
    return result.get(key, default) if isinstance(result, dict) else default


def run(mode):
    print("=" * 100)
    print(f"MODE: {mode}")
    print("=" * 100)
    print(f"{'case':26} {'exp':9} {'got':9} {'p_high':>7} {'method':10} {'trigger/rules'}")
    exact = over = under = high_to_low = 0
    dist = {key: 0 for key in RANK}
    for label, note, age, expected in CASES:
        try:
            result = classify(note, age, mode)
        except Exception as exc:  # noqa: BLE001
            print(f"{label:26} {expected:9} ERROR: {exc}")
            continue
        got = pick(result, "severity", "?")
        high_probability = (pick(result, "scores", {}) or {}).get("HIGH")
        trigger = pick(result, "critical_trigger") or pick(result, "matched_rules") or ""
        flag = ""
        if got in RANK:
            dist[got] += 1
            if RANK[got] == RANK[expected]:
                exact += 1
            elif RANK[got] > RANK[expected]:
                over += 1
                flag = "  <-- OVER"
            else:
                under += 1
                flag = "  <-- UNDER"
                if expected == "HIGH" and got == "LOW":
                    high_to_low += 1
        high_probability_text = (
            f"{high_probability:.3f}" if isinstance(high_probability, (int, float)) else "-"
        )
        print(
            f"{label:26} {expected:9} {got:9} {high_probability_text:>7} "
            f"{str(pick(result, 'method', '')):10} {trigger}{flag}"
        )
    count = len(CASES)
    print(f"\nexact {exact}/{count}   over-triage {over}   under-triage {under}   HIGH->LOW {high_to_low}")
    print("predicted distribution:", dist)

    print("\nBare-symptom probe (age 30) - if most are HIGH, symptom presence alone is driving it:")
    for word in BARE:
        try:
            result = classify(word, 30, mode)
            high_probability = (pick(result, "scores", {}) or {}).get("HIGH")
            high_probability_text = (
                f"{high_probability:.3f}" if isinstance(high_probability, (int, float)) else "-"
            )
            print(f"  {word:14} -> {pick(result, 'severity', '?'):9} p_high={high_probability_text}")
        except Exception as exc:  # noqa: BLE001
            print(f"  {word:14} ERROR: {exc}")
    print()


if HAS_MODE:
    for mode_name in ("ml", "rule_based"):
        run(mode_name)
else:
    run("default")
