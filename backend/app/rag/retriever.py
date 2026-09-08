"""Recherche sémantique dans la base de connaissances.

L'index est chargé une seule fois (singleton) au premier appel, construit
depuis `knowledge/` ou rechargé depuis `rag_index.json`. Le comportement est
dégradé propre : sans index ni documents, la recherche renvoie une liste vide.
"""

from app.rag.index import Index

_RETRIEVER: Index | None = None


def initialize() -> Index:
    """Prépare (build/recharge) l'index de la base de connaissances."""
    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = Index.load_or_build()
    return _RETRIEVER


def search_knowledge(query: str, top_k: int = 3) -> dict:
    """Retourne les extraits documentaires les plus pertinents pour `query`."""
    try:
        index = initialize()
        results = index.search(query, top_k=top_k)
    except Exception as exc:
        return {"query": query, "top_k": top_k, "results": [], "error": str(exc)}
    return {"query": query, "top_k": top_k, "results": results}


if __name__ == "__main__":  # pragma: no cover
    index = initialize()
    print(f"Index prêt : {index.n_docs} chunks")
    for query in ("adresse APIPA", "vlan mismatch", "passerelle injoignable"):
        results = search_knowledge(query)
        print(f"\nRequête : {query!r}")
        for item in results["results"]:
            print(f"  [{item['score']}] {item['source']} :: {item['title']}")
