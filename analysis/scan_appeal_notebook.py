from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/Donation Quality Appeal.ipynb"
PATTERN = re.compile(
    r"data_origin|source|native|review|web|MDCC|overall_quality_score|quality_label|"
    r"LOW|MEDIUM|HIGH|accuracy|MAE|R2|R-squared",
    re.I,
)


def output_text(output: dict) -> str:
    parts: list[str] = []
    text = output.get("text")
    if text:
        parts.extend(text if isinstance(text, list) else [text])
    data = output.get("data", {})
    plain = data.get("text/plain")
    if plain:
        parts.extend(plain if isinstance(plain, list) else [plain])
    return "".join(parts)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    nb = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    matched = 0
    for index, cell in enumerate(nb.get("cells", [])):
        source = "".join(cell.get("source", []))
        outputs = "\n".join(output_text(output) for output in cell.get("outputs", []))
        combined = f"{source}\nOUTPUT:\n{outputs}"
        if not PATTERN.search(combined):
            continue
        matched += 1
        snippet = combined[:1600].replace("\r", "")
        print(f"--- cell {index} ---")
        print(snippet)
    print("matched_cells", matched)


if __name__ == "__main__":
    main()
