"""Construction et persistance de l'index de la base de connaissances.

Lecture des documents Markdown de `knowledge/`, découpage en chunks et calcul
du vecteur TF-IDF de chaque chunk. L'index est sauvegardé en JSON (aucune
dépendance lourde) et rechargeable sans relire les documents.
"""

import json
import math
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import BASE_DIR, settings
from app.rag.embeddings import term_frequencies, tokenize

DEFAULT_KB_DIR = BASE_DIR.parent / "knowledge"
CHUNK_MAX_CHARS = 700
IDF_SMOOTHING = 1.0


@dataclass
class Chunk:
    doc: str
    title: str
    text: str
    tokens: Counter = field(default_factory=Counter)
    vector: dict[str, float] = field(default_factory=dict)
    id: str = ""


def _iter_markdown(kb_dir: Path):
    yield from sorted(kb_dir.rglob("*.md"))


def _chunk_text(text: str) -> list[str]:
    """Découpe un paragraphe en morceaux de ~CHUNK_MAX_CHARS."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    for para in paragraphs:
        while len(para) > CHUNK_MAX_CHARS:
            split = para[:CHUNK_MAX_CHARS].rsplit(". ", 1)[0]
            if len(split) < CHUNK_MAX_CHARS // 2:
                split = para[:CHUNK_MAX_CHARS]
            chunks.append(split.strip())
            para = para[len(split):].lstrip()
        if para:
            chunks.append(para.strip())
    return chunks


class Index:
    """Index vectoriel TF-IDF des documents de `knowledge/`."""

    def __init__(self, kb_dir: Path | None = None):
        self.kb_dir = kb_dir or DEFAULT_KB_DIR
        self.chunks: list[Chunk] = []
        self.doc_freq: Counter = Counter()
        self.n_docs = 0
        self.ready = False

    def _df(self, term: str) -> float:
        return math.log((self.n_docs + IDF_SMOOTHING) / (self.doc_freq[term] + IDF_SMOOTHING))

    def build(self) -> None:
        self.chunks = []
        self.doc_freq = Counter()
        self.n_docs = 0
        corpus_tokens: list[Counter] = []

        for path in _iter_markdown(self.kb_dir):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pos, chunk_text in enumerate(_chunk_text(text)):
                tokens = term_frequencies(tokenize(chunk_text))
                if not tokens:
                    continue
                title = path.stem
                chunk = Chunk(
                    doc=str(path.relative_to(self.kb_dir.parent)),
                    title=title,
                    text=chunk_text,
                    tokens=tokens,
                    id=f"{path.stem}#{pos}",
                )
                self.chunks.append(chunk)
                corpus_tokens.append(tokens)
                for term in tokens:
                    self.doc_freq[term] += 1

        self.n_docs = len(self.chunks)
        for chunk in self.chunks:
            chunk.vector = {
                term: count * self._df(term) for term, count in chunk.tokens.items()
            }
        self.ready = True

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        from app.rag.embeddings import cosine

        if not self.ready:
            return []
        qvec = {
            term: count * self._df(term)
            for term, count in term_frequencies(tokenize(query)).items()
        }
        scored = sorted(
            ((cosine(chunk.vector, qvec), chunk) for chunk in self.chunks),
            key=lambda item: item[0],
            reverse=True,
        )
        results = []
        for score, chunk in scored[:top_k]:
            if score <= 0:
                continue
            results.append(
                {
                    "chunk_id": chunk.id,
                    "source": chunk.doc,
                    "title": chunk.title,
                    "text": chunk.text,
                    "score": round(score, 4),
                }
            )
        return results

    def to_dict(self) -> dict:
        return {
            "n_docs": self.n_docs,
            "doc_freq": dict(self.doc_freq),
            "chunks": [
                {
                    "id": c.id,
                    "doc": c.doc,
                    "title": c.title,
                    "text": c.text,
                    "tokens": dict(c.tokens),
                }
                for c in self.chunks
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Index":
        index = cls()
        index.n_docs = data.get("n_docs", 0)
        index.doc_freq = Counter(data.get("doc_freq", {}))
        index.chunks = []
        for item in data.get("chunks", []):
            chunk = Chunk(
                id=item["id"],
                doc=item["doc"],
                title=item["title"],
                text=item["text"],
                tokens=Counter(item.get("tokens", {})),
            )
            chunk.vector = {
                term: count * index._df(term) for term, count in chunk.tokens.items()
            }
            index.chunks.append(chunk)
        index.ready = True
        return index

    def save(self, path: Path | None = None) -> Path:
        target = path or Path(settings.rag_index_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.to_dict(), ensure_ascii=False), encoding="utf-8")
        return target

    @classmethod
    def load_or_build(cls, index_path: Path | None = None) -> "Index":
        target = index_path or Path(settings.rag_index_path)
        if target.exists():
            try:
                return cls.from_dict(json.loads(target.read_text(encoding="utf-8")))
            except (ValueError, KeyError):
                pass
        index = cls()
        index.build()
        return index
