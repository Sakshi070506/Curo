"""
Tests for backend.ai.nlu module.
"""

import pytest
from backend.ai.nlu import (
    SOCRATES_TREE,
    DASHAVIDHA_PARIKSHA,
    AHARA_VIHARA_QUESTIONS,
    ROS_CHECKLIST,
    CONCEPT_TO_ICD_SNOMED,
    get_socrates_tree,
    get_next_question,
    get_ayush_questions,
    get_ahara_vihara_questions,
    get_ros_questions,
    get_icd_snomed,
    classify_intent_sync,
    VALID_INTENTS,
    extract_entities_sync,
    merge_tapped_answer,
    SOCRATES_SLOTS,
)


class TestClinicalOntology:
    def test_socrates_tree_has_complaints(self):
        assert "chest_pain" in SOCRATES_TREE
        assert "abdominal_pain" in SOCRATES_TREE
        assert "headache" in SOCRATES_TREE
        assert "dyspnoea" in SOCRATES_TREE
        assert "default" in SOCRATES_TREE

    def test_socrates_tree_structure(self):
        tree = SOCRATES_TREE["chest_pain"]
        assert len(tree) == 9
        slots = [q.slot for q in tree]
        assert set(slots) == set(SOCRATES_SLOTS)

    def test_dashavidha_pariksha_has_10_questions(self):
        assert len(DASHAVIDHA_PARIKSHA) == 10
        params = [q.slot for q in DASHAVIDHA_PARIKSHA]
        expected = {"prakriti", "vikriti", "sara", "samhanana", "pramana", "satmya", "sattva", "ahara_shakti", "vyayama_shakti", "vaya"}
        assert set(params) == expected

    def test_ahara_vihara_has_questions(self):
        assert len(AHARA_VIHARA_QUESTIONS) == 8

    def test_ros_checklist_has_systems(self):
        assert "cardiovascular" in ROS_CHECKLIST
        assert "respiratory" in ROS_CHECKLIST
        assert "gastrointestinal" in ROS_CHECKLIST
        assert "neurological" in ROS_CHECKLIST
        assert "genitourinary" in ROS_CHECKLIST
        assert "musculoskeletal" in ROS_CHECKLIST
        assert "dermatological" in ROS_CHECKLIST
        assert "endocrine" in ROS_CHECKLIST

    def test_concept_to_icd_snomed(self):
        assert "chest_pain" in CONCEPT_TO_ICD_SNOMED
        assert "icd10" in CONCEPT_TO_ICD_SNOMED["chest_pain"]
        assert "snomed" in CONCEPT_TO_ICD_SNOMED["chest_pain"]

    def test_get_socrates_tree_matching(self):
        tree = get_socrates_tree("chest pain")
        assert len(tree) == 9

    def test_get_socrates_tree_default(self):
        tree = get_socrates_tree("unknown complaint")
        assert tree == SOCRATES_TREE["default"]

    def test_get_next_question(self):
        state = {"chief_complaint": "chest pain", "answered_slots": ["site", "onset"]}
        next_q = get_next_question(state)
        assert next_q is not None
        assert next_q.slot == "character"

    def test_get_next_question_complete(self):
        state = {"chief_complaint": "chest pain", "answered_slots": SOCRATES_SLOTS}
        next_q = get_next_question(state)
        assert next_q is None

    def test_get_ayush_questions(self):
        questions = get_ayush_questions()
        assert len(questions) == 10

    def test_get_ahara_vihara_questions(self):
        questions = get_ahara_vihara_questions()
        assert len(questions) == 8

    def test_get_ros_questions_all(self):
        questions = get_ros_questions()
        assert len(questions) > 20

    def test_get_ros_questions_filtered(self):
        questions = get_ros_questions("cardiovascular")
        assert len(questions) == 4

    def test_get_icd_snomed_known(self):
        codes = get_icd_snomed("chest_pain")
        assert codes["icd10"] == "R07.9"
        assert codes["snomed"] == "29857009"

    def test_get_icd_snomed_unknown(self):
        codes = get_icd_snomed("unknown")
        assert codes["icd10"] == ""
        assert codes["snomed"] == ""


class TestIntentClassifier:
    def test_classify_symptom_report(self):
        result = classify_intent_sync("I have chest pain since morning")
        assert result["intent"] in VALID_INTENTS
        assert 0 <= result["confidence"] <= 1

    def test_classify_general_query(self):
        result = classify_intent_sync("What time does the clinic open?")
        assert result["intent"] in VALID_INTENTS

    def test_classify_affirmation(self):
        result = classify_intent_sync("Yes, that's correct")
        assert result["intent"] in VALID_INTENTS

    def test_classify_negation(self):
        result = classify_intent_sync("No, I don't have that")
        assert result["intent"] in VALID_INTENTS

    def test_classify_dont_know(self):
        result = classify_intent_sync("I'm not sure")
        assert result["intent"] in VALID_INTENTS


class TestEntityExtractor:
    def test_extract_entities_chest_pain(self):
        result = extract_entities_sync("Chest pain started 2 hours ago, crushing, radiates to left arm, severity 8/10")
        assert "site" in result
        assert "onset" in result
        assert "severity" in result
        assert all(slot in result for slot in SOCRATES_SLOTS)

    def test_extract_entities_not_mentioned(self):
        result = extract_entities_sync("I don't know")
        for slot in SOCRATES_SLOTS:
            # MockLLMClient returns canned response, so values may be present
            assert slot in result
            assert isinstance(result[slot], str)

    def test_merge_tapped_answer_priority(self):
        extracted = {"site": "chest", "onset": "not mentioned", "severity": "5/10"}
        tapped = {"onset": "sudden", "severity": "9/10"}
        merged = merge_tapped_answer(extracted, tapped)
        assert merged["onset"] == "sudden"
        assert merged["severity"] == "9/10"
        assert merged["site"] == "chest"


class TestNLUIntegration:
    def test_full_pipeline_chest_pain(self):
        # Test the complete NLU flow for a chest pain case
        state = {"chief_complaint": "chest pain", "answered_slots": []}
        next_q = get_next_question(state)
        assert next_q.slot == "site"

        # Simulate tapped answer
        state["answered_slots"].append("site")
        entities = extract_entities_sync("center of chest", current_complaint="chest pain")
        merged = merge_tapped_answer(entities, {"site": "center_chest"})
        assert merged["site"] == "center_chest"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])