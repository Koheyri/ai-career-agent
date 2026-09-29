"""Эмбеддинги: превращаем текст в вектор чисел.

Два режима с автовыбором:
- OllamaEmbedder — настоящий, модель nomic-embed-text (включится дома сам)
- FakeEmbedder — заглушка на чистом Python: ищет по совпадению слов
"""

import hashlib
import json
import math
import re
import urllib.request

OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"
VECTOR_SIZE = 256


class FakeEmbedder:
    """Заглушка: вектор = мешок слов из текста."""

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * VECTOR_SIZE
        for w in re.findall(r"\w+", text.lower()):
            idx = int(hashlib.md5(w.encode()).hexdigest(), 16) % VECTOR_SIZE
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]


class OllamaEmbedder:
    """Настоящие эмбеддинги через локальную Ollama."""

    def embed(self, text: str) -> list[float]:
        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/embeddings",
            data=json.dumps({"model": EMBED_MODEL, "prompt": text}).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)["embedding"]


def get_embedder():
    """Если Ollama отвечает — настоящий режим, иначе заглушка."""
    try:
        urllib.request.urlopen(f"{OLLAMA_URL}/api/version", timeout=2)
        print("Embedder: Ollama (nomic-embed-text)")
        return OllamaEmbedder()
    except Exception:
        print("Embedder: FAKE (Ollama не найдена — работаем заглушкой)")
        return FakeEmbedder()