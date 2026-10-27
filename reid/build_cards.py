"""Build the 23 re-identification cards: 10 chimeras + 13 single-source controls.

Controls are assembled from the same VillainScope description segments the chimeras
drew on, rendered through the same prose template, with the same anonymisation rules
(works, characters, places, real people, signature props removed or generalised).
Every edit is recorded so the two groups can be shown to differ in one respect only:
a blend of three villains versus one.
"""
import json
import pathlib
import re
import time

REID = pathlib.Path(__file__).resolve().parent
ROOT = REID.parent
CARDS = json.loads((ROOT / "IDN" / "cards_chimera_10.json").read_text(encoding="utf-8"))
SRC = json.loads((REID / "_sources_raw.json").read_text(encoding="utf-8"))

# data label -> answer-key name
SRC_KEY = {"lago": "Iago", "Vidal": "Captain Vidal", "Christof": "Christof",
           "Child Catcher": "Child Catcher", "Erfinder C.A. Rotwang": "Erfinder C.A. Rotwang",
           "Jason Dixon": "Jason Dixon", "Dudley Liam Smith": "Dudley Liam Smith",
           "El Indio": "El Indio", "Little Bill Daggett": "Little Bill Daggett",
           "Dmitri": "Dmitri", "Randall Boggs": "Randall Boggs", "Romano": "Romano",
           "Rory Breaker": "Rory Breaker"}

# name and setting are authored in the chimeras' own style: a role noun, and one clause
# that adds no work-specific information beyond what the segments already carry.
PROFILE = {
    "lago": ("The Advisor", "advisor",
             "a household where every confidence passes through one trusted ear"),
    "Vidal": ("The Officer", "officer",
              "a garrison holding a countryside under curfew"),
    "Christof": ("The Director", "director",
                 "a fabricated world broadcast without its inhabitant's knowledge"),
    "Child Catcher": ("The Enforcer", "enforcer",
                      "a regime whose laws are enforced against its children"),
    "Erfinder C.A. Rotwang": ("The Inventor", "inventor",
                              "a workshop where a lost woman is being rebuilt"),
    "Jason Dixon": ("The Patrolman", "police officer",
                    "a small-town force answerable to no one outside it"),
    "Dudley Liam Smith": ("The Captain", "police captain",
                          "a force that runs the underworld it polices"),
    "El Indio": ("The Leader", "leader of an outlaw band",
                 "a band that moves between towns it has already robbed"),
    "Little Bill Daggett": ("The Sheriff", "sheriff",
                            "a frontier town where the law is one man's temper"),
    "Dmitri": ("The Owner", "owner",
               "a family estate contested after a death"),
    "Randall Boggs": ("The Student", "student",
                      "a corporation that harvests terror from children"),
    "Romano": ("The Judicial Officer", "judicial officer",
               "a court that serves whichever power holds the day"),
    "Rory Breaker": ("The Crime Lord", "crime lord",
                     "a city enterprise run on reputation and fear"),
}

# anonymisation: (source, literal old text, replacement, what was removed)
EDITS = [
    ("lago",
     "Tragedian in real life - William Hazlitt: Practicing tragedy in reality with originality.",
     "Tragedian in real life: Practicing tragedy in reality with originality.",
     "실존 비평가 이름(William Hazlitt) 삭제"),
    ("Vidal",
     "the preservation of lineage through a symbolic pocket watch",
     "the preservation of lineage through an heirloom",
     "특징적 소품(회중시계) 일반화 — 키메라 카드와 동일한 처리"),
    ("Child Catcher",
     "the promise of free sweets (lollipops, treacle tart)",
     "the promise of free sweets",
     "특징적 소품(막대사탕, 트리클 타르트) 삭제"),
    ("Child Catcher",
     "not just as a job for the Baroness, but as a deeply gratifying personal sport",
     "not just as a job for his employer, but as a deeply gratifying personal sport",
     "등장인물명(the Baroness) 일반화"),
    ("Child Catcher",
     "the official enforcement arm of the Vulgarian regime's anti-child laws",
     "the official enforcement arm of the regime's anti-child laws",
     "지명(Vulgarian) 삭제"),
    ("El Indio",
     "choreographed ritual by using a musical pocket watch as a countdown",
     "choreographed ritual by using a countdown",
     "특징적 소품(음악 회중시계) 삭제"),
    ("Little Bill Daggett",
     "the obsessive yet failed construction of a personal domain, exemplified by a leaking house",
     "the obsessive yet failed construction of a personal domain",
     "특징적 소품(새는 집) 삭제"),
    ("Dmitri",
     "over subordinates, notably the assassin J.G. Jopling, to execute",
     "over subordinates, notably a hired assassin, to execute",
     "등장인물명(J.G. Jopling) 일반화"),
    ("Randall Boggs",
     "the psychological terror of victims during the forced extraction of screams",
     "the psychological terror of victims during the forced extraction of terror",
     "작품 고유 설정(비명 채취) 일반화"),
]

# the same 45-token leak list the chimera cards were checked against
LEAK_TOKENS = [
    "Christof", "Vidal", "Iago", "lago", "Child Catcher", "Rotwang", "Erfinder",
    "Jason Dixon", "Dudley", "El Indio", "Little Bill", "Daggett", "Dmitri",
    "Randall", "Boggs", "Romano", "Rory", "Breaker", "Truman", "Othello",
    "Pan's Labyrinth", "Labyrinth", "Chitty", "Metropolis", "Three Billboards",
    "Ebbing", "Confidential", "Dollars", "Unforgiven", "Budapest", "Monsters",
    "Secret in Their Eyes", "Lock, Stock", "Basterds", "Narnia", "Beethoven",
    "Singin", "pocket watch", "Vulgarian", "Baroness", "treacle", "lollipop",
    "Jopling", "screams", "Hazlitt",
]


def camel(label):
    return "".join(w.capitalize() for w in re.sub(r"[^A-Za-z ]", " ", label).split())


def anonymise(src, text):
    applied = []
    for s, old, new, why in EDITS:
        if s == src and old in text:
            text = text.replace(old, new)
            applied.append(why)
    return text, applied


def prose(name, occupation, setting, motivations, justifications, traits):
    """The experiment's prose template, unchanged."""
    mot = "; ".join("%s (%s)" % (c, b) for c, b in motivations)
    jus = " ".join("%s: %s" % (p, l) for p, l in justifications)
    return ("You are %s, %s — %s. Your motivations: %s. "
            "When your actions are questioned, you justify them as follows: %s "
            "Your personality traits: %s."
            % (name, occupation, setting, mot, jus, ", ".join(traits)))


out = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "template": "CHARACTER DESCRIPTION:\\nYou are known as {name}, a {occupation}. {description}",
       "note": "결속 지침·공통 규칙·안전 규칙은 포함하지 않는다.",
       "cards": {}}

# ---- experimental group: the chimeras, prose exactly as the experiment injects it
for name, card in CARDS["cards"].items():
    out["cards"]["chimera::" + name] = {
        "group": "chimera", "name": card["prose"]["name"],
        "occupation": card["prose"]["occupation"],
        "description": card["prose"]["description"],
        "n_motivations": len(card["kg"]["motivations"]),
        "n_justifications": len(card["kg"]["justification_patterns"]),
        "sources": sorted(set(card["provenance"]["motivations"]
                              + card["provenance"]["justifications"])),
        "anonymization": ["본 실험 카드 그대로 사용 (추가 편집 없음)"],
    }

# ---- control group: one card per source villain
for src, rec in SRC.items():
    nm, occ, setting = PROFILE[src]
    segs, applied = [], []
    for s in rec["segs"]:
        t, ap = anonymise(src, s)
        segs.append(t)
        applied += ap
    pairs = [(camel(s.split(":", 1)[0]), s.split(":", 1)[1].strip().rstrip(".") + ".")
             for s in segs]
    motivations = pairs[:3]
    justifications = pairs[3:6]
    # a trait label can itself name a character ("Even attempts to kill Truman"),
    # so the leak list filters traits before they reach the card
    dropped = [t for t in rec["traits"]
               if any(tok.lower() in t.lower() for tok in LEAK_TOKENS)]
    traits = [t for t in rec["traits"] if t not in dropped][:6]
    if dropped:
        applied.append("트레잇에서 고유명사 포함 항목 제외: " + ", ".join(dropped))
    desc = prose(nm, occ, setting, motivations, justifications, traits)
    out["cards"]["control::" + SRC_KEY[src]] = {
        "group": "control", "name": nm, "occupation": occ, "setting": setting,
        "description": desc,
        "n_motivations": len(motivations), "n_justifications": len(justifications),
        "n_segments_available": len(segs),
        "shortfall": max(0, 3 - len(motivations)) + max(0, 3 - len(justifications)),
        "sources": [SRC_KEY[src]],
        "anonymization": sorted(set(applied)) or ["편집 불필요 (고유명사·소품 없음)"],
    }

# ---- leak check, identical for both groups
report = []
for cid, c in out["cards"].items():
    blob = "%s %s %s" % (c["name"], c["occupation"], c["description"])
    hits = [t for t in LEAK_TOKENS if t.lower() in blob.lower()]
    c["leak_check"] = {"tokens_checked": len(LEAK_TOKENS), "hits": hits,
                       "passed": not hits}
    report.append((cid, c["group"], hits))

(REID / "cards_reid.json").write_text(json.dumps(out, ensure_ascii=False, indent=2),
                                      encoding="utf-8")

print("wrote reid/cards_reid.json ·", len(out["cards"]), "cards")
print()
print("%-34s %-8s %-6s %-6s %s" % ("카드", "군", "동기", "정당화", "누출"))
for cid, c in out["cards"].items():
    print("%-34s %-8s %-6d %-6d %s"
          % (cid, c["group"], c["n_motivations"], c["n_justifications"],
             "통과" if c["leak_check"]["passed"] else "실패 " + ",".join(c["leak_check"]["hits"])))
short = [(k, v["shortfall"], v["n_segments_available"])
         for k, v in out["cards"].items() if v.get("shortfall")]
print()
print("6개를 못 채운 대조군:", len(short))
for k, s, n in short:
    print("  %-34s 부족 %d (세그먼트 %d개)" % (k, s, n))
fails = [c for c, g, h in report if h]
print()
print("누출 점검 실패:", fails if fails else "없음")
