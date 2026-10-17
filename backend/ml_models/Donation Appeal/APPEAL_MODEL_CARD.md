# Donation Appeal Quality Model Card

## Runtime Selection

The backend loads appeal quality artifacts from `APPEAL_MODEL_DIR` when that
environment variable is set. If it is unset, the backend defaults to
`backend/ml_models/Donation Appeal`, which is the restored v1 live folder.

Training must write to a versioned folder. `train_quality.py` defaults to
`backend/ml_models/Donation Appeal/v2_paper_protocol` and should not overwrite
the live root artifacts.

## v1 Original Live Model

- Location: `backend/ml_models/Donation Appeal`
- Training date from original file timestamps observed before retraining:
  `2026-08-28 19:10`
- Restore source: tracked repository artifacts. The empty
  `backup_20261009_150802` folder could not be used for restoration.
- Stored training row count: not stored in `appeal_quality_config.joblib`
- Stored split indices: not stored in v1
- English TF-IDF: word 1-2 grams, max features 25,000, vocabulary 25,000
- Sinhala TF-IDF: `char_wb` 3-5 grams, max features 8,000, vocabulary 7,230
- Tamil TF-IDF: `char_wb` 3-5 grams, max features 8,000, vocabulary 6,982
- LSA dimensions: English 150, Sinhala 50, Tamil 50
- Handcrafted features: 13
- Boundary tolerance: 0.25

Parity on the v2 saved held-out indices (`n=1,136`):

| Metric | Value | 95% bootstrap interval |
|---|---:|---:|
| Accuracy | 0.919894 | 0.904049-0.934859 |
| Balanced accuracy | 0.920365 | 0.904787-0.935193 |
| Macro-F1 | 0.920697 | 0.905127-0.935512 |
| MAE | 0.147266 | 0.130674-0.164315 |
| R2 | 0.911148 | 0.895239-0.925111 |

## v2 Paper-Protocol Model

- Location: `backend/ml_models/Donation Appeal/v2_paper_protocol`
- Corpus file: `Donation_Appeal_MASTER_FINAL_v8_7100.csv`
- Corpus rows after filtering/thinning: 5,627
- Training rows: 4,491
- Test rows: 1,136
- Seed: 42
- Split: `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)`,
  first fold as test
- Near-duplicate grouping: connected components within language where TF-IDF
  cosine similarity is greater than 0.8
- Saved selected indices: `appeal_quality_selected_indices.npy`
- Saved test indices: `appeal_quality_test_indices.npy`
- English TF-IDF: word 1-2 grams, max features 25,000, vocabulary 25,000
- Sinhala TF-IDF: `char_wb` 3-5 grams, max features 8,000, vocabulary 7,230
- Tamil TF-IDF: `char_wb` 3-5 grams, max features 8,000, vocabulary 7,064
- LSA dimensions: English 150, Sinhala 50, Tamil 50
- Handcrafted features: 13
- Boundary tolerance: 0.25

Parity on the saved held-out indices (`n=1,136`):

| Metric | Value | 95% bootstrap interval |
|---|---:|---:|
| Accuracy | 0.789613 | 0.765845-0.813380 |
| Balanced accuracy | 0.792403 | 0.768972-0.814790 |
| Macro-F1 | 0.795555 | 0.771942-0.817428 |
| MAE | 0.340438 | 0.314077-0.367236 |
| R2 | 0.718073 | 0.688284-0.745379 |
