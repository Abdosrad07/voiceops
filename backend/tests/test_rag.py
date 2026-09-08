from pathlib import Path

from app.rag import embeddings
from app.rag import index as rag_index
from app.rag.retriever import search_knowledge


def _build_index(tmp_path: Path) -> rag_index.Index:
    kb = tmp_path / "knowledge"
    (kb / "networking").mkdir(parents=True)
    (kb / "networking" / "dhcp.md").write_text(
        "## DHCP\nQuand le serveur DHCP ne répond pas, le poste obtient une adresse "
        "APIPA 169.254.x.x. C'est le principal symptome d'un echec DHCP.",
        encoding="utf-8",
    )
    (kb / "networking" / "vlan.md").write_text(
        "## VLAN\nUn port en VLAN incorrect bloque DHCP. Verifier le switchport access "
        "vlan et la presence du VLAN sur le trunk.",
        encoding="utf-8",
    )
    index_obj = rag_index.Index(kb_dir=kb)
    index_obj.build()
    return index_obj


def test_index_build_and_search_returns_relevant_chunk(tmp_path: Path) -> None:
    index_obj = _build_index(tmp_path)
    assert index_obj.n_docs == 2
    assert all(c.vector for c in index_obj.chunks)

    apipa = index_obj.search("adresse APIPA echec dhcp")
    assert apipa
    assert apipa[0]["title"].startswith("dhcp")

    vlan = index_obj.search("port vlan incorrect switch")
    assert vlan
    assert vlan[0]["title"].startswith("vlan")


def test_index_roundtrip_json(tmp_path: Path) -> None:
    index_obj = _build_index(tmp_path)
    path = tmp_path / "index.json"
    index_obj.save(path)
    loaded = rag_index.Index.load_or_build(path)
    assert loaded.n_docs == index_obj.n_docs
    assert loaded.search("APIPA dhcp")


def test_retriever_graceful_without_docs(monkeypatch) -> None:
    monkeypatch.setattr(
        rag_index.Index,
        "load_or_build",
        lambda *a, **k: rag_index.Index(kb_dir=Path("does-not-exist")),
    )
    monkeypatch.setattr("app.rag.retriever._RETRIEVER", None)
    out = search_knowledge("APIPA")
    assert out["results"] == []


def test_search_knowledge_integration() -> None:
    """Contrat outil : la recherche renvoie structurellement des résultats/une erreur."""
    out = search_knowledge("adresse APIPA", top_k=2)
    assert "query" in out and "results" in out
    for item in out["results"]:
        assert {"chunk_id", "source", "title", "text", "score"} <= set(item)


def test_embeddings_cosine_and_tokenize() -> None:
    assert embeddings.cosine({"vlan": 2}, {"vlan": 2, "dhcp": 1}) > 0
    assert embeddings.cosine({"vlan": 1}, {"dhcp": 1}) == 0
    tokens = embeddings.tokenize("Le VLAN est incorrect")
    assert "vlan" in tokens
    assert "le" not in tokens
