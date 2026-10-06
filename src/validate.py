"""Валидация Gap Analysis на тестовом наборе.

Правила из Testing Plan (Confluence):
- релевантная (ba/sa/pm): пройдена, если match_score >= 60
- негативная: пройдена, если match_score < 60
- цель: >= 88.9% (16 из 18)
Весь прогон — одной версией промпта (правило регресса).
"""

import json
import time
from pathlib import Path

from gap_analyzer import analyze
from retriever import KnowledgeBase
from vacancy_loader import load_vacancies

THRESHOLD = 60
TARGET = "16/18 (88.9%)"
REPORTS_DIR = Path(__file__).parent.parent / "reports"


def main():
    kb = KnowledgeBase().build()
    vacs = load_vacancies()
    results = []
    passed = 0

    print(f"\nПрогон {len(vacs)} вакансий. Ожидай ~15 сек на каждую.\n")

    for i, vac in enumerate(vacs, start=1):
        expect_high = vac["type"] in ("ba", "sa", "pm")
        t0 = time.time()
        report = analyze(vac["text"], kb)
        dt = round(time.time() - t0)

        if report.get("_parse_error"):
            ok, score = False, None
        else:
            score = report["match_score"]
            ok = score >= THRESHOLD if expect_high else score < THRESHOLD

        passed += ok
        results.append({
            "file": vac["file"], "type": vac["type"],
            "expected": "высокий" if expect_high else "низкий",
            "score": score, "passed": ok, "seconds": dt,
            "report": report,
        })

        mark = "✅" if ok else "❌"
        print(f"{mark} [{i}/{len(vacs)}] {vac['file']} ({vac['type']}) "
              f"score={score} | {dt} сек")

    accuracy = passed / len(results)

    print("\n" + "=" * 50)
    print(f"ИТОГ: {passed} из {len(results)} = {accuracy:.1%}")
    print(f"Цель Testing Plan: {TARGET}")
    print("РЕЗУЛЬТАТ: ЦЕЛЬ ДОСТИГНУТА 🎉" if passed >= 16
          else "РЕЗУЛЬТАТ: цель не достигнута — правим промпт и перегоняем")

    REPORTS_DIR.mkdir(exist_ok=True)
    out = REPORTS_DIR / "validation_run1.json"
    out.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nПолный отчёт сохранён: {out}")


if __name__ == "__main__":
    main()
