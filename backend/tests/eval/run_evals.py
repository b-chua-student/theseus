import json
import re
from pathlib import Path

from api.app import create_app

CASES_PATH = Path(__file__).parent / "cases.json"

app = create_app()
get_all = app.extensions["get_all_manuscripts_service"]
index_service = app.extensions["index_manuscript_service"]
ask_service = app.extensions["ask_question_service"]

manuscript = get_all.execute()[0]
print(f"manuscript: {manuscript.title} ({manuscript.id})")
index_service.execute(manuscript.id)

cases = json.loads(CASES_PATH.read_text())
passed = 0

for case in cases:
    try:
        exchange = ask_service.execute(manuscript.id, case["question"])
    except Exception as exc:
        print("ERROR", case["question"], "->", exc)
        continue

    answer = exchange.answer
    text = answer.content.lower() if answer else ""

    ok = all(word.lower() in text for word in case["must_contain"])
    if case["must_cite"]:
        ok = ok and bool(re.search(r"\[\d+\]", text))

    passed += ok
    print("PASS" if ok else "FAIL", case["question"])
    if not ok:
        print("   answer:", text[:200])

print(f"{passed}/{len(cases)} passed")
