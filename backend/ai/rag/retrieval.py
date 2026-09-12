"""
Module   : Vector Retrieval
Owner    : ML Engineer
Purpose  : Vector search over clinical knowledge base.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np

from .embedding import EmbeddingConfig, EmbeddingModel, MockEmbeddingModel, get_embedding_model


@dataclass
class Concept:
    concept_id: str
    name: str
    category: str
    icd_code: str = ""
    snomed_code: str = ""
    description: str = ""
    related_questions: list[str] | None = None
    embedding: list[float] | None = None


class ClinicalRetriever:
    """Vector search over clinical knowledge base using pgvector or in-memory FAISS."""

    def __init__(
        self,
        concepts: list[Concept] | None = None,
        embedding_model: EmbeddingModel | MockEmbeddingModel | None = None,
        config: EmbeddingConfig | None = None,
        use_pgvector: bool = False,
        pgvector_conn=None,
    ):
        self.concepts = concepts or []
        self.embedding_model = embedding_model or get_embedding_model(config)
        self.use_pgvector = use_pgvector
        self.pgvector_conn = pgvector_conn
        self._embeddings_matrix = None
        self._build_index()

    def _build_index(self):
        if not self.concepts:
            return

        texts = [f"{c.name} {c.description}".strip() for c in self.concepts]
        embeddings = self.embedding_model.embed_texts(texts)

        for concept, emb in zip(self.concepts, embeddings):
            concept.embedding = emb

        self._embeddings_matrix = np.array(embeddings, dtype=np.float32)
        self._embeddings_matrix = self._embeddings_matrix / np.linalg.norm(
            self._embeddings_matrix, axis=1, keepdims=True
        )

    def add_concepts(self, concepts: list[Concept]):
        """Add new concepts to the index."""
        self.concepts.extend(concepts)
        self._build_index()

    def search(
        self,
        query: str,
        k: int = 5,
        category: str | None = None,
        min_similarity: float = 0.3,
    ) -> list[Concept]:
        """
        Search for top-k similar concepts.

        Args:
            query: Search query text
            k: Number of results to return
            category: Filter by category (symptom/drug/lab/procedure)
            min_similarity: Minimum cosine similarity threshold

        Returns:
            List of matching Concept objects with similarity scores
        """
        if not self.concepts or self._embeddings_matrix is None:
            return []

        query_emb = np.array(self.embedding_model.embed_query(query), dtype=np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)

        similarities = np.dot(self._embeddings_matrix, query_emb)

        if category:
            category_mask = np.array([c.category == category for c in self.concepts])
            similarities = np.where(category_mask, similarities, -1)

        top_k_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_k_indices:
            sim = similarities[idx]
            if sim >= min_similarity:
                concept = self.concepts[idx]
                concept.similarity = float(sim)
                results.append(concept)

        return results

    def search_by_embedding(
        self,
        embedding: list[float],
        k: int = 5,
        category: str | None = None,
        min_similarity: float = 0.3,
    ) -> list[Concept]:
        """Search using pre-computed embedding."""
        if not self.concepts or self._embeddings_matrix is None:
            return []

        query_emb = np.array(embedding, dtype=np.float32)
        query_emb = query_emb / np.linalg.norm(query_emb)

        similarities = np.dot(self._embeddings_matrix, query_emb)

        if category:
            category_mask = np.array([c.category == category for c in self.concepts])
            similarities = np.where(category_mask, similarities, -1)

        top_k_indices = np.argsort(similarities)[::-1][:k]

        results = []
        for idx in top_k_indices:
            sim = similarities[idx]
            if sim >= min_similarity:
                concept = self.concepts[idx]
                concept.similarity = float(sim)
                results.append(concept)

        return results

    def get_related_concepts(self, concept_id: str, k: int = 3) -> list[Concept]:
        """Get concepts related to a given concept ID."""
        concept = next((c for c in self.concepts if c.concept_id == concept_id), None)
        if not concept or not concept.embedding:
            return []

        return self.search_by_embedding(concept.embedding, k=k+1)[1:]


def load_concepts_from_ontology() -> list[Concept]:
    """Load clinical concepts from the clinical ontology module."""
    from backend.ai.nlu import CONCEPT_TO_ICD_SNOMED

    concepts = []
    for name, codes in CONCEPT_TO_ICD_SNOMED.items():
        category = _infer_category(name)
        concepts.append(Concept(
            concept_id=name.lower().replace(" ", "_"),
            name=name,
            category=category,
            icd_code=codes.get("icd10", ""),
            snomed_code=codes.get("snomed", ""),
            description=_get_description(name, category),
        ))

    drug_concepts = _get_drug_concepts()
    concepts.extend(drug_concepts)

    lab_concepts = _get_lab_concepts()
    concepts.extend(lab_concepts)

    return concepts


def _infer_category(name: str) -> str:
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["pain", "headache", "dyspnoea", "nausea", "fever", "vomiting"]):
        return "symptom"
    elif any(kw in name_lower for kw in ["metformin", "aspirin", "insulin", "lisinopril", "atorvastatin"]):
        return "drug"
    elif any(kw in name_lower for kw in ["glucose", "hba1c", "cholesterol", "creatinine", "hemoglobin"]):
        return "lab"
    elif any(kw in name_lower for kw in ["surgery", "operation", "ecg", "echo", "x-ray", "ct", "mri"]):
        return "procedure"
    else:
        return "diagnosis"


def _get_description(name: str, category: str) -> str:
    descriptions = {
        "chest_pain": "Pain or discomfort in the chest area",
        "abdominal_pain": "Pain in the abdominal region",
        "headache": "Pain in the head or upper neck",
        "dyspnoea": "Shortness of breath or difficulty breathing",
        "nausea": "Sensation of wanting to vomit",
        "fever": "Elevated body temperature",
        "hypertension": "High blood pressure",
        "diabetes": "Diabetes mellitus type 2",
        "metformin": "First-line medication for type 2 diabetes",
        "aspirin": "Antiplatelet agent for cardiovascular protection",
    }
    return descriptions.get(name.lower(), f"Clinical concept: {name}")


def _get_drug_concepts() -> list[Concept]:
    drugs = [
        ("metformin", "Metformin", "Biguanide antidiabetic", "372805003", ""),
        ("aspirin", "Aspirin", "Antiplatelet/NSAID", "372913009", ""),
        ("lisinopril", "Lisinopril", "ACE inhibitor", "373543003", ""),
        ("atorvastatin", "Atorvastatin", "Statin lipid-lowering", "373354003", ""),
        ("amlodipine", "Amlodipine", "Calcium channel blocker", "373368001", ""),
        ("metoprolol", "Metoprolol", "Beta blocker", "373416008", ""),
        ("omeprazole", "Omeprazole", "Proton pump inhibitor", "373462005", ""),
        ("insulin", "Insulin", "Hormone for diabetes", "387107003", ""),
    ]
    concepts = []
    for cid, name, desc, snomed, icd in drugs:
        concepts.append(Concept(
            concept_id=cid,
            name=name,
            category="drug",
            icd_code=icd,
            snomed_code=snomed,
            description=desc,
        ))
    return concepts


def _get_lab_concepts() -> list[Concept]:
    labs = [
        ("hba1c", "HbA1c", "Glycated hemoglobin", "", "43396009"),
        ("glucose_fasting", "Fasting Glucose", "Fasting blood glucose", "", "33747003"),
        ("cholesterol_total", "Total Cholesterol", "Total serum cholesterol", "", "166833005"),
        ("ldl", "LDL Cholesterol", "Low-density lipoprotein", "", "386428001"),
        ("hdl", "HDL Cholesterol", "High-density lipoprotein", "", "166834004"),
        ("triglycerides", "Triglycerides", "Serum triglycerides", "", "271394009"),
        ("creatinine", "Serum Creatinine", "Kidney function marker", "", "384834008"),
        ("urea", "Blood Urea", "Blood urea nitrogen", "", "384833002"),
        ("hemoglobin", "Hemoglobin", "Oxygen-carrying protein", "", "58321007"),
        ("tsh", "TSH", "Thyroid stimulating hormone", "", "254540009"),
    ]
    concepts = []
    for cid, name, desc, icd, snomed in labs:
        concepts.append(Concept(
            concept_id=cid,
            name=name,
            category="lab",
            icd_code=icd,
            snomed_code=snomed,
            description=desc,
        ))
    return concepts


__all__ = [
    "Concept",
    "ClinicalRetriever",
    "load_concepts_from_ontology",
]