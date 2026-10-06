"""Загрузчик тестовых вакансий из data/vacancies/*.md.

Парсер терпим к ручному вводу:
- решётки # в заголовках опциональны
- маркер пункта: - – — • * или без него
- разделитель "Текст вакансии" с # или без
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
VACANCIES_DIR = BASE_DIR / "data" / "vacancies"

VALID_TYPES = {"ba", "sa", "pm", "negative"}


def parse_vacancy(raw: str) -> dict:
    # Заголовок: "Вакансия 01: ..." — с # или без
    m = re.search(r"^#*\s*(Вакансия[^\n]*)$", raw, re.MULTILINE)
    title = m.group(1).strip() if m else "—"

    def field(name: str) -> str:
        # ловит "-type: ba", "– type: ba", "*type: ba", "type: ba"
        fm = re.search(
            rf"^[^\w\n]*{name}\s*:\s*(.+)$",
            raw, re.MULTILINE | re.IGNORECASE,
        )
        return fm.group(1).strip() if fm else ""

    # Текст: всё после строки-разделителя "Текст вакансии"
    parts = re.split(
        r"^#*\s*Текст вакансии\s*:?\s*$", raw, maxsplit=1, flags=re.MULTILINE
    )
    text = parts[1].strip() if len(parts) == 2 else ""

    return {
        "title": title,
        "company": field("company"),
        "url": field("url"),
        "type": field("type").lower(),
        "date": field("date"),
        "text": text,
    }


def load_vacancies() -> list[dict]:
    if not VACANCIES_DIR.exists():
        raise FileNotFoundError(f"Нет папки: {VACANCIES_DIR}")

    vacancies = []
    for file in sorted(VACANCIES_DIR.glob("*.md")):
        vac = parse_vacancy(file.read_text(encoding="utf-8"))
        vac["file"] = file.name
        vacancies.append(vac)
    return vacancies


def validate(vacancies: list[dict]) -> list[str]:
    problems = []
    for v in vacancies:
        if v["type"] not in VALID_TYPES:
            problems.append(f"{v['file']}: неизвестный type='{v['type']}'")
        if len(v["text"]) < 200:
            problems.append(
                f"{v['file']}: текст {len(v['text'])} симв. (<200) — скопирован не целиком?"
            )
    return problems


if __name__ == "__main__":
    vacs = load_vacancies()
    print(f"Загружено вакансий: {len(vacs)}")

    by_type: dict[str, list[str]] = {}
    for v in vacs:
        by_type.setdefault(v["type"], []).append(v["file"])

    print("\nСостав набора:")
    for t in sorted(by_type):
        print(f"  {t}: {len(by_type[t])} шт. ({', '.join(by_type[t])})")

    problems = validate(vacs)
    if problems:
        print(f"\nПРОБЛЕМЫ ({len(problems)}):")
        for p in problems:
            print(f"  ⚠ {p}")
    else:
        print("\nВсе вакансии валидны ✅")

    print(f"\n=== Пример разбора: {vacs[0]['file']} ===")
    for k, val in vacs[0].items():
        show = val[:120] + "..." if isinstance(val, str) and len(val) > 120 else val
        print(f"  {k}: {show}")
