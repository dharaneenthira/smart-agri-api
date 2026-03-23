import json
from pathlib import Path

_TREATMENTS = None

def load_treatments():
    global _TREATMENTS
    if _TREATMENTS is not None:
        return _TREATMENTS

    path = Path(__file__).resolve().parent / "treatments.json"
    try:
        _TREATMENTS = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        _TREATMENTS = {
            "Unknown": {
                "crop": "",
                "disease": "Unknown",
                "symptoms": [],
                "immediate_actions": ["Treatment file error. Please fix treatments.json."],
                "chemical_options": [],
                "safety_note": "Prototype advisory.",
                "references": []
            }
        }
    return _TREATMENTS

def get_treatment(label: str):
    treatments = load_treatments()
    return treatments.get(label) or treatments.get("Unknown")