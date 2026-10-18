# Severity Robustness Summary

## Split

- Data rows after label filtering: 7578
- Train n: 6090; validation n: 748; test n: 740
- Split code: `StratifiedGroupKFold(10, shuffle=True, random_state=42)`; test fold `folds[0][1]`, validation fold `folds[1][1]`.
- Label column: `camp_triage_label_final`; group column: `model_input_text`.
- Injury column used: `injury_flag`
- Record ID column for joining to raw NHAMCS injury indicator: NOT FOUND IN CSV.

## Baseline

- Balanced accuracy: 0.885105 (metrics.json test: 0.885105)
- Macro-F1: 0.882457 (metrics.json test: 0.882457)
- HIGH recall: 0.905213 (metrics.json test: 0.905213)
- HIGH-to-LOW count: 5 (metrics.json test: 5)

## Columns And Units

| Column | Unit | Valid range used for clipping |
|---|---:|---:|
| `vital_hr` | beats/min | 20.0-250.0 |
| `vital_spo2` | % | 50.0-100.0 |
| `vital_sbp` | mmHg | 50.0-300.0 |
| `vital_rr` | breaths/min | 4.0-80.0 |
| `vital_temp` | C | 30.0-43.0 |
| `pain_score` | 0-10 integer scale | 0.0-10.0 |

Red-flag columns: rf_breathing_difficulty, rf_chest_pain, rf_focal_neurologic_deficit, rf_active_bleeding, rf_syncope, rf_seizure.

## Results

The full machine-readable table is in `severity_robustness_results.csv`. Intervals are empirical 2.5th and 97.5th percentiles over repeats.

### baseline

| experiment   | level   | metric            |     mean |     p2_5 |    p97_5 |   n_rows |   n_high |   repeats |   baseline_mean |   delta_from_baseline |   injury_col |
|:-------------|:--------|:------------------|---------:|---------:|---------:|---------:|---------:|----------:|----------------:|----------------------:|-------------:|
| baseline     | test    | balanced_accuracy | 0.885105 | 0.885105 | 0.885105 |      740 |      211 |         1 |             nan |                   nan |          nan |
| baseline     | test    | macro_f1          | 0.882457 | 0.882457 | 0.882457 |      740 |      211 |         1 |             nan |                   nan |          nan |
| baseline     | test    | high_recall       | 0.905213 | 0.905213 | 0.905213 |      740 |      211 |         1 |             nan |                   nan |          nan |
| baseline     | test    | high_to_low       | 5        | 5        | 5        |      740 |      211 |         1 |             nan |                   nan |          nan |

### missing_vitals

| experiment     | level   | metric            |      mean |      p2_5 |     p97_5 |   n_rows |   n_high |   repeats |   baseline_mean |   delta_from_baseline |   injury_col |
|:---------------|:--------|:------------------|----------:|----------:|----------:|---------:|---------:|----------:|----------------:|----------------------:|-------------:|
| missing_vitals | p=0.1   | high_recall       |  0.889573 |  0.874289 |  0.895735 |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.1   | high_to_low       |  6.85     |  5.475    |  9        |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.1   | balanced_accuracy |  0.860759 |  0.848845 |  0.870292 |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.2   | high_recall       |  0.874408 |  0.852844 |  0.895972 |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.2   | high_to_low       |  8.45     |  7        | 10.525    |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.2   | balanced_accuracy |  0.833783 |  0.817149 |  0.848027 |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.3   | high_recall       |  0.861137 |  0.838626 |  0.891469 |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.3   | high_to_low       | 10.55     |  8        | 14        |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.3   | balanced_accuracy |  0.808337 |  0.790715 |  0.827538 |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.5   | high_recall       |  0.835545 |  0.807938 |  0.865047 |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.5   | high_to_low       | 16.1      | 11        | 20        |      740 |      211 |        20 |             nan |                   nan |          nan |
| missing_vitals | p=0.5   | balanced_accuracy |  0.759673 |  0.736287 |  0.776007 |      740 |      211 |        20 |             nan |                   nan |          nan |

### vital_noise

| experiment   | level                | metric            |     mean |     p2_5 |    p97_5 |   n_rows |   n_high |   repeats |   baseline_mean |   delta_from_baseline |   injury_col |
|:-------------|:---------------------|:------------------|---------:|---------:|---------:|---------:|---------:|----------:|----------------:|----------------------:|-------------:|
| vital_noise  | sd=5pct_training_sd  | high_recall       | 0.897156 | 0.888507 | 0.905213 |      740 |      211 |        20 |             nan |                   nan |          nan |
| vital_noise  | sd=5pct_training_sd  | high_to_low       | 4.6      | 4        | 5        |      740 |      211 |        20 |             nan |                   nan |          nan |
| vital_noise  | sd=5pct_training_sd  | balanced_accuracy | 0.880518 | 0.875818 | 0.886    |      740 |      211 |        20 |             nan |                   nan |          nan |
| vital_noise  | sd=10pct_training_sd | high_recall       | 0.897156 | 0.888507 | 0.905213 |      740 |      211 |        20 |             nan |                   nan |          nan |
| vital_noise  | sd=10pct_training_sd | high_to_low       | 4.8      | 4        | 5.525    |      740 |      211 |        20 |             nan |                   nan |          nan |
| vital_noise  | sd=10pct_training_sd | balanced_accuracy | 0.871578 | 0.86118  | 0.878362 |      740 |      211 |        20 |             nan |                   nan |          nan |

### free_text_input

| experiment      | level                                       | metric                 |     mean |     p2_5 |    p97_5 |   n_rows |   n_high |   repeats |   baseline_mean |   delta_from_baseline |   injury_col |
|:----------------|:--------------------------------------------|:-----------------------|---------:|---------:|---------:|---------:|---------:|----------:|----------------:|----------------------:|-------------:|
| free_text_input | patient_complains_prefix_pipe_to_and_mapped | balanced_accuracy      | 0.885105 | 0.885105 | 0.885105 |      740 |      211 |         1 |        0.885105 |                     0 |          nan |
| free_text_input | patient_complains_prefix_pipe_to_and_mapped | macro_f1               | 0.882457 | 0.882457 | 0.882457 |      740 |      211 |         1 |        0.882457 |                     0 |          nan |
| free_text_input | patient_complains_prefix_pipe_to_and_mapped | high_recall            | 0.905213 | 0.905213 | 0.905213 |      740 |      211 |         1 |        0.905213 |                     0 |          nan |
| free_text_input | patient_complains_prefix_pipe_to_and_mapped | high_to_low            | 5        | 5        | 5        |      740 |      211 |         1 |        5        |                     0 |          nan |
| free_text_input | baseline                                    | mean_complaint_nonzero | 2.42297  | 2.42297  | 2.42297  |      740 |      211 |         1 |        2.42297  |                     0 |          nan |
| free_text_input | patient_complains_prefix_pipe_to_and_mapped | mean_complaint_nonzero | 2.42297  | 2.42297  | 2.42297  |      740 |      211 |         1 |        2.42297  |                     0 |          nan |

### subgroup

| experiment   | level                       | metric            |       mean |       p2_5 |      p97_5 |   n_rows |   n_high |   repeats |   baseline_mean |   delta_from_baseline | injury_col   |
|:-------------|:----------------------------|:------------------|-----------:|-----------:|-----------:|---------:|---------:|----------:|----------------:|----------------------:|:-------------|
| subgroup     | injury_visits               | all               | nan        | nan        | nan        |        0 |        0 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | injury_like_complaint_proxy | balanced_accuracy |   0.859361 |   0.859361 |   0.859361 |      331 |       78 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | injury_like_complaint_proxy | macro_f1          |   0.8531   |   0.8531   |   0.8531   |      331 |       78 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | injury_like_complaint_proxy | high_recall       |   0.833333 |   0.833333 |   0.833333 |      331 |       78 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | injury_like_complaint_proxy | high_to_low       |   3        |   3        |   3        |      331 |       78 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_lt_18                   | balanced_accuracy |   0.889909 |   0.889909 |   0.889909 |      136 |       64 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_lt_18                   | macro_f1          |   0.889057 |   0.889057 |   0.889057 |      136 |       64 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_lt_18                   | high_recall       |   0.96875  |   0.96875  |   0.96875  |      136 |       64 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_lt_18                   | high_to_low       |   0        |   0        |   0        |      136 |       64 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_ge_65                   | balanced_accuracy |   0.842404 |   0.842404 |   0.842404 |      193 |       51 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_ge_65                   | macro_f1          |   0.840047 |   0.840047 |   0.840047 |      193 |       51 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_ge_65                   | high_recall       |   0.764706 |   0.764706 |   0.764706 |      193 |       51 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | age_ge_65                   | high_to_low       |   1        |   1        |   1        |      193 |       51 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | rest                        | balanced_accuracy |   0.897877 |   0.897877 |   0.897877 |      411 |       96 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | rest                        | macro_f1          |   0.887751 |   0.887751 |   0.887751 |      411 |       96 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | rest                        | high_recall       |   0.9375   |   0.9375   |   0.9375   |      411 |       96 |         1 |             nan |                   nan | injury_flag  |
| subgroup     | rest                        | high_to_low       |   4        |   4        |   4        |      411 |       96 |         1 |             nan |                   nan | injury_flag  |

### prevalence_resample

| experiment          | level                 | metric                          |     mean |     p2_5 |    p97_5 |   n_rows |   n_high |   repeats |   baseline_mean |   delta_from_baseline |   injury_col |
|:--------------------|:----------------------|:--------------------------------|---------:|---------:|---------:|---------:|---------:|----------:|----------------:|----------------------:|-------------:|
| prevalence_resample | high_prevalence=20pct | high_precision                  | 0.69724  | 0.655758 | 0.753998 |      740 |      148 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=20pct | high_recall                     | 0.903716 | 0.871622 | 0.939527 |      740 |      148 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=20pct | non_high_predicted_high_per_100 | 7.88514  | 5.93243  | 9.39527  |      740 |      148 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=35pct | high_precision                  | 0.833676 | 0.802958 | 0.882956 |      740 |      259 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=35pct | high_recall                     | 0.906178 | 0.872008 | 0.930695 |      740 |      259 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=35pct | non_high_predicted_high_per_100 | 6.35135  | 4.24662  | 7.77365  |      740 |      259 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=50pct | high_precision                  | 0.90257  | 0.878248 | 0.933831 |      740 |      370 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=50pct | high_recall                     | 0.907027 | 0.87     | 0.935135 |      740 |      370 |        20 |             nan |                   nan |          nan |
| prevalence_resample | high_prevalence=50pct | non_high_predicted_high_per_100 | 4.91216  | 3.23649  | 6.35811  |      740 |      370 |        20 |             nan |                   nan |          nan |
