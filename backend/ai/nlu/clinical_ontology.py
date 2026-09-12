"""
Module   : Clinical Ontology
Owner    : ML Engineer / Clinical Advisor
Purpose  : Question trees: SOCRATES + Dashavidha Pariksha + ROS.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Question:
    question_id: str
    question_text: str
    options: list[str]
    slot: str
    branch: str = "SOCRATES"
    follow_up_map: dict[str, str] | None = None


SOCRATES_TREE: dict[str, list[Question]] = {
    "chest_pain": [
        Question("soc_site", "Where exactly is the pain?", ["center_chest", "left_chest", "right_chest", "radiating"], "site"),
        Question("soc_onset", "When did the pain start?", ["sudden", "gradual", "intermittent", "not_sure"], "onset"),
        Question("soc_character", "How would you describe the pain?", ["crushing", "sharp", "burning", "dull", "pressure", "other"], "character"),
        Question("soc_radiation", "Does the pain travel anywhere?", ["left_arm", "right_arm", "jaw", "back", "neck", "nowhere"], "radiation"),
        Question("soc_associated", "Any other symptoms with the pain?", ["dyspnoea", "diaphoresis", "nausea", "palpitations", "dizziness", "none"], "associated"),
        Question("soc_timing", "Is the pain constant or does it come and go?", ["constant", "intermittent", "worse_morning", "worse_night", "with_exertion"], "timing"),
        Question("soc_exacerbating", "What makes the pain worse?", ["exertion", "breathing", "movement", "eating", "stress", "nothing_specific"], "exacerbating"),
        Question("soc_relieving", "What makes the pain better?", ["rest", "nitroglycerin", "antacid", "position_change", "nothing"], "relieving"),
        Question("soc_severity", "On a scale of 1-10, how severe is the pain?", ["1-3", "4-6", "7-8", "9-10"], "severity"),
    ],
    "abdominal_pain": [
        Question("soc_site", "Where is the abdominal pain?", ["upper_abdomen", "lower_abdomen", "right_upper", "left_upper", "right_lower", "left_lower", "diffuse"], "site"),
        Question("soc_onset", "When did the pain start?", ["sudden", "gradual", "intermittent", "not_sure"], "onset"),
        Question("soc_character", "How would you describe the pain?", ["cramping", "sharp", "dull", "burning", "bloating", "other"], "character"),
        Question("soc_radiation", "Does the pain travel anywhere?", ["back", "shoulder", "groin", "chest", "nowhere"], "radiation"),
        Question("soc_associated", "Any other symptoms?", ["nausea", "vomiting", "fever", "diarrhea", "constipation", "blood_stool", "none"], "associated"),
        Question("soc_timing", "Is the pain constant or intermittent?", ["constant", "intermittent", "after_meals", "empty_stomach", "night"], "timing"),
        Question("soc_exacerbating", "What makes it worse?", ["eating", "movement", "pressure", "stress", "nothing_specific"], "exacerbating"),
        Question("soc_relieving", "What makes it better?", ["antacid", "food", "rest", "bowel_movement", "nothing"], "relieving"),
        Question("soc_severity", "On a scale of 1-10, how severe?", ["1-3", "4-6", "7-8", "9-10"], "severity"),
    ],
    "headache": [
        Question("soc_site", "Where is the headache?", ["forehead", "temples", "back_of_head", "one_sided", "whole_head", "behind_eyes"], "site"),
        Question("soc_onset", "When did it start?", ["sudden", "gradual", "upon_waking", "after_injury", "not_sure"], "onset"),
        Question("soc_character", "How would you describe it?", ["throbbing", "pressure", "sharp", "dull", "band_like", "other"], "character"),
        Question("soc_radiation", "Does it travel anywhere?", ["neck", "eyes", "jaw", "nowhere"], "radiation"),
        Question("soc_associated", "Any other symptoms?", ["nausea", "vomiting", "visual_changes", "photophobia", "phonophobia", "fever", "weakness", "none"], "associated"),
        Question("soc_timing", "When is it worse?", ["morning", "evening", "constant", "intermittent", "with_activity"], "timing"),
        Question("soc_exacerbating", "What makes it worse?", ["light", "sound", "movement", "stress", "nothing_specific"], "exacerbating"),
        Question("soc_relieving", "What makes it better?", ["dark_room", "sleep", "painkiller", "massage", "nothing"], "relieving"),
        Question("soc_severity", "On a scale of 1-10, how severe?", ["1-3", "4-6", "7-8", "9-10"], "severity"),
    ],
    "dyspnoea": [
        Question("soc_site", "Where do you feel the breathing difficulty?", ["chest", "throat", "general", "not_sure"], "site"),
        Question("soc_onset", "When did it start?", ["sudden", "gradual", "with_exertion", "at_rest", "at_night"], "onset"),
        Question("soc_character", "How would you describe it?", ["can't_catch_breath", "shallow", "wheezing", "suffocating", "other"], "character"),
        Question("soc_radiation", "Does it travel anywhere?", ["no", "chest_pain", "arm_pain"], "radiation"),
        Question("soc_associated", "Any other symptoms?", ["cough", "fever", "chest_pain", "swelling_legs", "palpitations", "none"], "associated"),
        Question("soc_timing", "When is it worse?", ["exertion", "lying_flat", "night", "constant", "intermittent"], "timing"),
        Question("soc_exacerbating", "What makes it worse?", ["exertion", "lying_down", "cold_air", "dust", "nothing_specific"], "exacerbating"),
        Question("soc_relieving", "What makes it better?", ["sitting_up", "inhaler", "rest", "fresh_air", "nothing"], "relieving"),
        Question("soc_severity", "On a scale of 1-10, how severe?", ["1-3", "4-6", "7-8", "9-10"], "severity"),
    ],
    "default": [
        Question("soc_site", "Where is the symptom?", ["head", "chest", "abdomen", "back", "limbs", "other"], "site"),
        Question("soc_onset", "When did it start?", ["sudden", "gradual", "intermittent", "not_sure"], "onset"),
        Question("soc_character", "How would you describe it?", ["sharp", "dull", "burning", "throbbing", "pressure", "other"], "character"),
        Question("soc_radiation", "Does it travel anywhere?", ["yes", "no"], "radiation"),
        Question("soc_associated", "Any other symptoms?", ["fever", "nausea", "vomiting", "dizziness", "weakness", "none"], "associated"),
        Question("soc_timing", "Is it constant or intermittent?", ["constant", "intermittent", "morning", "evening", "with_activity"], "timing"),
        Question("soc_exacerbating", "What makes it worse?", ["movement", "eating", "stress", "nothing_specific"], "exacerbating"),
        Question("soc_relieving", "What makes it better?", ["rest", "medication", "position_change", "nothing"], "relieving"),
        Question("soc_severity", "On a scale of 1-10, how severe?", ["1-3", "4-6", "7-8", "9-10"], "severity"),
    ],
}


DASHAVIDHA_PARIKSHA: list[Question] = [
    Question("prakriti", "What is your natural body constitution?", ["vata", "pitta", "kapha", "vata_pitta", "pitta_kapha", "vata_kapha", "tridosha", "not_sure"], "prakriti", branch="AYUSH"),
    Question("vikriti", "What is your current imbalance?", ["vata_vriddhi", "pitta_vriddhi", "kapha_vriddhi", "vata_kshaya", "pitta_kshaya", "kapha_kshaya", "not_sure"], "vikriti", branch="AYUSH"),
    Question("sara", "Which tissue quality is predominant?", ["rasa_sara", "rakta_sara", "mamsa_sara", "meda_sara", "asthi_sara", "majja_sara", "shukra_sara", "not_sure"], "sara", branch="AYUSH"),
    Question("samhanana", "How would you describe your body build?", ["compact", "moderate", "loose", "not_sure"], "samhanana", branch="AYUSH"),
    Question("pramana", "How are your body measurements?", ["proportionate", "disproportionate", "not_sure"], "pramana", branch="AYUSH"),
    Question("satmya", "What suits your body (diet/lifestyle)?", ["all_foods", "specific_foods", "seasonal_changes", "not_sure"], "satmya", branch="AYUSH"),
    Question("sattva", "How is your mental strength?", ["strong", "moderate", "weak", "not_sure"], "sattva", branch="AYUSH"),
    Question("ahara_shakti", "How is your digestive capacity?", ["strong", "moderate", "weak", "irregular", "not_sure"], "ahara_shakti", branch="AYUSH"),
    Question("vyayama_shakti", "What is your exercise tolerance?", ["high", "moderate", "low", "not_sure"], "vyayama_shakti", branch="AYUSH"),
    Question("vaya", "What is your age category?", ["balya", "yauvana", "vardhakya", "not_sure"], "vaya", branch="AYUSH"),
]

AHARA_VIHARA_QUESTIONS: list[Question] = [
    Question("diet_type", "What is your usual diet?", ["vegetarian", "non_vegetarian", "mixed", "vegan"], "diet_type", branch="AYUSH"),
    Question("meal_timing", "How regular are your meals?", ["regular", "irregular", "skip_meals", "frequent_snacking"], "meal_timing", branch="AYUSH"),
    Question("water_intake", "How much water do you drink daily?", ["<1L", "1-2L", "2-3L", ">3L"], "water_intake", branch="AYUSH"),
    Question("sleep_pattern", "How is your sleep?", ["sound_7_8h", "disturbed_5_6h", "<5h", "daytime_sleep", "irregular"], "sleep_pattern", branch="AYUSH"),
    Question("exercise", "What is your physical activity level?", ["daily", "3_4_weekly", "occasionally", "sedentary"], "exercise", branch="AYUSH"),
    Question("addictions", "Any habits?", ["none", "tobacco", "alcohol", "both", "other"], "addictions", branch="AYUSH"),
    Question("bowel_habits", "How are your bowel movements?", ["regular_daily", "irregular", "constipation", "diarrhea", "alternating"], "bowel_habits", branch="AYUSH"),
    Question("urination", "How is urination?", ["normal", "frequent", "scanty", "painful", "nocturia"], "urination", branch="AYUSH"),
]


ROS_CHECKLIST: dict[str, list[Question]] = {
    "cardiovascular": [
        Question("ros_chest_pain", "Chest pain or discomfort?", ["yes", "no"], "chest_pain", branch="ROS"),
        Question("ros_palpitations", "Palpitations or irregular heartbeat?", ["yes", "no"], "palpitations", branch="ROS"),
        Question("ros_edema", "Swelling in legs/ankles?", ["yes", "no"], "edema", branch="ROS"),
        Question("ros_orthopnea", "Difficulty breathing lying flat?", ["yes", "no"], "orthopnea", branch="ROS"),
    ],
    "respiratory": [
        Question("ros_cough", "Persistent cough?", ["yes", "no"], "cough", branch="ROS"),
        Question("ros_wheeze", "Wheezing or whistling sound?", ["yes", "no"], "wheeze", branch="ROS"),
        Question("ros_hemoptysis", "Coughing up blood?", ["yes", "no"], "hemoptysis", branch="ROS"),
        Question("ros_dyspnea", "Shortness of breath?", ["yes", "no"], "dyspnea", branch="ROS"),
    ],
    "gastrointestinal": [
        Question("ros_nausea", "Nausea or vomiting?", ["yes", "no"], "nausea", branch="ROS"),
        Question("ros_abdominal_pain", "Abdominal pain?", ["yes", "no"], "abdominal_pain", branch="ROS"),
        Question("ros_blood_stool", "Blood in stool?", ["yes", "no"], "blood_stool", branch="ROS"),
        Question("ros_heartburn", "Heartburn or acid reflux?", ["yes", "no"], "heartburn", branch="ROS"),
        Question("ros_weight_loss", "Unintentional weight loss?", ["yes", "no"], "weight_loss", branch="ROS"),
    ],
    "neurological": [
        Question("ros_headache", "Frequent headaches?", ["yes", "no"], "headache", branch="ROS"),
        Question("ros_dizziness", "Dizziness or vertigo?", ["yes", "no"], "dizziness", branch="ROS"),
        Question("ros_weakness", "Weakness or numbness?", ["yes", "no"], "weakness", branch="ROS"),
        Question("ros_syncope", "Fainting or blackouts?", ["yes", "no"], "syncope", branch="ROS"),
        Question("ros_seizure", "Seizures?", ["yes", "no"], "seizure", branch="ROS"),
    ],
    "genitourinary": [
        Question("ros_dysuria", "Painful urination?", ["yes", "no"], "dysuria", branch="ROS"),
        Question("ros_frequency", "Frequent urination?", ["yes", "no"], "frequency", branch="ROS"),
        Question("ros_hematuria", "Blood in urine?", ["yes", "no"], "hematuria", branch="ROS"),
    ],
    "musculoskeletal": [
        Question("ros_joint_pain", "Joint pain or swelling?", ["yes", "no"], "joint_pain", branch="ROS"),
        Question("ros_muscle_pain", "Muscle pain?", ["yes", "no"], "muscle_pain", branch="ROS"),
        Question("ros_back_pain", "Back pain?", ["yes", "no"], "back_pain", branch="ROS"),
    ],
    "dermatological": [
        Question("ros_rash", "Skin rash?", ["yes", "no"], "rash", branch="ROS"),
        Question("ros_itching", "Itching?", ["yes", "no"], "itching", branch="ROS"),
    ],
    "endocrine": [
        Question("ros_heat_cold_intolerance", "Heat or cold intolerance?", ["yes", "no"], "heat_cold_intolerance", branch="ROS"),
        Question("ros_polyuria_polydipsia", "Excessive thirst/urination?", ["yes", "no"], "polyuria_polydipsia", branch="ROS"),
    ],
}


CONCEPT_TO_ICD_SNOMED: dict[str, dict[str, str]] = {
    "chest_pain": {"icd10": "R07.9", "snomed": "29857009"},
    "abdominal_pain": {"icd10": "R10.9", "snomed": "21522001"},
    "headache": {"icd10": "R51", "snomed": "25064002"},
    "dyspnoea": {"icd10": "R06.02", "snomed": "267036007"},
    "nausea": {"icd10": "R11.0", "snomed": "422587007"},
    "vomiting": {"icd10": "R11.10", "snomed": "422400008"},
    "fever": {"icd10": "R50.9", "snomed": "386661006"},
    "hypertension": {"icd10": "I10", "snomed": "38341003"},
    "diabetes": {"icd10": "E11.9", "snomed": "44054006"},
    "metformin": {"icd10": "", "snomed": "372805003"},
    "aspirin": {"icd10": "", "snomed": "372913009"},
}


def get_socrates_tree(complaint: str) -> list[Question]:
    """Get SOCRATES question tree for a chief complaint."""
    complaint_lower = complaint.lower().replace(" ", "_")
    for key in SOCRATES_TREE:
        if key in complaint_lower or complaint_lower in key:
            return SOCRATES_TREE[key]
    return SOCRATES_TREE["default"]


def get_next_question(state: dict[str, Any]) -> Question | None:
    """Get the next unanswered SOCRATES question based on session state."""
    complaint = state.get("chief_complaint", "")
    tree = get_socrates_tree(complaint)
    answered_slots = set(state.get("answered_slots", []))
    for q in tree:
        if q.slot not in answered_slots:
            return q
    return None


def get_ayush_questions() -> list[Question]:
    """Return all Dashavidha Pariksha questions."""
    return DASHAVIDHA_PARIKSHA


def get_ahara_vihara_questions() -> list[Question]:
    """Return Ahara-Vihara questions."""
    return AHARA_VIHARA_QUESTIONS


def get_ros_questions(system: str | None = None) -> list[Question]:
    """Return ROS questions, optionally filtered by system."""
    if system and system in ROS_CHECKLIST:
        return ROS_CHECKLIST[system]
    all_questions = []
    for questions in ROS_CHECKLIST.values():
        all_questions.extend(questions)
    return all_questions


def get_icd_snomed(concept: str) -> dict[str, str]:
    """Get ICD-10 and SNOMED codes for a concept."""
    return CONCEPT_TO_ICD_SNOMED.get(concept.lower(), {"icd10": "", "snomed": ""})


__all__ = [
    "Question",
    "SOCRATES_TREE",
    "DASHAVIDHA_PARIKSHA",
    "AHARA_VIHARA_QUESTIONS",
    "ROS_CHECKLIST",
    "CONCEPT_TO_ICD_SNOMED",
    "get_socrates_tree",
    "get_next_question",
    "get_ayush_questions",
    "get_ahara_vihara_questions",
    "get_ros_questions",
    "get_icd_snomed",
]