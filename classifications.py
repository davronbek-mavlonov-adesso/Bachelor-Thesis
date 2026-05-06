import json
import os

CLASSIFICATIONS_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "classifications.json"
)


def load_classifications() -> dict:
    """Load saved classifications from disk. Returns {} if file does not exist."""
    if os.path.exists(CLASSIFICATIONS_FILE):
        with open(CLASSIFICATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_classifications(data: dict) -> None:
    """Persist classifications to disk."""
    with open(CLASSIFICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
