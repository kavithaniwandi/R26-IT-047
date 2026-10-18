from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold, train_test_split


ROOT = Path(__file__).resolve().parents[1]
LABEL_COL = "camp_triage_label_final"
GROUP_COL = "model_input_text"
SEED = 42


def profile_key(row: pd.Series) -> str:
    if GROUP_COL in row and pd.notna(row[GROUP_COL]):
        return str(row[GROUP_COL])
    cols = [c for c in ["symptoms", "age", "has_red_flag", "red_flag_count"] if c in row.index]
    return "|".join(str(row.get(c, "")) for c in cols)


def main() -> None:
    matches = sorted(ROOT.rglob("nhamcs_2022_camp_relabeled_v2.csv"))
    if not matches:
        print("nhamcs_2022_camp_relabeled_v2.csv: NOT FOUND")
        return

    path = matches[0]
    df = pd.read_csv(path, low_memory=False)
    df = df[df[LABEL_COL].isin(["LOW", "MEDIUM", "HIGH"])].reset_index(drop=True)
    y = df[LABEL_COL].map({"LOW": 0, "MEDIUM": 1, "HIGH": 2}).astype(int)
    groups = df.apply(profile_key, axis=1)

    folds = list(StratifiedGroupKFold(10, shuffle=True, random_state=SEED).split(df, y, groups=groups))
    train_val_idx, test_idx = folds[0]
    train_idx, val_idx = train_test_split(
        train_val_idx,
        test_size=748,
        random_state=SEED,
        stratify=y.iloc[train_val_idx],
    )

    sets = {
        "train": set(groups.iloc[train_idx]),
        "val": set(groups.iloc[val_idx]),
        "test": set(groups.iloc[test_idx]),
    }
    print("split_sizes", {"train": len(train_idx), "val": len(val_idx), "test": len(test_idx)})
    print("train_val_overlap", len(sets["train"] & sets["val"]))
    print("train_test_overlap", len(sets["train"] & sets["test"]))
    print("val_test_overlap", len(sets["val"] & sets["test"]))


if __name__ == "__main__":
    main()
