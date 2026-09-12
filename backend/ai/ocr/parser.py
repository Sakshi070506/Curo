"""
Module   : Clinical Document Parser
Owner    : Document AI Engineer
Purpose  : Extracts diagnoses/drugs/lab values from OCR text.
"""

import re
from dataclasses import dataclass
from typing import Any

from backend.ai.common import MockLLMClient, get_prompt, parse_llm_json


@dataclass
class ParsedDocument:
    diagnoses: list[str]
    medications: list[dict]
    investigations: list[dict]
    procedures: list[str]
    dates: list[str]
    raw_confidence: float


DRUG_PATTERNS = [
    r"(\w+)\s+(\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|IU))",
    r"Tab\.?\s+(\w+)\s+(\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|IU))",
    r"Cap\.?\s+(\w+)\s+(\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|IU))",
    r"Syp\.?\s+(\w+)\s+(\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|IU))",
    r"Inj\.?\s+(\w+)\s+(\d+(?:\.\d+)?\s*(?:mg|g|ml|mcg|IU))",
]

FREQUENCY_PATTERNS = {
    r"\b(?:OD|once daily|daily)\b": "OD",
    r"\b(?:BD|twice daily|bid)\b": "BD",
    r"\b(?:TDS|thrice daily|tid)\b": "TDS",
    r"\b(?:QID|four times|qid)\b": "QID",
    r"\b(?:SOS|as needed|prn)\b": "SOS",
    r"\b(?:HS|at bedtime)\b": "HS",
}

DURATION_PATTERNS = [
    r"for\s+(\d+\s*(?:days?|weeks?|months?))",
    r"(\d+\s*(?:days?|weeks?|months?))\s*(?:course|treatment)",
    r"x\s*(\d+\s*(?:days?|weeks?|months?))",
]

LAB_PATTERNS = [
    r"([A-Za-z\s]+)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*([a-zA-Z/%]+)\s*(?:\(?ref[:\s]*([\d\.\-\s]+)\)?)?",
    r"([A-Z][a-z]+(?:\s+[A-Za-z]+)*)\s+(\d+(?:\.\d+)?)\s+(\w+)\s+\(([\d\.\-]+)\)",
]

DATE_PATTERNS = [
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b",
    r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2})\b",
    r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b",
]


async def parse_document(
    ocr_text: str,
    doc_type: str = "prescription",
    ocr_confidence: float = 0.0,
    client: MockLLMClient | None = None,
) -> ParsedDocument:
    """
    Parse clinical entities from OCR text using regex + LLM hybrid approach.

    Returns ParsedDocument with structured entities.
    """
    if client is None:
        client = MockLLMClient()

    spec = get_prompt("extract_document_entities")
    user_prompt = spec.user_template.format(ocr_text=ocr_text)

    messages = [
        {"role": "system", "content": spec.system},
        {"role": "user", "content": user_prompt},
    ]

    raw_response = await client.chat(messages, task="extract_document_entities")
    parsed = parse_llm_json(raw_response)

    diagnoses = parsed.get("diagnoses", []) or _extract_diagnoses_regex(ocr_text)
    medications = parsed.get("medications", []) or _extract_medications_regex(ocr_text)
    investigations = parsed.get("investigations", []) or _extract_investigations_regex(ocr_text)
    procedures = parsed.get("procedures", []) or _extract_procedures_regex(ocr_text)
    dates = parsed.get("dates", []) or _extract_dates_regex(ocr_text)

    medications = _enrich_medications(medications, ocr_text)
    investigations = _enrich_investigations(investigations, ocr_text)

    return ParsedDocument(
        diagnoses=diagnoses,
        medications=medications,
        investigations=investigations,
        procedures=procedures,
        dates=dates,
        raw_confidence=ocr_confidence,
    )


def _extract_diagnoses_regex(text: str) -> list[str]:
    diagnoses = []
    diag_keywords = [
        "diabetes", "hypertension", "hypothyroidism", "hyperthyroidism",
        "asthma", "copd", "pneumonia", "tuberculosis", "anemia",
        "myocardial infarction", "heart failure", "stroke", "ckd",
        "liver disease", "gerd", "peptic ulcer", "ibs", "ibd",
        "arthritis", "osteoporosis", "gout", "migraine", "epilepsy",
    ]
    text_lower = text.lower()
    for kw in diag_keywords:
        if kw in text_lower:
            diagnoses.append(kw.title())
    return list(set(diagnoses))


def _extract_medications_regex(text: str) -> list[dict]:
    medications = []
    for pattern in DRUG_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            drug_name = match.group(1).strip().title()
            dosage = match.group(2).strip() if len(match.groups()) >= 2 else ""

            freq = "OD"
            for freq_pattern, freq_code in FREQUENCY_PATTERNS.items():
                if re.search(freq_pattern, text[match.end():match.end()+50], re.IGNORECASE):
                    freq = freq_code
                    break

            duration = "ongoing"
            for dur_pattern in DURATION_PATTERNS:
                dur_match = re.search(dur_pattern, text[match.end():match.end()+50], re.IGNORECASE)
                if dur_match:
                    duration = dur_match.group(1)
                    break

            medications.append({
                "name": drug_name,
                "dosage": dosage,
                "frequency": freq,
                "duration": duration,
            })
    return medications


def _extract_investigations_regex(text: str) -> list[dict]:
    investigations = []
    for pattern in LAB_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            test_name = match.group(1).strip()
            value = float(match.group(2))
            unit = match.group(3).strip()
            ref_range = match.group(4).strip() if len(match.groups()) >= 4 and match.group(4) else ""

            abnormal = False
            if ref_range:
                try:
                    ref_parts = ref_range.replace(" ", "").split("-")
                    if len(ref_parts) == 2:
                        low, high = float(ref_parts[0]), float(ref_parts[1])
                        abnormal = value < low or value > high
                except (ValueError, IndexError):
                    pass

            investigations.append({
                "test": test_name,
                "value": value,
                "unit": unit,
                "ref_range": ref_range if ref_range else "not mentioned",
                "abnormal": abnormal,
            })
    return investigations


def _extract_procedures_regex(text: str) -> list[str]:
    procedures = []
    proc_keywords = [
        "surgery", "operation", "appendectomy", "cholecystectomy", "hernia repair",
        "cataract", "angioplasty", "bypass", "dialysis", "biopsy", "endoscopy",
        "colonoscopy", "ecg", "echo", "x-ray", "ct scan", "mri", "ultrasound",
    ]
    text_lower = text.lower()
    for kw in proc_keywords:
        if kw in text_lower:
            procedures.append(kw.title())
    return list(set(procedures))


def _extract_dates_regex(text: str) -> list[str]:
    dates = []
    for pattern in DATE_PATTERNS:
        matches = re.findall(pattern, text)
        dates.extend(matches)
    return list(set(dates))


def _enrich_medications(medications: list[dict], ocr_text: str) -> list[dict]:
    """Enrich medication data with frequency/duration from regex if missing."""
    for med in medications:
        if not med.get("frequency") or med["frequency"] == "OD":
            for freq_pattern, freq_code in FREQUENCY_PATTERNS.items():
                if re.search(freq_pattern, ocr_text, re.IGNORECASE):
                    med["frequency"] = freq_code
                    break
        if not med.get("duration") or med["duration"] == "ongoing":
            for dur_pattern in DURATION_PATTERNS:
                match = re.search(dur_pattern, ocr_text, re.IGNORECASE)
                if match:
                    med["duration"] = match.group(1)
                    break
    return medications


def _enrich_investigations(investigations: list[dict], ocr_text: str) -> list[dict]:
    """Enrich investigation data with reference ranges if missing."""
    for inv in investigations:
        if not inv.get("ref_range") or inv["ref_range"] == "not mentioned":
            test_lower = inv.get("test", "").lower()
            if "hba1c" in test_lower:
                inv["ref_range"] = "4.0-5.6"
                inv["abnormal"] = inv["value"] > 5.6
            elif "glucose" in test_lower or "sugar" in test_lower:
                inv["ref_range"] = "70-100"
                inv["abnormal"] = inv["value"] > 100 or inv["value"] < 70
            elif "cholesterol" in test_lower:
                inv["ref_range"] = "<200"
                inv["abnormal"] = inv["value"] > 200
            elif "creatinine" in test_lower:
                inv["ref_range"] = "0.6-1.3"
                inv["abnormal"] = inv["value"] > 1.3 or inv["value"] < 0.6
    return investigations


def parse_document_sync(
    ocr_text: str,
    doc_type: str = "prescription",
    ocr_confidence: float = 0.0,
) -> ParsedDocument:
    """Synchronous wrapper for parse_document."""
    import asyncio
    return asyncio.run(parse_document(ocr_text, doc_type, ocr_confidence))


__all__ = [
    "ParsedDocument",
    "parse_document",
    "parse_document_sync",
]