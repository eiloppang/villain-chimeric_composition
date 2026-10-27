"""Write the answer key before any model is called (see PREREGISTRATION.md §4)."""
import json
import pathlib
import time

REID = pathlib.Path(__file__).resolve().parent
ROOT = REID.parent
CARDS = json.loads((ROOT / "IDN" / "cards_chimera_10.json").read_text(encoding="utf-8"))

# source villain -> accepted names (aliases) and works (original / translated titles)
SOURCES = {
    "Iago": {
        "names": ["Iago", "lago"],
        "works": ["Othello", "오셀로"],
    },
    "Captain Vidal": {
        "names": ["Captain Vidal", "Capitán Vidal", "Capitan Vidal", "Vidal"],
        "works": ["Pan's Labyrinth", "Pans Labyrinth", "El laberinto del fauno",
                  "판의 미로"],
    },
    "Christof": {
        "names": ["Christof"],
        "works": ["The Truman Show", "Truman Show", "트루먼 쇼"],
    },
    "Child Catcher": {
        "names": ["Child Catcher", "Childcatcher", "Child-Catcher"],
        "works": ["Chitty Chitty Bang Bang", "치티치티 뱅뱅"],
    },
    "Erfinder C.A. Rotwang": {
        "names": ["Rotwang", "C.A. Rotwang", "Erfinder Rotwang"],
        "works": ["Metropolis", "메트로폴리스"],
    },
    "Jason Dixon": {
        "names": ["Jason Dixon", "Dixon"],
        "works": ["Three Billboards Outside Ebbing, Missouri", "Three Billboards",
                  "쓰리 빌보드"],
    },
    "Dudley Liam Smith": {
        "names": ["Dudley Liam Smith", "Dudley Smith", "Dudley"],
        "works": ["L.A. Confidential", "LA Confidential", "LA 컨피덴셜"],
    },
    "El Indio": {
        "names": ["El Indio", "Indio"],
        "works": ["For a Few Dollars More", "Per qualche dollaro in più",
                  "석양의 건맨"],
    },
    "Little Bill Daggett": {
        "names": ["Little Bill Daggett", "Little Bill", "Daggett"],
        "works": ["Unforgiven", "용서받지 못한 자"],
    },
    "Dmitri": {
        "names": ["Dmitri", "Dmitri Desgoffe-und-Taxis", "Desgoffe"],
        "works": ["The Grand Budapest Hotel", "Grand Budapest", "그랜드 부다페스트 호텔"],
    },
    "Randall Boggs": {
        "names": ["Randall Boggs", "Randall"],
        "works": ["Monsters, Inc.", "Monsters Inc", "몬스터 주식회사"],
    },
    "Romano": {
        "names": ["Romano"],
        "works": ["The Secret in Their Eyes", "El secreto de sus ojos",
                  "비밀의 눈동자"],
    },
    "Rory Breaker": {
        "names": ["Rory Breaker", "Rory"],
        "works": ["Lock, Stock and Two Smoking Barrels", "Lock Stock",
                  "록 스탁 앤 투 스모킹 배럴즈"],
    },
}

# tokens that collide with ordinary words or need a corroborating work title;
# a match on these alone is routed to ambiguous.csv for human adjudication
RISKY = ["Vidal", "Indio", "Dixon", "Dudley", "Dmitri", "Romano", "Rory", "Randall",
         "Daggett", "Desgoffe", "lago", "Metropolis", "Unforgiven", "Grand Budapest",
         "Lock Stock", "Three Billboards"]

key = {"generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
       "note": "실행 전 확정. 키메라는 출처 세 명 모두가 정답이다.",
       "risky_tokens": RISKY, "sources": SOURCES, "cards": {}}

for name, card in CARDS["cards"].items():
    srcs = sorted(set(card["provenance"]["motivations"]
                      + card["provenance"]["justifications"]))
    key["cards"]["chimera::" + name] = {
        "group": "chimera", "sources": srcs,
        "names": [n for s in srcs for n in SOURCES[s]["names"]],
        "works": [w for s in srcs for w in SOURCES[s]["works"]],
    }
for s in SOURCES:
    key["cards"]["control::" + s] = {
        "group": "control", "sources": [s],
        "names": SOURCES[s]["names"], "works": SOURCES[s]["works"],
    }

(REID / "answer_key.json").write_text(json.dumps(key, ensure_ascii=False, indent=2),
                                      encoding="utf-8")
print("wrote reid/answer_key.json ·", len(key["cards"]), "cards")
for k, v in key["cards"].items():
    print("  %-34s %s" % (k, ", ".join(v["sources"])))
