"""База знаний: чанки -> эмбеддинги -> поиск по сходству."""

import math

from chunker import make_chunks
from embeddings import get_embedder
from loader import load_candidate


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (na * nb)


class KnowledgeBase:
    def __init__(self):
        self.embedder = get_embedder()
        self.chunks: list[dict] = []
        self.vectors: list[list[float]] = []

    def build(self):
        self.chunks = make_chunks(load_candidate())
        self.vectors = [self.embedder.embed(c["text"]) for c in self.chunks]
        print(f"База собрана: {len(self.chunks)} чанков")
        return self

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        q = self.embedder.embed(query)
        scored = [(cosine(q, v), c) for c, v in zip(self.chunks, self.vectors)]
        scored.sort(key=lambda x: -x[0])
        return [{"score": round(s, 3), **c} for s, c in scored[:top_k]]


if __name__ == "__main__":
    kb = KnowledgeBase().build()
    for query in ["опыт с SQL", "кто работал с BPMN", "пет-проекты на Java"]:
        print(f"\n=== Запрос: {query} ===")
        for r in kb.search(query):
            print(f"  {r['score']} | [{r['id']}] {r['text'][:80]}...")