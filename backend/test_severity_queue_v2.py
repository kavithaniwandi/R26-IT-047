"""
Severity queue harness v2 - mirrors what PriorityApplication.jsx sends to
/api/severity/classify (no vitals, red-flag checkboxes, condition_group, symptoms).

Run from backend/:
    .\venv\Scripts\python.exe test_severity_queue_v2.py

ML mode is run twice:
  A) "app"      - exactly as the app calls it (NO vitals)
  B) "+vitals"  - same case with plausible vitals attached (sensitivity probe,
                  NOT ground truth). If B differs a lot from A, missing vitals
                  are what is driving the ML output in the real app.
rule_based mode is run once.
"""
from app.models.severity_service import classify_note

RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}

# Key names follow the notebook's VITAL_COLS. If predict_severity_ml expects
# different keys, edit here.
VITALS = {
    "LOW": {"vital_hr": 72, "vital_spo2": 98, "vital_sbp": 120, "vital_rr": 16, "vital_temp": 36.8, "pain_score": 2},
    "MEDIUM": {"vital_hr": 92, "vital_spo2": 96, "vital_sbp": 130, "vital_rr": 18, "vital_temp": 38.2, "pain_score": 5},
    "HIGH": {"vital_hr": 118, "vital_spo2": 91, "vital_sbp": 95, "vital_rr": 26, "vital_temp": 38.9, "pain_score": 8},
}

# Valid condition_group names are whatever the trained label encoder saw
# (the exported 'condition_groups' list). "Respiratory" appears in real archives;
# fill in the others from that list. Unknown values fall back to class priors.
RESP = "Respiratory"
UNK = "Unknown"

# label, note, age, expected, red_flags, condition_group
CASES = [
    ("low: mild headache", "mild headache since this morning", 30, "LOW", [], UNK),
    ("low: cold", "runny nose and sore throat for two days", 25, "LOW", [], UNK),
    ("low: minor cut", "minor cut on finger, bleeding stopped", 35, "LOW", [], UNK),
    ("low: mild cough", "mild cough, no fever", 40, "LOW", [], RESP),
    ("low: itchy rash", "itchy rash on arm", 22, "LOW", [], UNK),
    ("low: muscle ache", "mild muscle ache after work", 33, "LOW", [], UNK),
    ("low: refill", "requesting medication refill, no complaints", 55, "LOW", [], UNK),
    ("neg: mild headache", "no chest pain, no shortness of breath, mild headache", 30, "LOW", [], UNK),
    ("neg: sore throat", "denies fever or vomiting, sore throat only", 26, "LOW", [], UNK),
    ("med: fever+aches", "fever 38.5 for two days with body aches", 28, "MEDIUM", [], UNK),
    ("med: vomiting", "vomiting three times since yesterday, able to drink fluids", 34, "MEDIUM", [], UNK),
    ("med: sprain", "sprained ankle, swollen, can bear some weight", 27, "MEDIUM", [], UNK),
    ("med: wheeze", "persistent cough for a week with mild wheeze", 45, "MEDIUM", [], RESP),
    ("med: diarrhoea", "diarrhoea for two days, mild dehydration", 30, "MEDIUM", [], UNK),
    ("med: abd pain", "moderate abdominal pain for a day, no vomiting", 38, "MEDIUM", [], UNK),
    ("med: raised BP", "high blood pressure reading, mild headache, no other symptoms", 60, "MEDIUM", [], UNK),
    ("high: SOB+chest", "shortness of breath and chest tightness, dizziness", 45, "HIGH", ["breathing_difficulty", "chest_pain"], RESP),
    ("high: severe abd", "severe abdominal pain with vomiting and fever", 52, "HIGH", [], UNK),
    ("high: stiff neck", "fever with stiff neck and severe headache", 19, "HIGH", [], UNK),
    ("high: heavy bleed", "deep wound with heavy bleeding, pressure applied", 30, "HIGH", ["active_bleeding"], UNK),
    ("high: elderly confused", "elderly patient confused, fever, not eating", 82, "HIGH", [], UNK),
    ("high: child breathing", "child with high fever and difficulty breathing", 3, "HIGH", ["breathing_difficulty"], RESP),
    ("high: pregnant bleed", "pregnant woman with severe abdominal pain and bleeding", 29, "HIGH", ["active_bleeding"], UNK),
    ("crit: unconscious", "unconscious, not responding", 50, "CRITICAL", ["syncope"], UNK),
    ("crit: arrest", "not breathing, cardiac arrest", 60, "CRITICAL", ["breathing_difficulty"], UNK),
    ("crit: MI", "severe chest pain radiating to left arm, sweating, collapsed", 58, "CRITICAL", ["chest_pain", "syncope"], UNK),
    ("crit: seizure", "seizure ongoing, unresponsive", 12, "CRITICAL", ["seizure"], UNK),
    ("crit: massive bleed", "massive bleeding, cannot stop", 35, "CRITICAL", ["active_bleeding"], UNK),
    # extra guards for the negation fix (should NOT be stripped away)
    ("guard: cannot breathe", "not able to breathe properly", 50, "HIGH", ["breathing_difficulty"], RESP),
    ("guard: no urine", "no urine output for a day, weak", 60, "MEDIUM", [], UNK),
]

BARE = ["headache", "cough", "fever", "pain", "dizziness", "nausea", "tired",
        "sore throat", "rash", "back pain", "cold", "vomiting"]


def call(note, age, mode, flags, cg, vitals=None):
    kw = dict(
        clinical_note=note, age=age, mode=mode, source="TRIAGE",
        condition_group=cg,
        has_red_flag=1 if flags else 0,
        red_flag_count=len(flags),
        rf_flags={f: 1 for f in flags},
        symptoms=note,
    )
    if vitals is not None:
        kw["vitals"] = vitals
    return classify_note(**kw)


def sc(result, key):
    value = (result.get("scores") or {}).get(key)
    return f"{value:.2f}" if isinstance(value, (int, float)) else "-"


def tally(rows, key):
    exact = over = under = h2l = 0
    dist = {item: 0 for item in RANK}
    for row in rows:
        got, expected = row[key], row["exp"]
        if got not in RANK:
            continue
        dist[got] += 1
        if RANK[got] == RANK[expected]:
            exact += 1
        elif RANK[got] > RANK[expected]:
            over += 1
        else:
            under += 1
            if expected == "HIGH" and got == "LOW":
                h2l += 1
    return f"exact {exact}/{len(rows)}  over {over}  under {under}  HIGH->LOW {h2l}  dist {dist}"


def main():
    print("=" * 110)
    print("ML: A = as the app calls it (no vitals) | B = with plausible vitals attached")
    print("=" * 110)
    print(f"{'case':24} {'exp':9} | {'A got':9} {'pH':>5} {'pL':>5} | {'B got':9} {'pH':>5} {'pL':>5} | note")
    ml_rows = []
    for label, note, age, expected, flags, condition_group in CASES:
        app_result = call(note, age, "ml", flags, condition_group)
        vitals_result = (
            call(note, age, "ml", flags, condition_group, VITALS[expected])
            if expected in VITALS
            else None
        )
        row = {
            "exp": expected,
            "A": app_result.get("severity", "?"),
            "B": (vitals_result or app_result).get("severity", "?"),
        }
        ml_rows.append(row)
        mark = ""
        if app_result.get("critical_trigger"):
            mark = f"trigger={app_result['critical_trigger']}"
        elif RANK.get(row["A"], 0) > RANK[expected]:
            mark = "A:OVER"
        elif RANK.get(row["A"], 0) < RANK[expected]:
            mark = "A:UNDER"
        vitals_summary = (
            f"{row['B']:9} {sc(vitals_result, 'HIGH'):>5} {sc(vitals_result, 'LOW'):>5}"
            if vitals_result
            else f"{'(n/a)':9} {'-':>5} {'-':>5}"
        )
        print(
            f"{label:24} {expected:9} | {row['A']:9} {sc(app_result, 'HIGH'):>5} "
            f"{sc(app_result, 'LOW'):>5} | {vitals_summary} | {mark}"
        )
    print("\nA (app-shaped):", tally(ml_rows, "A"))
    print("B (+vitals)   :", tally(ml_rows, "B"))

    print("\nBare-symptom probe, ML as the app calls it (age 30):")
    for word in BARE:
        result = call(word, 30, "ml", [], UNK)
        print(f"  {word:14} -> {result.get('severity', '?'):9} pH={sc(result, 'HIGH')} pL={sc(result, 'LOW')}")

    print("\n" + "=" * 110)
    print("RULE_BASED")
    print("=" * 110)
    rule_rows = []
    for label, note, age, expected, flags, condition_group in CASES:
        result = call(note, age, "rule_based", flags, condition_group)
        got = result.get("severity", "?")
        rule_rows.append({"exp": expected, "R": got})
        trigger = result.get("critical_trigger") or result.get("matched_rules") or ""
        flag = (
            "OVER"
            if RANK.get(got, 0) > RANK[expected]
            else ("UNDER" if RANK.get(got, 0) < RANK[expected] else "")
        )
        print(f"{label:24} {expected:9} {got:9} {flag:6} {trigger}")
    print("\nrule_based:", tally(rule_rows, "R"))


if __name__ == "__main__":
    main()
