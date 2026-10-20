# Backend tests

Tests are grouped by component. Shared pytest fixtures remain in conftest.py
and are inherited by every group. All original tests, reports, data, and helpers
have been retained.

| Folder | Coverage |
| --- | --- |
| appeals/ | Appeal quality, generation, provider handling, budgets, and repair |
| auth/ | Authentication, roles, and demo-user seeding |
| camps/ | Relief-camp permissions, population forecasts, and YOLO threshold |
| donations/ | Donation requests, donor matching, and pledge expiry |
| ml/ | Flood, landslide, camp suitability, and SOS model artifacts |
| severity/ | Severity models/rules, vitals, complaint mapping, and specialty routing |
| sms/ | Victim messaging and the SMS gateway |
| triage/ | Patient queue policy, session persistence, and sample fixtures |
| data/ | Shared input data used by tests and offline scoring |
| fixtures/ | Shared JSON fixtures |
| reports/ | Preserved reports from previous test and diagnostic runs |
| tools/ | Manual data-driven diagnostics; not collected as pytest tests |

## Running tests

Run these commands from backend/ with the backend virtual environment active:

~~~text
python -m pytest tests --collect-only -q
python -m pytest tests -q
python -m pytest tests/triage -q
python -m pytest tests/auth/test_auth.py -q
~~~

Use isolated test database settings. The shared SQL test fixtures use an
in-memory database; do not point test processes at a shared Mongo database.

The typed-note stress helper requires its training dataset and is run manually:

~~~text
python tests/tools/make_notes.py --data <path-to-NHAMCS-CSV>
~~~

Its default output is tests/reports/typed_note_stress_report.json.
Historical report contents are retained unchanged, including their original
test paths and recorded results.
