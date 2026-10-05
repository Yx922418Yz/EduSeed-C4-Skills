import json

d = json.load(open(r"C:\Users\lenovo\Doubao\chats\2026-10-05\new-chat\c4-work\c4c\test-output\run3\3_solutions.json", encoding="utf-8"))
for s in d:
    pid = s["problem_id"]
    ok = s["solved"]
    ans = str(s.get("answer", ""))[:120]
    print(f"P{pid}: solved={ok} | {ans}")
