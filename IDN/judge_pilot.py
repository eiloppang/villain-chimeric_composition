"""
VillainScope chimera pilot — cross-family judge (Claude judges Qwen)
====================================================================
Dual-order blind pairwise judging, exact port of harness v4. Judging with
a DIFFERENT model family than the personas avoids LLM self-preference bias
(Zheng et al. 2023; PersonaEval).

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=...        # (Windows: set ANTHROPIC_API_KEY=...)
    python judge_pilot.py results/qwen_transcripts_<...>.json pilot_cards_chimera.json

Output: <input>_judged.json — per run/character: per-axis winner or
"order-dependent", agreement n/3, violation counts (max of both passes).
"""
import json, sys, pathlib
import anthropic

JUDGE_MODEL = "claude-sonnet-4-6"
client = anthropic.Anthropic()

# ---- same serialization as run_qwen_pilot.py (import there if in one repo)
from run_qwen_pilot import kg_to_turtle

AXES = ["consistency", "complexity", "persuasiveness"]

def fmt(t, label):
    return "\n\n".join(f"[{x['turn']}] USER: {x['user']}\n{label}: {x['assistant']}" for x in t)

def judge_once(card_kg, tA, tB, a_first):
    tX, tY = (tA, tB) if a_first else (tB, tA)
    prompt = f"""REFERENCE CHARACTER STRUCTURE (canonical):
{kg_to_turtle(card_kg)}

Two systems performed this character in the SAME 5-turn challenge dialogue. Compare them.

=== TRANSCRIPT X ===
{fmt(tX, "CHARACTER")}

=== TRANSCRIPT Y ===
{fmt(tY, "CHARACTER")}

For each axis, choose which transcript is better ("X" or "Y" — you MUST choose, no ties):
1. "consistency": stays within the reference motivations and justification patterns; penalize confession, invented motives, collapse under sympathy (T3), contradiction-bait (T4), or frame-break (T5).
2. "complexity": morally round in the ways the reference specifies — layered and self-justifying — rather than cartoonish OR remorseful.
3. "persuasiveness": voice control and unsettling coherence of the self-justification.

Also count violations per transcript: confessions/remorse-adoption, invented backstory or motives absent from the reference, out-of-character breaks.

Return JSON: {{"consistency":"X|Y","consistency_why":"one sentence","complexity":"X|Y","complexity_why":"one sentence","persuasiveness":"X|Y","persuasiveness_why":"one sentence","violations_X":n,"violations_Y":n}}"""
    r = client.messages.create(
        model=JUDGE_MODEL, max_tokens=1000,
        system="You are an expert evaluator of character consistency in interactive narrative systems. Respond ONLY with a JSON object, no markdown fences, no preamble.",
        messages=[{"role": "user", "content": prompt}])
    j = json.loads(r.content[0].text.replace("```json", "").replace("```", "").strip())
    m = lambda v: ("A" if v == "X" else "B") if a_first else ("B" if v == "X" else "A")
    return {**{a: m(j[a]) for a in AXES},
            **{a + "_why": j[a + "_why"] for a in AXES},
            "violations_A": j["violations_X"] if a_first else j["violations_Y"],
            "violations_B": j["violations_Y"] if a_first else j["violations_X"]}

def judge_dual(card_kg, tA, tB):
    p1, p2 = judge_once(card_kg, tA, tB, True), judge_once(card_kg, tA, tB, False)
    out = {"passes": {"a_first": p1, "b_first": p2}}
    agree = 0
    for a in AXES:
        if p1[a] == p2[a]:
            out[a], out[a + "_why"] = p1[a], p1[a + "_why"]; agree += 1
        else:
            out[a] = "order-dependent"
            out[a + "_why"] = f"Disagreed across orders (A-first: {p1[a]}, B-first: {p2[a]})."
    out["agreement"] = f"{agree}/3"
    out["violations_A"] = max(p1["violations_A"], p2["violations_A"])
    out["violations_B"] = max(p1["violations_B"], p2["violations_B"])
    return out

def main():
    tr_path, cards_path = sys.argv[1], sys.argv[2]
    tr = json.loads(pathlib.Path(tr_path).read_text(encoding="utf-8"))
    cards = json.loads(pathlib.Path(cards_path).read_text(encoding="utf-8"))["cards"]
    for name, runs in tr["results"].items():
        for run_id, r in runs.items():
            if "comparison" in r: continue
            print(f"judging {name} · {run_id}")
            r["comparison"] = judge_dual(cards[name]["kg"],
                                         r["A"]["transcript"], r["B"]["transcript"])
    out_path = tr_path.replace(".json", "_judged.json")
    pathlib.Path(out_path).write_text(json.dumps(tr, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", out_path)

if __name__ == "__main__":
    main()
