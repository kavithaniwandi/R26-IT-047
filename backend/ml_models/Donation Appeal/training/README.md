# Donation Appeal quality v3 reproduction

Training data is supplied separately by the dataset owner; it is not bundled here.

Expected dataset:
Donation_Appeal_MASTER_FINAL_v8_7100.csv

Expected SHA-256:
5074b1ebedc3f96118a982408b761b03af31b9e0cf4b398f6b190c742b7cedf4

Protocol: seed 42; five-fold StratifiedGroupKFold; near-duplicate
grouping threshold 0.8. The first fold is held out. Boundary tolerance
is selected using development data with margin 0.005. The shipped
model is fitted on development rows only. See the exported manifest
for the exact protocol and environment.

Use the environment versions recorded in v3_retrained/manifest.json.
Verify the dataset hash before running. Write outputs to a new,
non-existing directory:

python training/train_quality_v3.py <dataset-path> <new-output-directory>

Run from backend/ml_models/Donation Appeal/.
Never train into the deployed v3_retrained directory.
Set PYTHONDONTWRITEBYTECODE=1 when running Python.

Compare the new manifest, metrics and artifact hashes with the shipped
export. Identical results require the matching dataset, source and
environment; the manifest does not record a training-source hash.

The score decides the label, and the classifier overrides it only when the
score is within 0.5 of a band boundary (strictly less than 0.5 from 2 or 3).
The API's displayed score is clamped into the final label's band.
raw_quality_score retains the original post-isotonic score. Exported
regression metrics describe the original scores, not display clamping.

The reproduction notebook lives at
notebooks/Donation_Appeal_Quality_v3_Colab.ipynb, placed there by the owner.
No notebook copy is stored in training/. The old
notebooks/Donation Quality Appeal.ipynb is left for its owner to replace.

The pre-v3 model sets were removed on purpose.

Regenerate APPEAL_MODEL_CARD.md and appeal_eval.json without training:
python training/generate_metadata.py

The metadata generator reads only v3_retrained/manifest.json and
v3_retrained/metrics.json. It rejects disagreement in test accuracy
or selected boundary tolerance.
