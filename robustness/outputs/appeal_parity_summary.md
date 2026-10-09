# Appeal Parity Summary

- Corpus rows after filtering: 7100
- Selected rows used by saved training protocol: 5627
- Test rows: 1136
- Split source: `C:\Users\kenur\OneDrive\Desktop\R26-IT-047\backend\ml_models\Donation Appeal\appeal_quality_test_indices.npy`

## Overall

|   n_corpus |   n_selected |   n_test | split_source                                                                                                 |   accuracy |   balanced_accuracy |   macro_f1 |      mae |       r2 |   bootstrap_repeats |
|-----------:|-------------:|---------:|:-------------------------------------------------------------------------------------------------------------|-----------:|--------------------:|-----------:|---------:|---------:|--------------------:|
|       7100 |         5627 |     1136 | C:\Users\kenur\OneDrive\Desktop\R26-IT-047\backend\ml_models\Donation Appeal\appeal_quality_test_indices.npy |   0.789613 |            0.792403 |   0.795555 | 0.340438 | 0.718073 |                5000 |

## 95% Bootstrap Intervals

| metric            |     p2_5 |    p97_5 |
|:------------------|---------:|---------:|
| accuracy          | 0.765845 | 0.81338  |
| balanced_accuracy | 0.768972 | 0.81479  |
| macro_f1          | 0.771942 | 0.817428 |
| mae               | 0.314077 | 0.367236 |
| r2                | 0.688284 | 0.745379 |

## Per Language

| language   |   n |   accuracy |   balanced_accuracy |   macro_f1 |      mae |       r2 |
|:-----------|----:|-----------:|--------------------:|-----------:|---------:|---------:|
| English    | 929 |   0.76211  |            0.76454  |   0.765956 | 0.35928  | 0.684809 |
| Sinhala    | 100 |   0.9      |            0.896194 |   0.902006 | 0.240649 | 0.834182 |
| Tamil      | 107 |   0.925234 |            0.923032 |   0.927879 | 0.270104 | 0.83721  |
