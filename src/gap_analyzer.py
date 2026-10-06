"""Модуль Gap Analysis: профиль vs вакансия через локальную LLM.

Конвейер (RAG в действии):
вакансия -> retriever находит релевантные чанки профиля
-> промпт (шаблон из Confluence) -> qwen2.5:3b через Ollama -> JSON-отчёт.
"""

import json
import re
import time
import urllib.request

from retriever import KnowledgeBase
from vacancy_loader import load_vacancies

OLLAMA_URL = "http://localhost:11434"
LLM_MODEL = "qwen2.5:3b"

PROMPT_TEMPLATE = """Ты — карьерный аналитик. Сравни профиль кандидата с требованиями вакансии.

КОНТЕКСТ КАНДИДАТА:
{CANDIDATE_CHUNKS}

ВАКАНСИЯ:
{VACANCY_TEXT}

Алгоритм — выполняй строго по шагам:
Шаг 1. Выпиши до 5 КЛЮЧЕВЫХ требований вакансии — без которых работу не выполнить. Строки "будет плюсом", пожелания по годам опыта и отрасли — НЕ ключевые, если не помечены словом "обязательно". Включай специфичные требования (конкретные системы, инструменты, отраслевой опыт), а не только общие навыки вроде Excel и коммуникации.
Шаг 2. По каждому требованию ищи в контексте кандидата прямое подтверждение. Есть — met=true и цитата до 15 слов. Нет — met=false, evidence="".
Шаг 3. critical_total = сколько выписал, critical_met = сколько met=true.

Правила строгости:
- Цитата обязана ПРЯМО подтверждать требование. Нет прямой цитаты — met=false.
- Одна цитата не закрывает несколько разных требований.
- Выдумывать доказательства запрещено.
- Соблюдай guardrails из контекста: учебные проекты — не коммерческий опыт; высшее образование не завершено; глубину навыков не завышать; руководство — только подтверждённое.

gaps — квалификационные пробелы ВНЕ списка critical. Условия работы (график, локация, зарплата, размер команды) — не gaps.

Формат ответа — только JSON, без пояснений до и после:
{"critical_requirements": [{"requirement": "...", "met": true, "evidence": "цитата из контекста"}], "critical_total": 5, "critical_met": 3, "match_score": 60, "gaps": [{"requirement": "...", "severity": "критично или желательно"}], "risks": {"experience": "...", "skills": "...", "education": "..."}, "summary": "вывод в 2-3 предложениях"}
"""


def ask_ollama(prompt: str, temperature: float = 0.1) -> str:
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 4096, "temperature": temperature, "num_predict": 3072},
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.load(resp)["response"]


def extract_json(text: str) -> dict:
    """Достаёт JSON: выносит из ```-блоков или берёт балансный {...}."""
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    start = text.find("{")
    if start == -1:
        raise ValueError("В ответе нет JSON")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start : i + 1])
    raise ValueError("JSON не закрыт")


def recalc_score(report: dict) -> dict:
    """Score считает Python по меткам модели, а не доверяет её числу."""
    reqs = report.get("critical_requirements", [])
    if isinstance(reqs, list) and reqs:
        met = sum(1 for r in reqs if r.get("met") is True)
        report["match_score"] = round(met / len(reqs) * 100)
    return report


def analyze(vacancy_text: str, kb: KnowledgeBase, top_k: int = 6) -> dict:
    hits = kb.search(vacancy_text[:1500], top_k=top_k)
    chunks_text = "\n---\n".join(f"[{h['id']}] {h['text']}" for h in hits)
    prompt = (
        PROMPT_TEMPLATE
        .replace("{CANDIDATE_CHUNKS}", chunks_text)
        .replace("{VACANCY_TEXT}", vacancy_text[:2500])
    )
    raw = ask_ollama(prompt)
    try:
        return recalc_score(extract_json(raw))
    except Exception:
        # Повторная попытка: свежая генерация с большей температурой
        # (зацикливание модели случайно, повтор обычно чистый)
        raw = ask_ollama(prompt, temperature=0.5)
        try:
            return recalc_score(extract_json(raw))
        except Exception:
            return {"_parse_error": True, "_raw": raw[:1500]}


if __name__ == "__main__":
    kb = KnowledgeBase().build()
    vacs = load_vacancies()
    vac = vacs[0]

    expect = "низкий" if vac["type"] in ("negative", "stretch") else "высокий"
    print(f"\nАнализ: {vac['file']} — {vac['title']}")
    print(f"Ожидание: {expect} match")
    print("Модель думает...")

    t0 = time.time()
    report = analyze(vac["text"], kb)
    dt = time.time() - t0

    print(f"\nВремя: {dt:.0f} сек")
    print(json.dumps(report, ensure_ascii=False, indent=2))
