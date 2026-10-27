"""Score the re-identification runs against the preregistered answer key.

Rules come from reid/PREREGISTRATION.md §5 and are not changed here:
a response counts as a re-identification if it contains any accepted character name
or work title for that card. Matches that rest only on tokens flagged `risky`, and
Q1 responses that disclaim recognition while still naming something, are not decided
automatically — they go to ambiguous.csv for a human.
"""
import csv
import json
import pathlib
import re
import collections

REID = pathlib.Path(__file__).resolve().parent
RAW = REID / "raw"
KEY = json.loads((REID / "answer_key.json").read_text(encoding="utf-8"))
CARDS = json.loads((REID / "cards_reid.json").read_text(encoding="utf-8"))["cards"]
RISKY = {t.lower() for t in KEY["risky_tokens"]}

DISCLAIM = re.compile(
    r"\b(do not recognis|don't recognis|do not recognize|don't recognize|"
    r"not recognise|not recognize|i do not know|i don't know|unfamiliar|"
    r"cannot identify|can't identify|no specific|not from an existing|"
    r"does not appear to be from|not based on)", re.I)
ITEM = re.compile(r"(?m)^\s*(?:\d+[.)]|[-*•])\s+")


def find(token, text):
    """Word-boundary match for ASCII tokens, substring for non-ASCII (Hangul etc.)."""
    if not token:
        return False
    if all(ord(ch) < 128 for ch in token):
        pat = r"(?<![A-Za-z0-9])%s(?![A-Za-z0-9])" % re.escape(token)
        return re.search(pat, text, re.I) is not None
    return token in text


def matches(card_key, text):
    names = [n for n in card_key["names"] if find(n, text)]
    works = [w for w in card_key["works"] if find(w, text)]
    return names, works


def first_item(text):
    """The first candidate in a listed answer, for Q2 top-1 scoring."""
    parts = ITEM.split(text)
    if len(parts) >= 3:
        return parts[1]
    # not a list: fall back to the first sentence block
    return text.split("\n\n")[0][:400]


# "정답 목록과 부분적으로만 겹치는 응답"(PREREGISTRATION §5)을 문자 그대로 구현한다:
# 정답 항목이 여러 낱말일 때, 변별력 있는 낱말만 맞고 항목 전체는 맞지 않은 경우.
COMMON = {"the", "and", "of", "a", "in", "for", "two", "more", "their", "show",
          "hotel", "eyes", "secret", "little", "captain", "child", "city", "dollars",
          "outside", "smoking", "barrels", "stock", "lock", "inc", "monsters"}


def partial_overlap(card_key, text, prompt=""):
    """A token the model was handed carries no evidence that it recognised anything.

    The Q2 wording ("list the three most likely...") put `three` in every response and
    so matched `Three Billboards` on every card; the same holds for any word the card
    itself supplied. Tokens present in the prompt are therefore not counted.
    """
    out = []
    for entry in card_key["names"] + card_key["works"]:
        toks = [w for w in re.split(r"[^A-Za-z]+", entry) if len(w) >= 5]
        toks = [w for w in toks
                if w.lower() not in COMMON and not find(w, prompt)]
        if not toks or find(entry, text):
            continue
        for w in toks:
            if find(w, text):
                out.append("%s (%s)" % (w, entry))
    return sorted(set(out))


rows, ambiguous = [], []
for path in sorted(RAW.glob("*.jsonl")):
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        cid = r["card_id"]
        k = KEY["cards"][cid]
        text = r.get("response", "")
        if "error" in r:
            rows.append({"card": cid, "group": r["group"], "model": r["model_label"],
                         "question": r["question"], "sample": r["sample"],
                         "response_summary": "[ERROR] " + r["error"][:120],
                         "reidentified": "error", "matched": "", "top1": "",
                         "needs_review": "no"})
            continue
        names, works = matches(k, text)
        hit = names + works
        only_risky = bool(hit) and all(h.lower() in RISKY for h in hit)
        disclaims = bool(DISCLAIM.search(text)) and r["question"] == "q1"

        review = ""
        if hit and only_risky:
            review = "위험 토큰 단독 일치"
        elif hit and disclaims:
            review = "비인식 표현과 후보 동시 제시"
        elif not hit:
            partial = partial_overlap(k, text, r.get("prompt", ""))
            if partial:
                review = "정답 항목의 일부만 일치: " + ", ".join(partial)

        top1 = ""
        if r["question"] == "q2" and hit:
            n1, w1 = matches(k, first_item(text))
            top1 = "yes" if (n1 or w1) else "no"

        rec = {"card": cid, "group": r["group"], "model": r["model_label"],
               "question": r["question"], "sample": r["sample"],
               "response_summary": re.sub(r"\s+", " ", text)[:200],
               "reidentified": ("review" if review else ("yes" if hit else "no")),
               "matched": "; ".join(hit), "top1": top1,
               "needs_review": "yes" if review else "no"}
        rows.append(rec)
        if review:
            ambiguous.append({**rec, "reason": review,
                              "response_full": re.sub(r"\s+", " ", text)[:1500]})

with (REID / "results.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

if ambiguous:
    with (REID / "ambiguous.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(ambiguous[0].keys()))
        w.writeheader()
        w.writerows(ambiguous)

# ---------------------------------------------------------------- summary
def rate(sel):
    yes = sum(1 for r in sel if r["reidentified"] == "yes")
    rev = sum(1 for r in sel if r["reidentified"] == "review")
    return yes, rev, len(sel)

L = []
W = L.append
W("# 재식별 검사 결과\n")
W("판정 기준은 `PREREGISTRATION.md` §5 그대로다. `review`는 자동 판정하지 않고 "
  "`ambiguous.csv`로 보낸 응답이며, 아래 비율에서는 재식별로 세지 않았다.\n")
models = sorted({r["model"] for r in rows})
W("\n## 1. 모델 × 군 × 질문별 재식별 비율\n")
W("| 모델 | 군 | 질문 | 재식별 | 검토 필요 | 전체 | 비율 |")
W("| --- | --- | --- | --- | --- | --- | --- |")
for m in models:
    for g in ("control", "chimera"):
        for q in ("q1", "q2"):
            sel = [r for r in rows if r["model"] == m and r["group"] == g
                   and r["question"] == q]
            if not sel:
                continue
            y, rv, n = rate(sel)
            W("| %s | %s | %s | %d | %d | %d | %.0f%% |"
              % (m, g, q, y, rv, n, 100 * y / n if n else 0))

W("\n## 2. 카드 단위 — Q1\n")
W("5회 중 재식별 횟수. `한 번이라도`는 5회 중 1회 이상 재식별된 경우다.\n")
W("| 카드 | 군 | " + " | ".join(models) + " | 한 번이라도 |")
W("| --- | --- | " + " | ".join("---" for _ in models) + " | --- |")
for cid in CARDS:
    cells, any_hit = [], False
    for m in models:
        sel = [r for r in rows if r["card"] == cid and r["model"] == m
               and r["question"] == "q1"]
        y, rv, n = rate(sel)
        any_hit = any_hit or y > 0
        cells.append("%d/%d%s" % (y, n, " (검토 %d)" % rv if rv else ""))
    W("| %s | %s | %s | %s |" % (cid, CARDS[cid]["group"], " | ".join(cells),
                                 "**예**" if any_hit else "아니오"))

W("\n## 3. 카드 단위 — Q2 (강제 추측)\n")
W("`1순위`는 응답에서 가장 먼저 제시된 후보가 정답인 경우다.\n")
W("| 카드 | 군 | " + " | ".join("%s 재식별 / 1순위" % m for m in models) + " |")
W("| --- | --- | " + " | ".join("---" for _ in models) + " |")
for cid in CARDS:
    cells = []
    for m in models:
        sel = [r for r in rows if r["card"] == cid and r["model"] == m
               and r["question"] == "q2"]
        y, rv, n = rate(sel)
        t1 = sum(1 for r in sel if r["top1"] == "yes")
        cells.append("%d/%d / %d" % (y, n, t1))
    W("| %s | %s | %s |" % (cid, CARDS[cid]["group"], " | ".join(cells)))

W("\n## 4. 키메라가 재식별된 경우\n")
hits = [r for r in rows if r["group"] == "chimera" and r["reidentified"] == "yes"]
if hits:
    W("| 카드 | 모델 | 질문 | 샘플 | 맞힌 이름·작품 |")
    W("| --- | --- | --- | --- | --- |")
    for r in hits:
        W("| %s | %s | %s | %d | %s |"
          % (r["card"], r["model"], r["question"], r["sample"], r["matched"]))
else:
    W("없음.")

W("\n## 5. 카드 구성 (대조군 개수 부족 기록)\n")
W("| 카드 | 군 | 동기 | 정당화 | 어휘 점검 |")
W("| --- | --- | --- | --- | --- |")
for cid, c in CARDS.items():
    W("| %s | %s | %d | %d | %s |"
      % (cid, c["group"], c["n_motivations"], c["n_justifications"],
         "통과" if c["leak_check"]["passed"] else "실패"))

W("\n## 6. 검토 필요 응답\n")
W("자동 판정하지 않은 응답 **%d건**. 사유별 분포: %s. 전체는 `ambiguous.csv`."
  % (len(ambiguous),
     ", ".join("%s %d" % (k, v) for k, v in
               collections.Counter(a["reason"] for a in ambiguous).items()) or "없음"))

(REID / "summary.md").write_text("\n".join(L), encoding="utf-8")
print("rows:", len(rows), "| ambiguous:", len(ambiguous))
print("wrote results.csv, summary.md" + (", ambiguous.csv" if ambiguous else ""))
