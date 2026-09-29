"""Чанкинг профиля кандидата для RAG.

Режет candidate.json на смысловые куски (чанки),
которые позже превратятся в эмбеддинги и лягут в ChromaDB.
"""

from loader import load_candidate


def make_chunks(profile: dict) -> list[dict]:
    """Собирает список чанков из профиля. Каждый чанк: id, section, text."""
    chunks = []

    # 1. Профиль: имя, город, формат, языки
    cand = profile.get("candidate", {})
    langs = ", ".join(f"{k} — {v}" for k, v in cand.get("languages", {}).items())
    chunks.append({
        "id": "meta",
        "section": "profile",
        "text": (
            f"Кандидат: {cand.get('name', '—')}. "
            f"Город: {cand.get('city', '—')}. "
            f"Формат работы: {', '.join(cand.get('format', []))}. "
            f"Языки: {langs}. "
            f"Релокация: {'да' if cand.get('relocation') else 'нет'}."
        ),
    })

    # 2. Целевые роли
    roles = ", ".join(
        f"{r['title']} (приоритет {r['priority']})"
        for r in profile.get("target_roles", [])
    )
    chunks.append({
        "id": "target_roles",
        "section": "profile",
        "text": f"Целевые роли кандидата: {roles}.",
    })

    # 3. Хард-скиллы: один чанк на категорию
    for category, skills in profile.get("hard_skills", {}).items():
        chunks.append({
            "id": f"skills_{category}",
            "section": "skills",
            "text": f"Навыки ({category}): {', '.join(skills)}.",
        })

    # 4. Опыт: один чанк на место работы
    for i, job in enumerate(profile.get("experience", []), start=1):
        text = (
            f"Опыт работы: {job['title']} в {job['company']} ({job['period']}). "
            f"Обязанности и результаты: {'; '.join(job.get('facts', []))}."
        )
        if job.get("achievements"):
            text += f" Достижения: {'; '.join(job['achievements'])}."
        chunks.append({
            "id": f"experience_{i}",
            "section": "experience",
            "text": text,
        })

    # 5. Пет-проекты
    for i, proj in enumerate(profile.get("pet_projects", []), start=1):
        chunks.append({
            "id": f"project_{i}",
            "section": "projects",
            "text": (
                f"Пет-проект: {proj['name']}. Стек: {proj['stack']}. "
                f"Код: {proj.get('url', '—')}."
            ),
        })

    # 6. Образование
    edu = "; ".join(
        f"{e['place']} ({e['year']}) — {e['detail']}"
        for e in profile.get("education", [])
    )
    chunks.append({
        "id": "education",
        "section": "education",
        "text": f"Образование: {edu}.",
    })

    # 7. Сертификаты
    certs = "; ".join(
        f"{c['name']} — {c['org']} ({c['year']})"
        for c in profile.get("certificates", [])
    )
    chunks.append({
        "id": "certificates",
        "section": "education",
        "text": f"Сертификаты: {certs}.",
    })

    return chunks


if __name__ == "__main__":
    chunks = make_chunks(load_candidate())
    print(f"Всего чанков: {len(chunks)}\n")
    for c in chunks:
        print(f"[{c['id']}] {c['text']}\n")