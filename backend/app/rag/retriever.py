"""Recherche dans la base de connaissances (Phase 5 vient compléter l'index)."""

_RETRIEVER = None  # index FAISS/jetons initialisé à la Phase 5


def search_knowledge(query: str, top_k: int = 3) -> dict:
    """Retourne les extraits documentaires les plus pertinents pour `query`."""
    if _RETRIEVER is None:
        return {"query": query, "top_k": top_k, "results": []}
    return _RETRIEVER.search(query, top_k=top_k)
