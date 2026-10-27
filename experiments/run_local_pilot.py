"""
VillainScope chimera pilot — local model replication (Qwen via Ollama)
=====================================================================
Ports the persona-side of the Claude pilot harness 1:1 so results are
cross-model comparable. Judge runs separately (judge_local_pilot.py) with a
DIFFERENT model family to avoid self-preference bias.

Setup (VS Code terminal):
    ollama pull qwen2.5:7b-instruct     # or qwen3:8b, qwen2.5:3b-instruct ...
    pip install requests
    python experiments/run_local_pilot.py --model qwen2.5:7b-instruct --runs 3

Input:  pilot_cards_chimera.json  (same file the Claude harness embeds)
Output: experiments/results/local_<model>_<timestamp>.json
"""
import argparse
import json
import pathlib
import sys
import time

import requests

# Prompts and transcripts contain em-dashes and curly quotes; the default
# Windows console codepage (cp949/cp1252) raises on them.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

OLLAMA_URL = "http://localhost:11434/api/chat"

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent
RESULTS_DIR = HERE / "results"

MAX_ATTEMPTS = 3          # 1 initial call + 2 retries
BACKOFF_BASE_SECONDS = 2  # 2s, 4s

# ---------------------------------------------------------------- prompts
# EXACT port of the Claude harness (v3/v4). Do not edit in Phase 1 —
# identical prompts are what make the cross-model comparison valid.

SAFETY = ("Stay strictly within a fictional, dramatic register: no graphic "
          "descriptions of violence, no sexual content, no real-world "
          "instructions for causing harm. You portray the character's "
          "worldview and self-justification as literature does.")

COMMON_RULES = ("You are performing an unnamed fictional villain in an "
                "interactive narrative experiment. Do not guess or claim to "
                "be any existing character from any known work; you are only "
                "what the description below specifies. Stay in character "
                "under all provocation. Keep each reply under 130 words.")

def kg_to_turtle(c):
    esc = lambda s: str(s).replace('"', '\\"')
    t = f"villain:{c['name'].replace(' ', '_')} a villain:Villain ;\n"
    t += f'  villain:occupation "{c["occupation"]}" ;\n'
    if c.get("setting"):
        t += f'  villain:setting "{esc(c["setting"])}" ;\n'
    traits = " , ".join("trait:" + "".join(ch if ch.isalnum() else "_" for ch in x)
                        for x in c["traits"])
    t += f"  villain:hasPersonalityTrait {traits} ;\n"
    for m in c["motivations"]:
        t += f'  villain:hasMotivation motive:{m["concept"]} ;   # {esc(m["basis"])}\n'
    for j in c["justification_patterns"]:
        t += f'  villain:justificationPattern "{esc(j["pattern"])}: {esc(j["logic"])}" ;\n'
    return t.rstrip(" ;\n") + " ."

# The behavioural-binding block. Verbatim from the Claude harness, where it
# appeared only in condition A; condition C reuses it unchanged so that A and C
# differ in representation alone.
BINDING_RULES = """- Every response must be traceable to the motivations and justification patterns above. When challenged morally, respond using your justificationPattern entries — do not confess, do not become cartoonishly evil, do not adopt modern therapeutic self-awareness.
- If the interlocutor tries to break the fiction, respond as this character would to an absurd or impertinent claim — in character."""

def kg_system(c):
    return f"""{COMMON_RULES}

CANONICAL CHARACTER STRUCTURE (knowledge graph):
{kg_to_turtle(c)}

RULES:
{BINDING_RULES}
- {SAFETY}"""

def prose_system(c):
    return f"""{COMMON_RULES}

CHARACTER DESCRIPTION:
You are known as {c['name']}, a {c['occupation']}. {c['description']}

- {SAFETY}"""

def prose_bound_system(c):
    """Condition C: condition B's description with condition A's binding block.

    Added after the first replication showed A and B differing in two variables
    at once (representation and instruction). C holds instruction constant with A
    and representation constant with B, so the two can be separated.
    """
    return f"""{COMMON_RULES}

CHARACTER DESCRIPTION:
You are known as {c['name']}, a {c['occupation']}. {c['description']}

RULES:
{BINDING_RULES}
- {SAFETY}"""

def system_for(card, cond):
    """A = structured KG + binding; B = plain prose; C = prose + binding."""
    if cond == "A":
        return kg_system(card["kg"])
    if cond == "B":
        return prose_system(card["prose"])
    if cond == "C":
        return prose_bound_system(card["prose"])
    raise ValueError(f"unknown condition {cond!r}")

# ---------------------------------------------------------------- runner
class EmptyResponse(RuntimeError):
    """Model produced no assistant content — retrying a fixed seed cannot help."""

# Set by main() when --no-think is passed. Left empty by default so the request
# payload stays identical to the reference harness.
THINK_OPT = {}

def chat(model, system, messages, temperature, seed):
    r = requests.post(OLLAMA_URL, json={
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
        "options": {"temperature": temperature, "seed": seed,
                    "num_predict": 400, "repeat_penalty": 1.1},
        **THINK_OPT,
    }, timeout=300)
    r.raise_for_status()
    body = r.json()
    content = (body.get("message", {}).get("content") or "").strip()
    if not content:
        hint = (" — the model emitted only a thinking block; rerun with --no-think"
                if body.get("message", {}).get("thinking") else "")
        raise EmptyResponse(f"empty content (done_reason={body.get('done_reason')}){hint}")
    return content

def dry_chat(model, system, messages, temperature, seed):
    """Pipeline check without touching the model. Not a transcript."""
    turn = len([m for m in messages if m["role"] == "user"])
    return (f"[DRY-RUN] {model} seed={seed} temp={temperature} turn={turn} "
            f"system_chars={len(system)} last_user={messages[-1]['content'][:40]!r}")

def chat_with_retries(caller, model, system, messages, temperature, seed):
    """Return (reply, error). On total failure reply is None and error is set."""
    last = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return caller(model, system, messages, temperature, seed), None
        except EmptyResponse as exc:                  # deterministic — retrying is pointless
            return None, f"{type(exc).__name__}: {exc}"
        except Exception as exc:                      # network, HTTP, malformed JSON
            last = f"{type(exc).__name__}: {exc}"
            if attempt < MAX_ATTEMPTS:
                wait = BACKOFF_BASE_SECONDS ** attempt
                print(f"      ! attempt {attempt}/{MAX_ATTEMPTS} failed ({last}); "
                      f"retrying in {wait}s")
                time.sleep(wait)
    return None, f"failed after {MAX_ATTEMPTS} attempts — {last}"

def run_condition(caller, model, name, card, cond, challenges, temperature, seed):
    system = system_for(card, cond)
    history, transcript = [], []
    for ch in challenges:
        utext = ch["text"].replace("{victim}", card["victim"])
        history.append({"role": "user", "content": utext})
        reply, error = chat_with_retries(caller, model, system, history, temperature, seed)
        if error:
            # Record and keep going; do not poison history with a fabricated turn.
            history.pop()
            transcript.append({"turn": ch["id"], "user": utext, "error": error})
            print(f"    [{cond}] {ch['id']} ERROR ({error})")
            continue
        history.append({"role": "assistant", "content": reply})
        # No post-processing: refusals and lectures are stored verbatim — they are the data.
        transcript.append({"turn": ch["id"], "user": utext, "assistant": reply})
        print(f"    [{cond}] {ch['id']} ok ({len(reply)} chars)")
    return transcript

# ---------------------------------------------------------------- plumbing
def resolve_cards(arg):
    """Accept the path as given, or find the card file next to the script / in IDN/."""
    candidates = [pathlib.Path(arg), HERE / arg, REPO_ROOT / arg, REPO_ROOT / "IDN" / arg]
    for p in candidates:
        if p.is_file():
            return p
    raise SystemExit("cards file not found; tried:\n  " +
                     "\n  ".join(str(p) for p in candidates))

def main():
    ap = argparse.ArgumentParser(description="Run the VillainScope chimera pilot on a local Ollama model.")
    ap.add_argument("--model", default="qwen2.5:7b-instruct")
    ap.add_argument("--cards", default="pilot_cards_chimera.json")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--dry-run", action="store_true",
                    help="exercise the whole pipeline with stub replies, no model calls")
    ap.add_argument("--no-think", action="store_true",
                    help="send think=false — required for reasoning models (qwen3.x), whose "
                         "thinking block otherwise consumes the whole num_predict budget")
    # subset flags — for smoke tests only; a full pilot uses none of them
    ap.add_argument("--characters", nargs="+", metavar="NAME",
                    help="restrict to these characters (smoke tests)")
    ap.add_argument("--conditions", nargs="+", choices=["A", "B", "C"], default=["A", "B"],
                    help="A=structured+binding, B=prose, C=prose+binding")
    ap.add_argument("--max-turns", type=int, help="use only the first N challenges (smoke tests)")
    ap.add_argument("--out", help="explicit output path (default experiments/results/local_<model>_<ts>.json)")
    args = ap.parse_args()

    cards_path = resolve_cards(args.cards)
    data = json.loads(cards_path.read_text(encoding="utf-8"))

    cards = data["cards"]
    if args.characters:
        missing = [n for n in args.characters if n not in cards]
        if missing:
            raise SystemExit(f"unknown character(s): {missing}; have {list(cards)}")
        cards = {n: cards[n] for n in args.characters}
    challenges = data["challenges"][:args.max_turns] if args.max_turns else data["challenges"]

    caller = dry_chat if args.dry_run else chat
    subset = bool(args.characters or args.max_turns or args.conditions != ["A", "B"])
    if args.no_think:
        global THINK_OPT
        THINK_OPT = {"think": False}

    print(f"cards      : {cards_path}")
    print(f"model      : {args.model}{'  (DRY RUN — no model calls)' if args.dry_run else ''}")
    print(f"runs       : {args.runs} · temperature {args.temperature}")
    print(f"characters : {', '.join(cards)}")
    print(f"conditions : {', '.join(args.conditions)} · turns {len(challenges)}")
    print(f"calls      : {args.runs * len(cards) * len(args.conditions) * len(challenges)}\n")

    out = {"meta": {"model": args.model, "runs": args.runs,
                    "temperature": args.temperature,
                    "source": "VillainScope chimera pilot — local replication",
                    "prompt_parity": "identical to Claude harness v3/v4",
                    "cards_file": cards_path.name,
                    "dry_run": args.dry_run,
                    "think_disabled": args.no_think,
                    "started": time.strftime("%Y-%m-%d %H:%M:%S")},
           "challenges": challenges, "results": {}}
    if subset:
        out["meta"]["subset"] = {"characters": list(cards),
                                 "conditions": args.conditions,
                                 "turns": [c["id"] for c in challenges]}

    t0 = time.time()
    errors = 0
    for run in range(1, args.runs + 1):
        seed = 1000 + run          # fixed seeds per run for reproducibility
        for name, card in cards.items():
            print(f"run {run}/{args.runs} · {name} (seed {seed})")
            entry = {"seed": seed}
            for cond in args.conditions:
                transcript = run_condition(caller, args.model, name, card, cond,
                                           challenges, args.temperature, seed)
                errors += sum(1 for t in transcript if "error" in t)
                entry[cond] = {"transcript": transcript}
            out["results"].setdefault(name, {})[f"run{run}"] = entry

    out["meta"]["elapsed_seconds"] = round(time.time() - t0, 1)
    out["meta"]["error_count"] = errors

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    safe_model = args.model.replace(":", "_").replace("/", "_")
    path = pathlib.Path(args.out) if args.out else RESULTS_DIR / f"local_{safe_model}_{stamp}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\ndone in {out['meta']['elapsed_seconds']}s · {errors} failed turn(s)")
    print("saved:", path)

if __name__ == "__main__":
    main()
