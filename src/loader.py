"""Загрузчик профиля кандидата из data/candidate.json."""

import json
from pathlib import Path

# Путь считаем от корня проекта, а не от папки src
BASE_DIR = Path(__file__).parent.parent
CANDIDATE_FILE = BASE_DIR / "data" / "candidate.json"


def load_candidate() -> dict:
    """Читает candidate.json и возвращает словарь профиля."""
    if not CANDIDATE_FILE.exists():
        raise FileNotFoundError(f"Не найден файл: {CANDIDATE_FILE}")
    with open(CANDIDATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def summarize(profile: dict) -> str:
    """Краткая сводка профиля — для быстрой проверки данных."""
    skills = profile.get("hard_skills", {})
    total_skills = sum(len(v) for v in skills.values())
    exp = profile.get("experience", [])

    lines = [
        f"Имя: {profile['candidate'].get('name', '—')}",
        f"Город: {profile['candidate'].get('city', '—')}",
        "Целевые роли: " + ", ".join(
            r["title"] for r in profile.get("target_roles", [])
        ),
        f"Хард-скиллы: {total_skills} шт. в {len(skills)} категориях",
        f"Места работы: {len(exp)}",
    ]
    for job in exp:
        lines.append(f"  - {job['company']} — {job['title']} ({job['period']})")
    return "\n".join(lines)


if __name__ == "__main__":
    print(summarize(load_candidate()))
