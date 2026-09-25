import os

# ============ API ============
# Ключ НИКОГДА не вписываем в код. Он будет храниться в переменной окружения
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Если будем использовать локальную модель через Ollama
OLLAMA_BASE_URL = "http://localhost:11434"

# ============ Пути к данным ============
DATA_DIR = "data"
CANDIDATE_FILE = os.path.join(DATA_DIR, "candidate.json")

# ============ Параметры эмбеддингов ============
EMBEDDING_MODEL = "text-embedding-3-small"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# ============ ChromaDB ============
CHROMA_PERSIST_DIR = "chroma_db"
