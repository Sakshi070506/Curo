"""
Module   : Knowledge API
Owner    : ML / RAG Engineer
Purpose  : Clinical knowledge retrieval (RAG) and drug interaction checking.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.config import settings
from backend.database.schemas import (
    DrugInteractionRequest,
    DrugInteractionResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from backend.dependencies import require_auth

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# Lazy-loaded retriever and interaction checker
_retriever = None
_interaction_checker = None


def get_retriever():
    global _retriever
    if _retriever is None:
        from backend.ai.rag.embedding import EmbeddingConfig, get_embedding_model
        from backend.ai.rag.retrieval import ClinicalRetriever, load_concepts_from_ontology

        config = EmbeddingConfig(provider=settings.embedding_provider, model_name=settings.embedding_model)
        embedding_model = get_embedding_model(config)
        concepts = load_concepts_from_ontology()
        _retriever = ClinicalRetriever(concepts=concepts, embedding_model=embedding_model)
    return _retriever


def get_interaction_checker():
    global _interaction_checker
    if _interaction_checker is None:
        from backend.ai.rag.interaction_checker import InteractionChecker
        _interaction_checker = InteractionChecker(csv_path=settings.drug_interactions_csv)
    return _interaction_checker


@router.post("/search", response_model=KnowledgeSearchResponse)
def search_knowledge(req: KnowledgeSearchRequest, user: dict = Depends(require_auth)):
    """Search clinical knowledge base using vector similarity."""
    try:
        retriever = get_retriever()
        results = retriever.search(
            query=req.query,
            k=req.k,
            category=req.category,
            min_similarity=req.min_similarity,
        )
        return KnowledgeSearchResponse(
            results=[
                {
                    "concept_id": r.concept_id,
                    "name": r.name,
                    "category": r.category,
                    "icd_code": r.icd_code,
                    "snomed_code": r.snomed_code,
                    "description": r.description,
                    "similarity": getattr(r, "similarity", 0.0),
                }
                for r in results
            ]
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Knowledge search failed: {exc}")


@router.post("/drug-interactions", response_model=DrugInteractionResponse)
def check_drug_interactions(req: DrugInteractionRequest, user: dict = Depends(require_auth)):
    """Check for drug-drug interactions."""
    try:
        from backend.ai.rag.interaction_checker import check_interactions

        interactions = check_interactions(req.medications, csv_path=settings.drug_interactions_csv)
        checker = get_interaction_checker()
        highest = checker.get_highest_severity(interactions)

        return DrugInteractionResponse(
            interactions=interactions,
            highest_severity=highest,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Drug interaction check failed: {exc}")
