import os

# ============ LLM ============
# Работаем через Ollama — локально и бесплатно
LLM_MODEL = "qwen2.5:3b"
OLLAMA_BASE_URL = "http://localhost:11434"

# ============ Пути к данным ============
DATA_DIR = "data"
CANDIDATE_FILE = os.path.join(DATA_DIR, "candidate.json")

# ============ Параметры эмбеддингов ============
EMBEDDING_MODEL = "nomic-embed-text"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ============ ChromaDB ============
CHROMA_PERSIST_DIR = "chroma_db"
