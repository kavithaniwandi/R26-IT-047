# Severity ML Probability Arrays

This folder contains legacy probability arrays:

- `val_avg_proba.npy`
- `test_avg_proba.npy`

Observed local metadata on 2026-10-11:

- `val_avg_proba.npy`: shape `(757, 15)`, last modified `2026-08-28 19:10:34`
- `test_avg_proba.npy`: shape `(757, 15)`, last modified `2026-08-28 19:10:34`

These files do **not** match the reported severity split sizes in
`backend/app/models/severity_model/metrics.json` and the training notebook:

- validation: `748`
- test: `740`

No notebook cell or script in this checkout was found that writes these exact
filenames. Do not use these arrays as the source of truth for the reported
`metrics.json` validation or test metrics unless their matching labels and split
provenance are recovered.

The deployed severity thresholds are stored in the shipped
`backend/app/models/severity_model/severity_bundle.joblib`; the copied config
values in `model_config.json` are kept in sync by
`backend/tests/test_threshold_consistency.py`.
