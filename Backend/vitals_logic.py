"""
Threshold rules for classifying vitals. Mirrors the logic in the frontend
so the doctor dashboard and the backend agree on what counts as abnormal.

These are simplified thresholds for demo purposes, not real clinical
guidance.
"""

LABELS = {
    "hr": "heart rate",
    "bp": "blood pressure",
    "spo2": "SpO2",
    "temp": "temperature",
}


def classify(vitals: dict) -> tuple[str, list[str]]:
    """Returns (status_level, flags) where status_level is
    'normal' | 'warning' | 'critical'."""
    flags = []
    if vitals["hr"] > 100 or vitals["hr"] < 55:
        flags.append("hr")
    if vitals["bp_sys"] > 140 or vitals["bp_sys"] < 90 or vitals["bp_dia"] > 90:
        flags.append("bp")
    if vitals["spo2"] < 94:
        flags.append("spo2")
    if vitals["temp"] > 38.0 or vitals["temp"] < 36.0:
        flags.append("temp")

    if not flags:
        return "normal", flags
    if len(flags) == 1:
        return "warning", flags
    return "critical", flags


def alert_message(level: str, flags: list[str]) -> str:
    flag_labels = ", ".join(LABELS[f] for f in flags)
    prefix = "Critical" if level == "critical" else "Abnormal"
    return f"{prefix} reading: {flag_labels}"
