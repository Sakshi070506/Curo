"""
Tests for Knowledge API endpoints.
"""

from fastapi.testclient import TestClient

from backend.main import app


def test_knowledge_search():
    client = TestClient(app)
    resp = client.post("/api/knowledge/search", json={
        "query": "chest pain",
        "k": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert isinstance(data["results"], list)
    # Should find chest pain related concepts
    if data["results"]:
        result = data["results"][0]
        assert "concept_id" in result
        assert "name" in result
        assert "category" in result
        assert "similarity" in result


def test_knowledge_search_with_category():
    client = TestClient(app)
    resp = client.post("/api/knowledge/search", json={
        "query": "metformin",
        "k": 5,
        "category": "drug"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    for r in data["results"]:
        assert r["category"] == "drug"


def test_drug_interaction_check():
    client = TestClient(app)
    resp = client.post("/api/knowledge/drug-interactions", json={
        "medications": [
            {"name": "Warfarin"},
            {"name": "Aspirin"}
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "interactions" in data
    assert "highest_severity" in data
    # Warfarin + Aspirin should have critical interaction
    if data["interactions"]:
        assert data["highest_severity"] == "critical"


def test_drug_interaction_no_interaction():
    client = TestClient(app)
    resp = client.post("/api/knowledge/drug-interactions", json={
        "medications": [
            {"name": "Metformin"},
            {"name": "Vitamin D"}
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["interactions"] == []
    assert data["highest_severity"] == "none"
