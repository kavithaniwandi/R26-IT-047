# Severity Safety-Layer Ablation

- Test n: 740
- HIGH n: 211
- Validation n: 748
- Bootstrap resamples: 5000; the same resample indices are used for every row.
- Split: `StratifiedGroupKFold(10, shuffle=True, random_state=42)`; test fold `folds[0][1]`; validation fold `folds[1][1]`.
- Retuning rule: grid-search `T_HIGH=0.20..0.80`, `T_LOW=0.30..0.80` on validation; choose highest balanced accuracy subject to HIGH recall >= 0.9.

## Validation-Tuned Thresholds

| variant                     |   t_high |   t_low |   validation_balanced_accuracy |   validation_high_recall |
|:----------------------------|---------:|--------:|-------------------------------:|-------------------------:|
| model_only_no_safety_layers |     0.24 |    0.38 |                       0.939458 |                 0.917647 |
| red_flag_only               |     0.24 |    0.38 |                       0.913828 |                 0.917647 |
| complaint_only              |     0.24 |    0.38 |                       0.936379 |                 0.929412 |
| both_layers_baseline        |     0.24 |    0.38 |                       0.910749 |                 0.929412 |

## Test Results

| mode                          | variant                     |   t_high |   t_low |   n_rows |   n_high |   balanced_accuracy |   macro_f1 |   high_recall |   high_to_low |   medium_to_high |   high_recall_ci_low |   high_recall_ci_high |   medium_to_high_ci_low |   medium_to_high_ci_high |
|:------------------------------|:----------------------------|---------:|--------:|---------:|---------:|--------------------:|-----------:|--------------:|--------------:|-----------------:|---------------------:|----------------------:|------------------------:|-------------------------:|
| fixed_saved_thresholds        | model_only_no_safety_layers |     0.39 |    0.4  |      740 |      211 |            0.914215 |   0.915067 |      0.872038 |             8 |               22 |             0.826726 |              0.915842 |                      13 |                       32 |
| fixed_saved_thresholds        | red_flag_only               |     0.39 |    0.4  |      740 |      211 |            0.884602 |   0.883074 |      0.881517 |             8 |               39 |             0.836735 |              0.923859 |                      28 |                       52 |
| fixed_saved_thresholds        | complaint_only              |     0.39 |    0.4  |      740 |      211 |            0.914718 |   0.914293 |      0.895735 |             5 |               24 |             0.853535 |              0.935484 |                      15 |                       34 |
| fixed_saved_thresholds        | both_layers_baseline        |     0.39 |    0.4  |      740 |      211 |            0.885105 |   0.882457 |      0.905213 |             5 |               41 |             0.864077 |              0.942864 |                      29 |                       54 |
| validation_retuned_thresholds | model_only_no_safety_layers |     0.24 |    0.38 |      740 |      211 |            0.910429 |   0.910382 |      0.886256 |             8 |               29 |             0.843241 |              0.927602 |                      19 |                       40 |
| validation_retuned_thresholds | red_flag_only               |     0.24 |    0.38 |      740 |      211 |            0.883583 |   0.881502 |      0.895735 |             8 |               44 |             0.854269 |              0.935185 |                      32 |                       57 |
| validation_retuned_thresholds | complaint_only              |     0.24 |    0.38 |      740 |      211 |            0.910932 |   0.909677 |      0.909953 |             5 |               31 |             0.869565 |              0.946341 |                      21 |                       43 |
| validation_retuned_thresholds | both_layers_baseline        |     0.24 |    0.38 |      740 |      211 |            0.884086 |   0.880909 |      0.919431 |             5 |               46 |             0.881279 |              0.953846 |                      34 |                       60 |
