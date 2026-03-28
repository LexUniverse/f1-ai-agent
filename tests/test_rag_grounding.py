import os

import chromadb
import pytest

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
    )


def _retrieve_with_boosted_scores(
    query: str,
    canonical_entity_ids: list[str],
    *,
    top_k: int = 5,
    min_score: float = 0.25,
):
    hits = retrieve_historical_context(query, canonical_entity_ids, top_k=top_k, min_score=0.0)
    out: list[dict] = []
    for h in hits:
        hh = dict(h)
        hh["score"] = max(float(hh.get("score", 0.0)), 0.91)
        out.append(hh)
    return [h for h in out if h["score"] >= min_score]


def _seed_historical_collection(*, source_id: str, snippet: str):
    from src.retrieval.embeddings import get_embedding_function

    client = chromadb.PersistentClient(path=".chroma")
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )
    collection.upsert(
        ids=[f"seed:{source_id}"],
        documents=[snippet],
        metadatas=[
            {
                "dataset": "f1db",
                "source_id": source_id,
            }
        ],
    )


def test_retriever_returns_ranked_hits_from_seeded_index():
    _seed_historical_collection(
        source_id="f1db:race:2023-monaco",
        snippet="Гран-при Монако 2023: победил Макс Ферстаппен Red Bull.",
    )

    hits = retrieve_historical_context(
        "Монако 2023 Ферстаппен",
        [],
        top_k=5,
        min_score=0.0,
    )

    assert hits
    assert hits[0]["source_id"] == "f1db:race:2023-monaco"
    assert "Ферстаппен" in hits[0]["snippet"] or "Монако" in hits[0]["snippet"]
    assert hits[0]["score"] >= 0.0


def test_next_message_grounds_from_indexed_f1db_context(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "Макс Ферстаппен в Монако 2023"

    _seed_historical_collection(
        source_id="f1db:race:2023-monaco",
        snippet="Гран-при Монако 2023: победил Макс Ферстаппен Red Bull.",
    )

    monkeypatch.setattr(f1g, "retrieve_historical_context", _retrieve_with_boosted_scores)
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: True)
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


def _seed_from_docs(docs: list[tuple[str, str, dict]]) -> None:
    from src.retrieval.embeddings import get_embedding_function

    client = chromadb.PersistentClient(path=".chroma")
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=get_embedding_function(),
    )
    ids = [x[0] for x in docs]
    texts = [x[1] for x in docs]
    metas = [x[2] for x in docs]
    collection.upsert(ids=ids, documents=texts, metadatas=metas)


def test_retrieval_monaco_2000_winner_in_hits():
    monaco_ru = (
        "Победитель Гран-при Монако 2000 — Дэвид Култхард (David Coulthard, McLaren).\n"
        "Формула 1, сезон 2000, этап 7 — Гран-при: Monaco Grand Prix.\n"
        "Официальное название гонки: Grand Prix de Monaco 2000.\n"
        "страна проведения: Monaco (monaco)\n"
        "Идентификаторы для поиска: grand prix Monaco Grand Prix, monaco, год 2000, круг 7.\n"
        "Результат гонки (подиум): место 1 David Coulthard, очки 10.\n"
    )
    _seed_from_docs(
        [
            (
                "chunk:monaco-2000",
                monaco_ru,
                {
                    "dataset": "f1db",
                    "source_id": "f1db:season-summary:2000:gp:7:monaco",
                    "year": "2000",
                    "grand_prix_id": "monaco",
                    "chunk_kind": "grand_prix_race",
                    "table": "f1db-season-summary",
                },
            ),
        ]
    )

    hits = retrieve_historical_context(
        "гран при монако 2000 победитель",
        [],
        top_k=10,
        min_score=0.0,
    )
    union = " ".join(h["snippet"] for h in hits).lower()
    assert "култхард" in union or "coulthard" in union


def test_retrieval_2021_champion_in_hits():
    overview = (
        "Формула 1, сезон 2021 год. В итоговой классификации чемпионата участвовало 22 гонщиков. "
        "Чемпион мира среди пилотов: Max Verstappen.\n"
        "Итоговая таблица пилотов (команда — гонщик — место — очки за сезон):\n"
        "1. Red Bull — Max Verstappen — 395.5 очков\n"
    )
    _seed_from_docs(
        [
            (
                "chunk:2021-overview",
                overview,
                {
                    "dataset": "f1db",
                    "source_id": "f1db:season-summary:2021:overview",
                    "year": "2021",
                    "chunk_kind": "season_overview",
                    "table": "f1db-season-summary",
                },
            ),
        ]
    )

    hits = retrieve_historical_context(
        "чемпион формулы 1 в 2021 году кто",
        [],
        top_k=10,
        min_score=0.0,
    )
    union = " ".join(h["snippet"] for h in hits).lower()
    assert "verstappen" in union or "ферстаппен" in union


@pytest.mark.integration_index
def test_full_index_monaco_2000_winner_requires_env_and_csv():
    if os.environ.get("RUN_F1_INDEX_INTEGRATION") != "1":
        pytest.skip("set RUN_F1_INDEX_INTEGRATION=1 after build_historical_index()")
    from pathlib import Path

    if not Path("f1db-csv/f1db-races.csv").exists():
        pytest.skip("f1db-csv not present")

    hits = retrieve_historical_context(
        "гран при монако 2000",
        [],
        top_k=15,
        min_score=0.0,
    )
    union = " ".join(h["snippet"] for h in hits).lower()
    assert "coulthard" in union


def test_response_contains_traceable_evidence(client, monkeypatch):
    start = client.post("/start_chat", json={"access_code": "ABC123"})
    sid = start.json()["session_id"]
    session = client.app.state.session_store.get(sid)
    assert session is not None
    session.next_message = "Макс Ферстаппен"

    monkeypatch.setattr(
        f1g,
        "retrieve_historical_context",
        lambda *_args, **_kwargs: [{"source_id": "f1db:driver:verstappen", "snippet": "Multiple wins in modern era", "score": 0.93}],
    )
    monkeypatch.setattr(f1g, "gigachat_supervisor_accept_answer", lambda **_: True)
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
    assert evidence["entity_tags"] == []
    assert evidence["rank_score"] > 0
    assert evidence["used_in_answer"] is True
