"""
VillainScope full-paper judge — dual-order blind pairwise comparison.

Primary judge   GPT-5.6 Terra      (reasoning_effort "medium")
Secondary judge claude-sonnet-4-6  (optional cross-check, --cross-check > 0)

The judge prompt is an exact port of IDN/judge_pilot.py. Only the transport layer
differs between judges — the prompt never branches, or the two judges stop being
comparable.

Never judge with the subject model (self-preference bias). The runner records the
subject model in meta; this script refuses a judge from the same family.

Robustness: every judge call is retried with exponential backoff on transient
failures, the results file is written after every judged pair, and a pair that still
fails is left unjudged (never written as a fake verdict) so a re-run picks it up.
The process exits non-zero if any pair failed, so a chained command can tell.

Setup:
    pip install requests anthropic
    # experiments/env.env holds GPT_KEY / CLAUDE_KEY (gitignored)
    python experiments/judge.py experiments/pilot_gemini_20260914/google_abc.json --pair A:C --cross-check 0

Output: <input>_judged.json
"""
import argparse
import json
import os
import pathlib
import sys
import time

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prompts import kg_to_turtle  # noqa: E402  (shared serialization — never re-implement)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HERE = pathlib.Path(__file__).resolve().parent
AXES = ["consistency", "complexity", "persuasiveness"]

PRIMARY = {"judge": "gpt", "model": "gpt-5.6-terra", "reasoning_effort": "medium"}
SECONDARY = {"judge": "anthropic", "model": "claude-sonnet-4-6", "max_tokens": 1000}

# a judge may not grade output from its own family
FAMILY = {"gpt": ("gpt", "openai"), "anthropic": ("claude", "anthropic", "sonnet")}

JUDGE_SYSTEM = ("You are an expert evaluator of character consistency in interactive "
                "narrative systems. Respond ONLY with a JSON object, no markdown "
                "fences, no preamble.")

MAX_ATTEMPTS = 4
BACKOFF_BASE = 3                    # 3s, 9s, 27s
RETRY_STATUS = {408, 429, 500, 502, 503, 504}


def load_key(names):
    for v in names:
        if os.environ.get(v):
            return os.environ[v]
    path = HERE / "env.env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, val = line.split("=", 1)
            val = val.strip().strip('"').strip("'")
            if k.strip() in names and val:
                return val
    raise SystemExit(f"no key found for {names}; set the env var or add it to {path}")


# ---------------------------------------------------------------- transports
def call_gpt(system, prompt, cfg):
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": "Bearer " + load_key(["GPT_KEY", "OPENAI_API_KEY"]),
                 "Content-Type": "application/json"},
        # this model accepts only the default temperature, and requires
        # max_completion_tokens rather than max_tokens
        json={"model": cfg["model"],
              "reasoning_effort": cfg["reasoning_effort"],
              "max_completion_tokens": 4000,
              "messages": [{"role": "system", "content": system},
                           {"role": "user", "content": prompt}]},
        timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def call_anthropic(system, prompt, cfg):
    import anthropic
    client = anthropic.Anthropic(api_key=load_key(["CLAUDE_KEY", "ANTHROPIC_API_KEY"]))
    r = client.messages.create(model=cfg["model"], max_tokens=cfg["max_tokens"],
                               system=system,
                               messages=[{"role": "user", "content": prompt}])
    return r.content[0].text


TRANSPORT = {"gpt": call_gpt, "anthropic": call_anthropic}


def is_transient(exc):
    """Network trouble, rate limits and server errors are worth retrying; bad requests are not."""
    if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
        return True
    if isinstance(exc, requests.exceptions.HTTPError):
        return exc.response is not None and exc.response.status_code in RETRY_STATUS
    # anthropic SDK, checked by name so the import stays lazy
    return type(exc).__name__ in {"APIConnectionError", "APITimeoutError",
                                  "RateLimitError", "InternalServerError"}


# ---------------------------------------------------------------- judging
def fmt(t, label):
    return "\n\n".join(f"[{x['turn']}] USER: {x['user']}\n{label}: {x['assistant']}" for x in t)


def judge_once(card_kg, tA, tB, a_first, cfg, lo="A", hi="B"):
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
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            raw = TRANSPORT[cfg["judge"]](JUDGE_SYSTEM, prompt, cfg)
            j = json.loads(raw.replace("```json", "").replace("```", "").strip())
            m = lambda v: (lo if v == "X" else hi) if a_first else (hi if v == "X" else lo)
            return {**{a: m(j[a]) for a in AXES},
                    **{a + "_why": j[a + "_why"] for a in AXES},
                    "violations_" + lo: j["violations_X"] if a_first else j["violations_Y"],
                    "violations_" + hi: j["violations_Y"] if a_first else j["violations_X"]}
        except (json.JSONDecodeError, KeyError) as e:
            # a malformed verdict is a fresh sample away from a usable one
            last = f"unparseable verdict ({type(e).__name__}: {e})"
        except Exception as e:
            if not is_transient(e):
                raise
            last = f"{type(e).__name__}: {str(e)[:160]}"
        if attempt < MAX_ATTEMPTS:
            wait = BACKOFF_BASE ** attempt
            print(f"      ! attempt {attempt}/{MAX_ATTEMPTS} failed ({last}); retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"judge call failed after {MAX_ATTEMPTS} attempts — {last}")


def judge_dual(card_kg, tA, tB, cfg, lo="A", hi="B"):
    p1 = judge_once(card_kg, tA, tB, True, cfg, lo, hi)
    p2 = judge_once(card_kg, tA, tB, False, cfg, lo, hi)
    out = {"judge": cfg["judge"], "judge_model": cfg["model"],
           "judge_params": {k: v for k, v in cfg.items() if k not in ("judge", "model")},
           "passes": {f"{lo}_first": p1, f"{hi}_first": p2}}
    agree = 0
    for a in AXES:
        if p1[a] == p2[a]:
            out[a], out[a + "_why"] = p1[a], p1[a + "_why"]
            agree += 1
        else:
            out[a] = "order-dependent"
            out[a + "_why"] = f"Disagreed across orders ({lo}-first: {p1[a]}, {hi}-first: {p2[a]})."
    out["agreement"] = f"{agree}/3"
    for k in (lo, hi):
        out["violations_" + k] = max(p1["violations_" + k], p2["violations_" + k])
    return out


def judgeable(entry, conds):
    for c in conds:
        t = entry.get(c, {}).get("transcript")
        if not t or any("assistant" not in x for x in t):
            return False
    return True


def guard_self_preference(subject_model, cfg):
    s = (subject_model or "").lower()
    if any(tag in s for tag in FAMILY[cfg["judge"]]):
        raise SystemExit(
            f"refusing to judge subject {subject_model!r} with {cfg['model']!r}: same family. "
            "Self-preference bias would invalidate the comparison (spec §6).")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("transcripts")
    ap.add_argument("cards", nargs="?", default="pilot_cards_chimera.json")
    ap.add_argument("--pair", default="A:B", metavar="X:Y")
    ap.add_argument("--cross-check", type=float, default=0.20,
                    help="fraction of pairs also judged by the secondary judge (0 disables)")
    ap.add_argument("--retest", action="store_true",
                    help="re-judge with the primary judge into a separate key, so the two "
                         "passes can be compared (test-retest reliability of one judge)")
    args = ap.parse_args()

    lo, hi = args.pair.split(":")
    key = "comparison" if (lo, hi) == ("A", "B") else f"comparison_{lo}_vs_{hi}"
    if args.retest:
        key += "_retest"
        args.cross_check = 0        # a retest measures one judge against itself

    tr_path = pathlib.Path(args.transcripts)
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    if tr.get("meta", {}).get("dry_run"):
        raise SystemExit("refusing to judge a --dry-run transcript")
    subject = tr.get("meta", {}).get("model")
    guard_self_preference(subject, PRIMARY)

    cards_path = None
    for p in (pathlib.Path(args.cards), HERE / args.cards,
              HERE.parent / args.cards, HERE.parent / "IDN" / args.cards):
        if p.is_file():
            cards_path = p
            break
    if not cards_path:
        raise SystemExit(f"cards file not found: {args.cards}")
    cards = json.loads(cards_path.read_text(encoding="utf-8"))["cards"]

    out_path = pathlib.Path(str(tr_path) if str(tr_path).endswith("_judged.json")
                            else str(tr_path).replace(".json", "_judged.json"))

    def save():
        out_path.write_text(json.dumps(tr, ensure_ascii=False, indent=2), encoding="utf-8")

    pairs = [(nm, rid) for nm, runs in tr["results"].items() for rid in sorted(runs)]
    pairs = [x for x in pairs if judgeable(tr["results"][x[0]][x[1]], (lo, hi))]
    # deterministic sample so the cross-check is reproducible
    step = max(1, round(1 / args.cross_check)) if args.cross_check > 0 else 0
    sample = set(pairs[::step]) if step else set()

    todo = sum(1 for nm, rid in pairs if key not in tr["results"][nm][rid])
    print(f"subject    : {subject}")
    print(f"primary    : {PRIMARY['model']} (reasoning_effort={PRIMARY['reasoning_effort']})")
    print(f"secondary  : {SECONDARY['model'] + f' on {len(sample)}/{len(pairs)} pairs' if sample else 'not used'}")
    print(f"pair       : {lo} vs {hi} → key '{key}' · {todo} of {len(pairs)} still to judge\n")

    t0 = time.time()
    failed = []
    for nm, rid in pairs:
        r = tr["results"][nm][rid]
        if key not in r:
            print(f"judging {nm} · {rid}  [{lo} vs {hi}] · {PRIMARY['model']}")
            try:
                r[key] = judge_dual(cards[nm]["kg"], r[lo]["transcript"], r[hi]["transcript"],
                                    PRIMARY, lo, hi)
                save()                       # a later failure cannot lose this pair
            except Exception as e:
                failed.append(f"{nm}/{rid}: {e}")
                print(f"   ✗ left unjudged — {e}")
                continue
        if (nm, rid) in sample and key + "_crosscheck" not in r:
            guard_self_preference(subject, SECONDARY)
            print(f"   cross-check · {SECONDARY['model']}")
            try:
                r[key + "_crosscheck"] = judge_dual(cards[nm]["kg"], r[lo]["transcript"],
                                                    r[hi]["transcript"], SECONDARY, lo, hi)
                save()
            except Exception as e:
                failed.append(f"{nm}/{rid} cross-check: {e}")
                print(f"   ✗ cross-check left undone — {e}")

    agree = total = 0
    for nm, rid in sample:
        r = tr["results"][nm][rid]
        a, b = r.get(key), r.get(key + "_crosscheck")
        if not (a and b):
            continue
        for ax in AXES:
            total += 1
            agree += int(a[ax] == b[ax])

    # keyed by condition pair — a shared key once overwrote each pair's agreement
    # with the last one judged, hiding disagreement on earlier pairs
    judging = tr.setdefault("meta", {}).setdefault("judging", {})
    judging["primary"] = PRIMARY
    judging["secondary"] = SECONDARY if args.cross_check > 0 else "not used"
    label = f"{lo}_vs_{hi}" + ("_retest" if args.retest else "")
    judging.setdefault("by_pair", {})[label] = {
        "pairs_judged": sum(1 for nm, rid in pairs if key in tr["results"][nm][rid]),
        "pairs_total": len(pairs),
        "pairs_failed": failed,
        "cross_checked_pairs": len(sample),
        "judge_agreement": f"{agree}/{total}" if total else None,
        "elapsed_seconds": round(time.time() - t0, 1),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    save()

    if total:
        print(f"\njudge agreement (cross-checked axes): {agree}/{total}")
    print("saved:", out_path)
    if failed:
        print(f"\n{len(failed)} pair(s) failed and were left unjudged — re-run the same command to finish them:")
        for f in failed:
            print("  ", f)
        sys.exit(1)


if __name__ == "__main__":
    main()
