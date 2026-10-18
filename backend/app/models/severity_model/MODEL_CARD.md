# Severity Triage Model Card

## Data And Split

- Data file: `nhamcs_2022_camp_relabeled_v2.csv`
- Label column: `camp_triage_label_final`
- Group column: `model_input_text`
- Split rule: `StratifiedGroupKFold(10, shuffle=True, random_state=42)`
- Test fold: `folds[0][1]`
- Validation fold: `folds[1][1]`
- Training indices: all rows not in the test or validation folds

## Runtime Versions

- `numpy==1.26.4`
- `scikit-learn==1.7.2`
- `xgboost==2.1.4`
- `lightgbm==4.7.0`

## Decision Policy

- Thresholds: `T_HIGH=0.3900000000000002`, `T_LOW=0.4000000000000001`
- Meta-learner: class-balanced logistic regression, `C=0.1`
- Safety layers: `red_flag`, `complaint`

## Saved Test Metrics

- Test n: `740`
- Accuracy: `0.8878378378378379`
- Balanced accuracy: `0.8851047076899321`
- Macro-F1: `0.8824573092864648`
- HIGH recall: `0.9052132701421801`
- HIGH-to-LOW count: `5`
- Confusion matrix, LOW/MEDIUM/HIGH rows by LOW/MEDIUM/HIGH columns:

```text
[[271, 5, 12],
 [5, 195, 41],
 [5, 15, 191]]
```

## Provenance Files

- `training/Severity_Triage_.ipynb`
- `training/severity_pipeline.py`
- `training/train_run.py`
- `training/requirements.txt`
