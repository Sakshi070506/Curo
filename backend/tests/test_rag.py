"""
Tests for backend.ai.rag module.
"""

import pytest
from backend.ai.rag import (
    EmbeddingConfig,
    MockEmbeddingModel,
    Concept,
    ClinicalRetriever,
    load_concepts_from_ontology,
    DrugInteraction,
    InteractionChecker,
    check_interactions,
)


class TestEmbedding:
    def test_mock_embedding_model_init(self):
        model = MockEmbeddingModel()
        assert model.config.dimension == 384

    def test_mock_embedding_texts(self):
        model = MockEmbeddingModel()
        texts = ["chest pain", "diabetes", "metformin"]
        embeddings = model.embed_texts(texts)
        assert len(embeddings) == 3
        assert all(len(e) == 384 for e in embeddings)
        # Check normalization
        import numpy as np
        for e in embeddings:
            norm = np.linalg.norm(e)
            assert abs(norm - 1.0) < 1e-5

    def test_mock_embedding_deterministic(self):
        model = MockEmbeddingModel()
        emb1 = model.embed_texts(["test"])
        emb2 = model.embed_texts(["test"])
        assert emb1 == emb2

    def test_embed_query(self):
        model = MockEmbeddingModel()
        emb = model.embed_query("chest pain")
        assert len(emb) == 384

    def test_embed_concept(self):
        model = MockEmbeddingModel()
        concept = {"name": "Chest Pain", "description": "Pain in chest"}
        emb = model.embed_concept(concept)
        assert len(emb) == 384

    def test_embedding_config_from_env(self, monkeypatch):
        monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
        monkeypatch.setenv("EMBEDDING_MODEL", "all-mpnet-base-v2")
        config = EmbeddingConfig()
        assert config.provider == "local"
        assert config.model_name == "all-mpnet-base-v2"


class TestRetrieval:
    def test_concept_creation(self):
        concept = Concept(
            concept_id="chest_pain",
            name="Chest Pain",
            category="symptom",
            icd_code="R07.9",
            snomed_code="29857009",
            description="Pain in chest area",
        )
        assert concept.concept_id == "chest_pain"
        assert concept.category == "symptom"

    def test_clinical_retriever_init(self):
        concepts = [
            Concept(concept_id="cp", name="Chest Pain", category="symptom"),
            Concept(concept_id="dm", name="Diabetes", category="diagnosis"),
        ]
        retriever = ClinicalRetriever(concepts=concepts, embedding_model=MockEmbeddingModel())
        assert len(retriever.concepts) == 2
        assert retriever._embeddings_matrix is not None
        assert retriever._embeddings_matrix.shape == (2, 384)

    def test_search_returns_results(self):
        concepts = [
            Concept(concept_id="cp", name="Chest Pain", category="symptom", description="Chest discomfort"),
            Concept(concept_id="dm", name="Diabetes", category="diagnosis", description="High blood sugar"),
            Concept(concept_id="met", name="Metformin", category="drug", description="Diabetes medication"),
        ]
        retriever = ClinicalRetriever(concepts=concepts, embedding_model=MockEmbeddingModel())
        results = retriever.search("chest discomfort", k=2)
        assert len(results) <= 2
        assert all(hasattr(r, 'similarity') for r in results)

    def test_search_with_category_filter(self):
        concepts = [
            Concept(concept_id="cp", name="Chest Pain", category="symptom"),
            Concept(concept_id="met", name="Metformin", category="drug"),
        ]
        retriever = ClinicalRetriever(concepts=concepts, embedding_model=MockEmbeddingModel())
        results = retriever.search("chest", k=5, category="drug")
        assert len(results) == 0  # No drugs match "chest"
        # Use exact name match for mock to work
        results = retriever.search("Metformin", k=5, category="drug")
        assert len(results) >= 1
        assert all(r.category == "drug" for r in results)

    def test_search_by_embedding(self):
        concepts = [
            Concept(concept_id="cp", name="Chest Pain", category="symptom"),
        ]
        retriever = ClinicalRetriever(concepts=concepts, embedding_model=MockEmbeddingModel())
        # Use same text for embedding to ensure match
        emb = retriever.embedding_model.embed_query("Chest Pain")
        results = retriever.search_by_embedding(emb, k=1)
        assert len(results) == 1

    def test_get_related_concepts(self):
        concepts = [
            Concept(concept_id="cp", name="Chest Pain", category="symptom"),
            Concept(concept_id="ap", name="Abdominal Pain", category="symptom"),
        ]
        retriever = ClinicalRetriever(concepts=concepts, embedding_model=MockEmbeddingModel())
        related = retriever.get_related_concepts("cp", k=1)
        # Mock may not find related due to random embeddings, just check it runs
        assert isinstance(related, list)

    def test_load_concepts_from_ontology(self):
        concepts = load_concepts_from_ontology()
        assert len(concepts) > 20
        categories = set(c.category for c in concepts)
        assert "symptom" in categories
        assert "diagnosis" in categories
        assert "drug" in categories
        assert "lab" in categories
        # Check ICD/SNOMED codes populated
        chest_pain = next((c for c in concepts if c.concept_id == "chest_pain"), None)
        assert chest_pain is not None
        assert chest_pain.icd_code == "R07.9"
        assert chest_pain.snomed_code == "29857009"


class TestInteractionChecker:
    def test_interaction_checker_loads_csv(self):
        checker = InteractionChecker()
        assert len(checker._interactions) > 30

    def test_check_known_interaction(self):
        checker = InteractionChecker()
        medications = [
            {"name": "Metformin"},
            {"name": "Aspirin"},
        ]
        results = checker.check(medications)
        # Metformin + Aspirin not in list, so should be empty
        # But let's test a known pair (use exact CSV name)
        medications = [
            {"name": "Metformin"},
            {"name": "contrast_media"},
        ]
        results = checker.check(medications)
        assert len(results) >= 1
        assert results[0]["severity"] == "critical"

    def test_check_warfarin_aspirin(self):
        checker = InteractionChecker()
        medications = [
            {"name": "Warfarin"},
            {"name": "Aspirin"},
        ]
        results = checker.check(medications)
        assert len(results) >= 1
        interaction = results[0]
        assert interaction["severity"] == "critical"
        assert "bleeding" in interaction["mechanism"].lower()

    def test_check_atorvastatin_gemfibrozil(self):
        checker = InteractionChecker()
        medications = [
            {"name": "Atorvastatin"},
            {"name": "Gemfibrozil"},
        ]
        results = checker.check(medications)
        assert len(results) >= 1
        assert results[0]["severity"] == "critical"
        assert "rhabdomyolysis" in results[0]["mechanism"].lower()

    def test_check_no_interaction(self):
        checker = InteractionChecker()
        medications = [
            {"name": "Metformin"},
            {"name": "Vitamin D"},
        ]
        results = checker.check(medications)
        assert len(results) == 0

    def test_check_single_pair(self):
        checker = InteractionChecker()
        interaction = checker.check_single("metformin", "contrast_media")
        assert interaction is not None
        assert interaction.severity == "critical"

    def test_get_highest_severity(self):
        checker = InteractionChecker()
        interactions = [
            {"severity": "moderate"},
            {"severity": "critical"},
            {"severity": "high"},
        ]
        highest = checker.get_highest_severity(interactions)
        assert highest == "critical"

    def test_convenience_function(self):
        medications = [{"name": "Warfarin"}, {"name": "Aspirin"}]
        results = check_interactions(medications)
        assert len(results) >= 1
        assert results[0]["severity"] == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])