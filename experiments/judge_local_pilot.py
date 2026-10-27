"""
VillainScope chimera pilot — cross-family judge (Claude judges the local model)
==============================================================================
Dual-order blind pairwise judging, exact port of harness v4. Judging with
a DIFFERENT model family than the personas avoids LLM self-preference bias
(Zheng et al. 2023; PersonaEval). Never judge Qwen output with Qwen.

Setup:
    pip install anthropic
    export ANTHROPIC_API_KEY=...        # (Windows: set ANTHROPIC_API_KEY=...)
    python experiments/judge_local_pilot.py experiments/results/local_<...>.json pilot_cards_chimera.json

Output: <input>_judged.json — per run/character: per-axis winner or
"order-dependent", agreement n/3, violation counts (max of both passes).
"""
import argparse, json, os, sys, pathlib
import anthropic

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

JUDGE_MODEL = "claude-sonnet-4-6"

def load_api_key():
    """Env var wins; otherwise read a gitignored local env file.

    Accepts either `ANTHROPIC_API_KEY=sk-ant-...` or a file holding just the key.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "environment"
    here = pathlib.Path(__file__).resolve().parent
    for path in (here / "env.env", here / ".env", here.parent / ".env"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                if k.strip() == "ANTHROPIC_API_KEY":
                    os.environ["ANTHROPIC_API_KEY"] = v.strip().strip('"').strip("'")
                    return str(path)
            elif line.startswith("sk-ant-"):          # bare key, no assignment
                os.environ["ANTHROPIC_API_KEY"] = line
                return str(path)
    raise SystemExit(
        "ANTHROPIC_API_KEY not found. Set the env var, or put the key in "
        "experiments/env.env (already gitignored).")

print("api key from:", load_api_key())
client = anthropic.Anthropic()

# ---- same serialization as run_local_pilot.py
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run_local_pilot import kg_to_turtle, resolve_cards

AXES = ["consistency", "complexity", "persuasiveness"]

def fmt(t, label):
    return "\n\n".join(f"[{x['turn']}] USER: {x['user']}\n{label}: {x['assistant']}" for x in t)

def judge_once(card_kg, tA, tB, a_first, lo="A", hi="B"):
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
    m = lambda v: (lo if v == "X" else hi) if a_first else (hi if v == "X" else lo)
    return {**{a: m(j[a]) for a in AXES},
            **{a + "_why": j[a + "_why"] for a in AXES},
            "violations_" + lo: j["violations_X"] if a_first else j["violations_Y"],
            "violations_" + hi: j["violations_Y"] if a_first else j["violations_X"]}

def judge_dual(card_kg, tA, tB, lo="A", hi="B"):
    p1 = judge_once(card_kg, tA, tB, True, lo, hi)
    p2 = judge_once(card_kg, tA, tB, False, lo, hi)
    out = {"passes": {f"{lo}_first": p1, f"{hi}_first": p2}}
    agree = 0
    for a in AXES:
        if p1[a] == p2[a]:
            out[a], out[a + "_why"] = p1[a], p1[a + "_why"]; agree += 1
        else:
            out[a] = "order-dependent"
            out[a + "_why"] = f"Disagreed across orders ({lo}-first: {p1[a]}, {hi}-first: {p2[a]})."
    out["agreement"] = f"{agree}/3"
    for k in (lo, hi):
        out["violations_" + k] = max(p1["violations_" + k], p2["violations_" + k])
    return out

def judgeable(entry, conds):
    """Both conditions present and every turn answered — otherwise fmt() would KeyError."""
    for cond in conds:
        t = entry.get(cond, {}).get("transcript")
        if not t or any("assistant" not in x for x in t):
            return False
    return True

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcripts", help="a results JSON written by run_local_pilot.py")
    ap.add_argument("cards", nargs="?", default="pilot_cards_chimera.json")
    ap.add_argument("--pair", default="A:B", metavar="X:Y",
                    help="which two conditions to compare, e.g. A:C (default A:B)")
    args = ap.parse_args()

    lo, hi = args.pair.split(":")
    key = "comparison" if (lo, hi) == ("A", "B") else f"comparison_{lo}_vs_{hi}"

    tr = json.loads(pathlib.Path(args.transcripts).read_text(encoding="utf-8"))
    if tr.get("meta", {}).get("dry_run"):
        raise SystemExit("refusing to judge a --dry-run transcript (stub replies, not model output)")
    cards = json.loads(resolve_cards(args.cards).read_text(encoding="utf-8"))["cards"]

    for name, runs in tr["results"].items():
        for run_id, r in runs.items():
            if key in r: continue
            if not judgeable(r, (lo, hi)):
                print(f"skipping {name} · {run_id} (missing condition {lo}/{hi} or errored turn)")
                continue
            print(f"judging {name} · {run_id}  [{lo} vs {hi}]")
            r[key] = judge_dual(cards[name]["kg"], r[lo]["transcript"], r[hi]["transcript"],
                                lo, hi)
    out_path = args.transcripts.replace(".json", "_judged.json")
    if args.transcripts.endswith("_judged.json"):
        out_path = args.transcripts          # add a pair to an already-judged file in place
    pathlib.Path(out_path).write_text(json.dumps(tr, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", out_path)

if __name__ == "__main__":
    main()
