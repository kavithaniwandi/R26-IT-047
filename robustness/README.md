# Severity Robustness Harness

This folder contains a read-only robustness harness for the live severity
triage bundle.

The script requires the NHAMCS relabelled CSV used by the training notebook:

```powershell
python robustness\severity_robustness.py `
  --data C:\path\to\nhamcs_2022_camp_relabeled_v2.csv `
  --out-dir robustness\outputs
```

Exact parity with `backend/app/models/severity_model/metrics.json` requires the
pinned runtime versions recorded in that manifest. If you only want to inspect
the script on a mismatched environment, add:

```powershell
--allow-version-mismatch
```

The script reproduces the notebook split exactly:

```python
StratifiedGroupKFold(10, shuffle=True, random_state=42)
idx_test = folds[0][1]
idx_val = folds[1][1]
```

It writes:

- `severity_robustness_results.csv`
- `severity_robustness_summary.md`

The NHAMCS CSV is not committed in this repository, so the script will fail
clearly until `--data` points to that file.
