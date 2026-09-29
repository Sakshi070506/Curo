"""
Module   : Ontology Seeder
Owner    : ML Engineer
Purpose  : Loads SOCRATES/Dashavidha Pariksha question trees + clinical_knowledge table.
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add repo root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ai.rag.retrieval import load_concepts_from_ontology
from backend.database.connection import get_engine, get_session_factory
from backend.database.models import ClinicalKnowledge


async def main():
    from backend.config import settings

    print(f"[seed_ontology] Using database: {settings.database_url}")

    engine = get_engine()
    SessionLocal = get_session_factory(engine)

    # Load concepts from ontology
    concepts = load_concepts_from_ontology()
    print(f"[seed_ontology] Loaded {len(concepts)} concepts from ontology")

    # Insert into database
    async with SessionLocal() as session:
        for concept in concepts:
            # Check if already exists
            existing = await session.get(ClinicalKnowledge, concept.concept_id)
            if existing:
                print(f"[seed_ontology] Skipping existing concept: {concept.concept_id}")
                continue

            ck = ClinicalKnowledge(
                id=str(uuid.uuid4()),
                concept_id=concept.concept_id,
                name=concept.name,
                category=concept.category,
                icd_code=concept.icd_code or "",
                snomed_code=concept.snomed_code or "",
                description=concept.description or "",
                related_questions=concept.related_questions or [],
                embedding=concept.embedding,
            )
            session.add(ck)

        await session.commit()
        print(f"[seed_ontology] Successfully seeded {len(concepts)} concepts!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
