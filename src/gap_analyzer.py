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

# Плейсхолдеры подставляются через replace() — фигурные скобки
# в JSON-примере не мешают, шаблон можно править как в Confluence
PROMPT_TEMPLATE = """Ты — карьерный аналитик. Сравни профиль кандидата с требованиями вакансии.

КОНТЕКСТ КАНДИДАТА:
{CANDIDATE_CHUNKS}

ВАКАНСИЯ:
{VACANCY_TEXT}

Задачи:
1. Оцени соответствие в процентах
2. Найди пересечения: требования вакансии, закрытые профилем
3. Найди пробелы (gaps): требования, которых нет в профиле
4. Оцени риски по категориям: опыт, навыки, образование

Формат ответа — только JSON, без пояснений до и после:
{"match_score": число 0-100, "matched": [{"requirement": "...", "evidence": "цитата из контекста"}], "gaps": [{"requirement": "...", "severity": "критично или желательно"}], "risks": {"experience": "...", "skills": "...", "education": "..."}, "summary": "вывод в 2-3 предложениях"}

Каждый пункт matched обязан содержать цитату из контекста.
Лимиты компактности:
- Максимум 5 пунктов в matched и максимум 5 в gaps — выбирай самые важные.
- Цитата-доказательство: до 15 слов.

Калибровка match_score (обязательная):
- Если 3+ gaps с severity "критично" — score НЕ может быть выше 40.
- Если большинство ключевых требований вакансии закрыть нечем — score 10-30.
- score отражает реальную долю закрытых критичных требований, а не вежливость.
- Противоречие "много критичных gaps, но высокий score" запрещено.
Выдумывать доказательства запрещено.
- Соблюдай guardrails из контекста кандидата: не выдавай учебные проекты за коммерческий опыт, высшее образование не завершено, глубину навыков не завышать, руководство = только подтверждённое.
- Если требование вакансии нельзя проверить по контексту — помечай его в gaps, а не придумывай соответствие."""


def ask_ollama(prompt: str) -> str:
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_ctx": 4096, "temperature": 0.1, "num_predict": 2048},
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
        return extract_json(raw)
    except Exception:
        # Модель вернула мусор — сохраняем сырой ответ для диагностики
        return {"_parse_error": True, "_raw": raw[:1500]}


if __name__ == "__main__":
    kb = KnowledgeBase().build()
    vacs = load_vacancies()
    vac = vacs[0]  # vacancy_01 — бизнес-аналитик, ожидаем высокий match

    expect = "низкий" if vac["type"] == "negative" else "высокий"
    print(f"\nАнализ: {vac['file']} — {vac['title']}")
    print(f"Ожидание: {expect} match")
    print("Модель думает... (1-5 минут на CPU — это нормально)")

    t0 = time.time()
    report = analyze(vac["text"], kb)
    dt = time.time() - t0

    print(f"\nВремя: {dt:.0f} сек")
    print(json.dumps(report, ensure_ascii=False, indent=2))
