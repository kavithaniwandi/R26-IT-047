# Appeal Parity Summary

- Corpus rows after filtering: 7100
- Selected rows used by saved training protocol: 5627
- Test rows: 1136
- Split source: `C:\Users\kenur\OneDrive\Desktop\R26-IT-047\backend\ml_models\Donation Appeal\appeal_quality_test_indices.npy`

## Overall

|   n_corpus |   n_selected |   n_test | split_source                                                                                                 |   accuracy |   balanced_accuracy |   macro_f1 |      mae |       r2 |   bootstrap_repeats |
|-----------:|-------------:|---------:|:-------------------------------------------------------------------------------------------------------------|-----------:|--------------------:|-----------:|---------:|---------:|--------------------:|
|       7100 |         5627 |     1136 | C:\Users\kenur\OneDrive\Desktop\R26-IT-047\backend\ml_models\Donation Appeal\appeal_quality_test_indices.npy |   0.919894 |            0.920365 |   0.920697 | 0.147266 | 0.911148 |                5000 |

## 95% Bootstrap Intervals

| metric            |     p2_5 |    p97_5 |
|:------------------|---------:|---------:|
| accuracy          | 0.904049 | 0.934859 |
| balanced_accuracy | 0.904787 | 0.935193 |
| macro_f1          | 0.905127 | 0.935512 |
| mae               | 0.130674 | 0.164315 |
| r2                | 0.895239 | 0.925111 |

## Per Language

| language   |   n |   accuracy |   balanced_accuracy |   macro_f1 |      mae |       r2 |
|:-----------|----:|-----------:|--------------------:|-----------:|---------:|---------:|
| English    | 929 |   0.916039 |            0.916515 |   0.916541 | 0.13457  | 0.913665 |
| Sinhala    | 100 |   0.94     |            0.938034 |   0.937135 | 0.178405 | 0.910814 |
| Tamil      | 107 |   0.934579 |            0.932029 |   0.936106 | 0.228388 | 0.894074 |
