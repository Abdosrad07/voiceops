"""Embeddings de documents : vectorisation locale, sans réseau ni dépendance lourde.

MVP : représentation bag-of-words pondérée (TF-IDF) avec normalisation
(lowercase, sans accents, racines simples). Le module est volontairement
simple pour être remplacé par un modèle d'embeddings réel (ex. sentence
transformers) à la Phase 5 finale sans changer le contrat de l'index.
"""

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Iterable

ACCENTS = dict.fromkeys(
    "àáâäãåèéêëìíîïòóôöõùúûüçñÿ",
    "",
)
STOPWORDS = {
    "le", "la", "les", "de", "du", "des", "un", "une", "et", "ou", "a", "au",
    "aux", "en", "dans", "pour", "sur", "que", "qui", "quoi", "est", "sont",
    "pas", "ne", "plus", "si", "il", "elle", "ce", "cette", "ces",
    "avec", "sans", "par", "comme", "vers", "qu", "d", "l", "n", "s", "tout",
    "toute", "tous", "poste", "postes",
}


def normalize(text: str) -> str:
    """Normalise un texte : minuscules, accents ôtés, espaces réduits."""
    text = unicodedata.normalize("NFKD", text or "").lower()
    text = text.translate(ACCENTS)
    return re.sub(r"[^a-z0-9 ]", " ", text)


def tokenize(text: str) -> list[str]:
    tokens = normalize(text).split()
    return [t for t in tokens if len(t) > 1 and t not in STOPWORDS]


def term_frequencies(tokens: Iterable[str]) -> Counter:
    return Counter(tokens)


def cosine(a: dict[str, float], b: dict[str, float]) -> float:
    """Similarité cosinus entre deux vecteurs creux."""
    if not a or not b:
        return 0.0
    common = set(a) & set(b)
    if not common:
        return 0.0
    dot = sum(a[t] * b[t] for t in common)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
