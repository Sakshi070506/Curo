"""
Module   : Summary Templates
Owner    : Summary/LLM Engineer
Purpose  : Standard clinical format templates (EN/HI).
"""

from typing import Any


SECTIONS = [
    "chief_complaint",
    "hpi",
    "past_medical_history",
    "past_surgical_history",
    "drug_allergy_history",
    "family_history",
    "personal_history",
    "review_of_systems",
    "prior_investigations",
    "ayush",
]

SECTION_LABELS_EN = {
    "chief_complaint": "Chief Complaint",
    "hpi": "History of Present Illness (HPI)",
    "past_medical_history": "Past Medical History",
    "past_surgical_history": "Past Surgical History",
    "drug_allergy_history": "Drug & Allergy History",
    "family_history": "Family History",
    "personal_history": "Personal History",
    "review_of_systems": "Review of Systems (ROS)",
    "prior_investigations": "Prior Investigations",
    "ayush": "AYUSH Assessment (Dashavidha Pariksha)",
}

SECTION_LABELS_HI = {
    "chief_complaint": "मुख्य शिकायत",
    "hpi": "वर्तमान बीमारी का इतिहास (HPI)",
    "past_medical_history": "पिछला चिकित्सा इतिहास",
    "past_surgical_history": "पिछला शल्य इतिहास",
    "drug_allergy_history": "दवा और एलर्जी इतिहास",
    "family_history": "पारिवारिक इतिहास",
    "personal_history": "व्यक्तिगत इतिहास",
    "review_of_systems": "प्रणालियों की समीक्षा (ROS)",
    "prior_investigations": "पहले की जांच",
    "ayush": "आयुष मूल्यांकन (दशविध परीक्षा)",
}

HPI_SUBSECTIONS = [
    "onset",
    "character",
    "radiation",
    "severity",
    "exacerbating",
    "relieving",
]

HPI_LABELS_EN = {
    "onset": "Onset",
    "character": "Character",
    "radiation": "Radiation",
    "severity": "Severity",
    "exacerbating": "Exacerbating Factors",
    "relieving": "Relieving Factors",
}

HPI_LABELS_HI = {
    "onset": "शुरुआत",
    "character": "प्रकृति",
    "radiation": "विकिरण",
    "severity": "गंभीरता",
    "exacerbating": "बढ़ाने वाले कारक",
    "relieving": "घटाने वाले कारक",
}


def format_value(value: Any, lang: str = "en") -> str:
    """Format a value for display."""
    if value is None:
        return "Not mentioned" if lang == "en" else "उल्लेख नहीं"
    if isinstance(value, list):
        if not value:
            return "None" if lang == "en" else "कोई नहीं"
        return ", ".join(str(v) for v in value)
    if isinstance(value, dict):
        if not value:
            return "None" if lang == "en" else "कोई नहीं"
        items = []
        for k, v in value.items():
            label = k.replace("_", " ").title()
            items.append(f"{label}: {v}")
        return "; ".join(items)
    return str(value)


def render_template(data: dict[str, Any], lang: str = "en") -> str:
    """
    Render structured summary data into physician-readable text format.

    Args:
        data: Summary dictionary from synthesizer
        lang: Language code ('en' or 'hi')

    Returns:
        Formatted text string
    """
    labels = SECTION_LABELS_HI if lang == "hi" else SECTION_LABELS_EN
    hpi_labels = HPI_LABELS_HI if lang == "hi" else HPI_LABELS_EN

    lines = []
    for section in SECTIONS:
        if section not in data:
            continue

        value = data[section]
        if value in (None, "", [], {}):
            continue

        label = labels.get(section, section.replace("_", " ").title())

        if section == "hpi" and isinstance(value, dict):
            lines.append(f"\n{label}:")
            for sub_key in HPI_SUBSECTIONS:
                if sub_key in value and value[sub_key] not in (None, "", "not mentioned"):
                    sub_label = hpi_labels.get(sub_key, sub_key.title())
                    lines.append(f"  {sub_label}: {format_value(value[sub_key], lang)}")
        elif section == "ayush" and isinstance(value, dict):
            lines.append(f"\n{label}:")
            for k, v in value.items():
                if v not in (None, "", "not mentioned"):
                    sub_label = k.replace("_", " ").title()
                    lines.append(f"  {sub_label}: {format_value(v, lang)}")
        else:
            formatted = format_value(value, lang)
            if formatted and formatted not in ("Not mentioned", "उल्लेख नहीं", "None", "कोई नहीं", "not mentioned"):
                lines.append(f"\n{label}: {formatted}")

    return "\n".join(lines).strip()


def render_patient_audio(data: dict[str, Any], lang: str = "hi") -> str:
    """
    Render concise, patient-friendly summary for TTS playback.

    Args:
        data: Summary dictionary
        lang: Language code ('hi' or 'en')

    Returns:
        Concise text suitable for audio playback
    """
    parts = []

    if data.get("chief_complaint") and data["chief_complaint"] != "not mentioned":
        complaint = data["chief_complaint"]
        if lang == "hi":
            parts.append(f"आपकी मुख्य शिकायत है: {complaint}")
        else:
            parts.append(f"Your main complaint is: {complaint}")

    hpi = data.get("hpi", {})
    if hpi:
        hpi_parts = []
        for key in ["onset", "character", "severity"]:
            if hpi.get(key) and hpi[key] != "not mentioned":
                hpi_parts.append(f"{key}: {hpi[key]}")
        if hpi_parts:
            if lang == "hi":
                parts.append(f"बीमारी का विवरण: {', '.join(hpi_parts)}")
            else:
                parts.append(f"Illness details: {', '.join(hpi_parts)}")

    pmh = data.get("past_medical_history", [])
    if pmh and pmh != ["not mentioned"]:
        if lang == "hi":
            parts.append(f"पिछली बीमारियाँ: {', '.join(pmh)}")
        else:
            parts.append(f"Past illnesses: {', '.join(pmh)}")

    drugs = data.get("drug_allergy_history", [])
    if drugs and drugs != ["not mentioned"]:
        if lang == "hi":
            parts.append(f"दवाएँ और एलर्जी: {', '.join(drugs)}")
        else:
            parts.append(f"Medications and allergies: {', '.join(drugs)}")

    if lang == "hi":
        parts.append("कृपया डॉक्टर से मिलें।")
    else:
        parts.append("Please consult your doctor.")

    return " ".join(parts)


def validate_summary_structure(data: dict[str, Any]) -> list[str]:
    """
    Validate that summary has all required sections.

    Returns:
        List of missing section names
    """
    missing = []
    for section in SECTIONS:
        if section not in data:
            missing.append(section)
    return missing


__all__ = [
    "SECTIONS",
    "SECTION_LABELS_EN",
    "SECTION_LABELS_HI",
    "HPI_SUBSECTIONS",
    "HPI_LABELS_EN",
    "HPI_LABELS_HI",
    "render_template",
    "render_patient_audio",
    "validate_summary_structure",
]