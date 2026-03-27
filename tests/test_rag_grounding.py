import chromadb

import src.graph.f1_turn_graph as f1g
from src.answer.gigachat_rag import GigachatRUSynthesisResult
from src.answer.russian_qna import build_sources_block_ru_from_evidence, qna_confidence_from_evidence
from src.models.api_contracts import AnswerSection, StructuredRUAnswer
from src.retrieval.retriever import COLLECTION_NAME, retrieve_historical_context


def _fake_gigachat_historical(*, evidence, user_question: str = ""):
    block, cc = build_sources_block_ru_from_evidence(evidence)
    summary = evidence[0].snippet.strip()[:120]
    conf = qna_confidence_from_evidence(evidence)
    msg = f"Историческая сводка: {summary}. Уверенность: {conf.tier_ru}."
    return GigachatRUSynthesisResult(
        message=msg,
        structured_answer=StructuredRUAnswer(
            sections=[AnswerSection(heading="Сводка", body=summary)],
            sources_block_ru=block,
            citation_count=cc,
        ),
        confidence=conf,
    )


def _retrieve_with_boosted_scores(
    query: str,
    canonical_entity_ids: list[str],
    *,
    top_k: int = 5,
    min_score: float = 0.35,
):
    hits = retrieve_historical_context(query, canonical_entity_ids, top_k=top_k, min_score=0.0)
    out: list[dict] = []
    for h in hits:
        hh = dict(h)
        hh["score"] = max(float(hh.get("score", 0.0)), 0.91)
        out.append(hh)
    return [h for h in out if h["score"] >= min_score]


def _seed_historical_collection(*, canonical_entity_id: str, source_id: str, snippet: str):
    client = chromadb.PersistentClient(path=".chroma")
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    collection.upsert(
        ids=[f"seed:{source_id}"],
        documents=[snippet],
        metadatas=[
            {
                "dataset": "f1db",
                "canonical_entity_id": canonical_entity_id,
                "source_id": source_id,
            }
        ],
    )


def test_retriever_returns_ranked_hits_from_seeded_index():
    _seed_historical_collection(
        canonical_entity_id="driver:max_verstappen",
        source_id="f1db:race:2023-monaco",
        snippet="Verstappen won Monaco GP in 2023 for Red Bull.",
    )

    hits = retrieve_historical_context(
        "max verstappen monaco",
        ["driver:max_verstappen"],
        top_k=5,
        min_score=0.0,
    )

    assert hits
    assert hits[0]["source_id"] == "f1db:race:2023-monaco"
    assert "Verstappen won Monaco GP" in hits[0]["snippet"]
    assert hits[0]["score"] >= 0.0


def test_next_message_grounds_from_indexed_f1db_context(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "Макс Ферстаппен в Монако"

    _seed_historical_collection(
        canonical_entity_id="driver:max_verstappen",
        source_id="f1db:race:2023-monaco",
        snippet="Verstappen won Monaco GP in 2023 for Red Bull.",
    )

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("max verstappen monaco", ["driver:max_verstappen"], ["driver:max_verstappen"]),
    )
    monkeypatch.setattr(f1g, "retrieve_historical_context", _retrieve_with_boosted_scores)
    monkeypatch.setattr(f1g, "gigachat_judge_rag_sufficient", lambda **_: True)
    monkeypatch.setattr(
        f1g,
        "gigachat_synthesize_historical",
        lambda **kw: _fake_gigachat_historical(**kw),
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert "Историческая сводка" in payload["message"]
    assert payload["details"]["evidence"]


def test_response_contains_traceable_evidence(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "Макс Ферстаппен"

    monkeypatch.setattr(
        "src.api.chat.resolve_entities",
        lambda _query: ("max verstappen", ["driver:max_verstappen"], ["driver:max_verstappen"]),
    )
    monkeypatch.setattr(
        f1g,
        "retrieve_historical_context",
        lambda *_args, **_kwargs: [{"source_id": "f1db:driver:verstappen", "snippet": "Multiple wins in modern era", "score": 0.93}],
    )
    monkeypatch.setattr(
        f1g,
        "gigachat_synthesize_historical",
        lambda **kw: _fake_gigachat_historical(**kw),
    )

    response = client.post("/next_message", headers={"X-Session-Id": sid}, json={})
    assert response.status_code == 200
    payload = response.json()
    evidence = payload["details"]["evidence"][0]
    assert evidence["source_id"]
    assert evidence["snippet"]
    assert evidence["entity_tags"] == ["driver:max_verstappen"]
    assert evidence["rank_score"] > 0
    assert evidence["used_in_answer"] is True
