"""
Tests for backend.ai.summary module.
"""

import pytest
from backend.ai.summary import (
    SECTIONS,
    SECTION_LABELS_EN,
    SECTION_LABELS_HI,
    HPI_SUBSECTIONS,
    HPI_LABELS_EN,
    HPI_LABELS_HI,
    render_template,
    render_patient_audio,
    validate_summary_structure,
    SummaryResult,
    synthesize_sync,
    confirm,
    edit,
)


class TestTemplates:
    def test_sections_complete(self):
        expected = {
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
        }
        assert set(SECTIONS) == expected

    def test_section_labels_en(self):
        assert SECTION_LABELS_EN["chief_complaint"] == "Chief Complaint"
        assert SECTION_LABELS_EN["hpi"] == "History of Present Illness (HPI)"
        assert "AYUSH" in SECTION_LABELS_EN["ayush"]

    def test_section_labels_hi(self):
        assert SECTION_LABELS_HI["chief_complaint"] == "मुख्य शिकायत"
        assert "दशविध" in SECTION_LABELS_HI["ayush"]

    def test_hpi_subsections(self):
        assert set(HPI_SUBSECTIONS) == {"onset", "character", "radiation", "severity", "exacerbating", "relieving"}

    def test_hpi_labels_en(self):
        assert HPI_LABELS_EN["onset"] == "Onset"
        assert HPI_LABELS_EN["severity"] == "Severity"

    def test_hpi_labels_hi(self):
        assert HPI_LABELS_HI["onset"] == "शुरुआत"
        assert HPI_LABELS_HI["severity"] == "गंभीरता"

    def test_render_template_english(self):
        data = {
            "chief_complaint": "chest pain",
            "hpi": {
                "onset": "2 hours ago",
                "character": "crushing",
                "radiation": "left arm",
                "severity": "8/10",
                "exacerbating": "exertion",
                "relieving": "rest",
            },
            "past_medical_history": ["hypertension"],
            "drug_allergy_history": ["penicillin"],
            "family_history": ["father: MI at 55"],
            "personal_history": {"smoking": "10 pack-years"},
            "review_of_systems": {"cardiovascular": "positive"},
            "prior_investigations": [{"test": "ECG", "result": "normal"}],
            "ayush": {"prakriti": "pitta"},
        }
        rendered = render_template(data, lang="en")
        assert "Chief Complaint: chest pain" in rendered
        assert "History of Present Illness (HPI):" in rendered
        assert "Onset: 2 hours ago" in rendered
        assert "Severity: 8/10" in rendered
        assert "Past Medical History: hypertension" in rendered
        assert "Drug & Allergy History: penicillin" in rendered
        assert "AYUSH Assessment" in rendered

    def test_render_template_hindi(self):
        data = {
            "chief_complaint": "सीने में दर्द",
            "hpi": {"onset": "2 घंटे पहले", "severity": "8/10"},
            "past_medical_history": ["उच्च रक्तचाप"],
        }
        rendered = render_template(data, lang="hi")
        assert "मुख्य शिकायत: सीने में दर्द" in rendered
        assert "शुरुआत: 2 घंटे पहले" in rendered
        assert "पिछला चिकित्सा इतिहास: उच्च रक्तचाप" in rendered

    def test_render_template_skips_empty(self):
        data = {
            "chief_complaint": "chest pain",
            "hpi": {},
            "past_medical_history": [],
            "drug_allergy_history": ["not mentioned"],
        }
        rendered = render_template(data, lang="en")
        assert "Chief Complaint: chest pain" in rendered
        assert "Past Medical History" not in rendered
        assert "Drug & Allergy History" not in rendered

    def test_render_patient_audio_english(self):
        data = {
            "chief_complaint": "chest pain",
            "hpi": {"onset": "2 hours ago", "character": "crushing", "severity": "8/10"},
            "past_medical_history": ["hypertension"],
            "drug_allergy_history": ["penicillin"],
        }
        audio = render_patient_audio(data, lang="en")
        assert "Your main complaint is: chest pain" in audio
        assert "Illness details:" in audio
        assert "Past illnesses: hypertension" in audio
        assert "Medications and allergies: penicillin" in audio
        assert "Please consult your doctor" in audio

    def test_render_patient_audio_hindi(self):
        data = {
            "chief_complaint": "सीने में दर्द",
            "hpi": {"onset": "2 घंटे पहले"},
        }
        audio = render_patient_audio(data, lang="hi")
        assert "मुख्य शिकायत है: सीने में दर्द" in audio
        assert "कृपया डॉक्टर से मिलें" in audio

    def test_validate_summary_structure_complete(self):
        data = {s: "value" for s in SECTIONS}
        missing = validate_summary_structure(data)
        assert missing == []

    def test_validate_summary_structure_missing(self):
        data = {"chief_complaint": "chest pain"}
        missing = validate_summary_structure(data)
        assert len(missing) == 9
        assert "hpi" in missing
        assert "ayush" in missing


class TestSynthesizer:
    def test_synthesize_basic(self):
        interview = {
            "chief_complaint": "chest pain",
            "hpi": {"onset": "2 hours ago", "severity": "8/10"},
            "past_medical_history": ["hypertension"],
        }
        documents = {
            "documents": [{
                "diagnoses": ["Type 2 Diabetes"],
                "medications": [{"name": "Metformin", "dosage": "500mg", "frequency": "BD"}],
                "investigations": [{"test": "HbA1c", "value": 8.2, "unit": "%", "ref_range": "4.0-5.6", "abnormal": True}],
            }]
        }
        result = synthesize_sync(interview, documents)
        assert isinstance(result, SummaryResult)
        assert result.summary["chief_complaint"] == "chest pain"
        assert result.summary["hpi"]["onset"] == "2 hours ago"
        assert "hypertension" in result.summary["past_medical_history"]
        assert "Type 2 Diabetes" in result.summary["past_medical_history"]
        assert len(result.summary["prior_investigations"]) >= 1

    def test_synthesize_source_attribution(self):
        interview = {"chief_complaint": "chest pain"}
        documents = {"documents": [{"diagnoses": ["Diabetes"]}]}
        result = synthesize_sync(interview, documents)
        assert "chief_complaint" in result.source_attribution
        assert "interview" in result.source_attribution["chief_complaint"]
        # past_medical_history gets data from documents but attribution is based on LLM output
        # The LLM Mock returns canned response, so attribution may show "llm_inference"
        assert "past_medical_history" in result.source_attribution

    def test_synthesize_missing_sections(self):
        interview = {"chief_complaint": "chest pain"}
        documents = {}
        result = synthesize_sync(interview, documents)
        missing = result.missing_sections
        # _ensure_all_sections adds all sections with defaults, so none are missing
        assert missing == []

    def test_confirm(self):
        result = confirm("summary_123", {"hpi.severity": "9/10"})
        assert result["summary_id"] == "summary_123"
        assert result["status"] == "confirmed"

    def test_edit(self):
        result = edit("summary_123", {"chief_complaint": "severe chest pain"})
        assert result["summary_id"] == "summary_123"
        assert result["status"] == "edited"
        assert result["patches"]["chief_complaint"] == "severe chest pain"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])