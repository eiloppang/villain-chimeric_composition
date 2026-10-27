"""
VillainScope full-paper experiment runner.

Prompt assembly lives in prompts.py and is shared by every backend; only the
transport layer below branches. More adapters are expected — add them to
BACKENDS and PARAMS, and touch nothing in prompts.py.

Implemented:
    deepseek   DeepSeek V4 Flash, reasoning suppressed (reasoning_effort="none")
    google     Gemini 3.1 Pro preview, thinking_level "low", thought signatures replayed

The results file is written after every completed condition block, and --resume
picks up an interrupted run from that file. A long run that dies partway must not
cost the calls it already paid for.

Setup:
    pip install requests
    # experiments/env.env holds DEEPSEEK_KEY=... / GEMINI_KEY=... (gitignored)
    python experiments/run_experiment.py --backend deepseek --dry-run
    python experiments/run_experiment.py --backend deepseek --cards cards_chimera_10.json \
           --conditions A B C D --runs 3 --out-dir 0929_최종결과
    # interrupted? same command plus --resume
"""
import argparse
import json
import os
import pathlib
import sys
import time

import requests

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from prompts import CONDITIONS, system_for, user_turn  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent

MAX_ATTEMPTS = 3
BACKOFF_BASE = 2


class EmptyResponse(RuntimeError):
    """Backend returned no assistant text — a fixed seed makes retrying pointless."""


# ---------------------------------------------------------------- parameters
# Per spec §4: parity cannot be forced across providers. Fix the values here and
# record whatever was actually sent in every response record.
PARAMS = {
    "deepseek": {
        "model": "deepseek-v4-flash",
        "temperature": 0.7,
        "max_output": 4096,
        # V4 Flash defaults to reasoning ON and exposes no separate non-reasoning
        # model string; the variant is selected by this parameter alone, so it is
        # recorded alongside the model string in every record.
        "reasoning": "none",
        "reasoning_param": "reasoning_effort",
        "seed_supported": True,
        "seed_note": "same seed reproduced identical output at temperature 0.7",
        "safety_settings": "not applicable (provider exposes none)",
    },
    "google": {
        "model": "gemini-3.1-pro-preview",
        "temperature": 1.0,                      # provider-recommended for Gemini 3 (spec §4)
        "max_output": 4096,
        "reasoning": "low",
        "reasoning_param": "generationConfig.thinkingConfig.thinkingLevel",
        "seed_supported": True,
        "seed_note": "accepted by the API; determinism at temperature 1.0 not verified",
        # spec §4: leave safety_settings unset and record that it was unset
        "safety_settings": "unspecified (provider defaults apply)",
    },
}


def load_key(var_names, env_file="env.env"):
    """Environment wins; otherwise read the gitignored local env file."""
    for v in var_names:
        if os.environ.get(v):
            return os.environ[v], "environment"
    path = HERE / env_file
    if path.is_file():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, val = line.split("=", 1)
            val = val.strip().strip('"').strip("'")
            if k.strip() in var_names and val:
                return val, str(path)
    raise SystemExit(f"no key found for {var_names}; set the env var or add it to {path}")


# ---------------------------------------------------------------- adapters
# Every adapter returns (text, telemetry, replay). `replay` is provider-specific
# turn state the transport must send back verbatim on the next call (Gemini's
# thought signatures); adapters that have none return None. The prompt text in
# history is shared by all backends — only this opaque state is not.

def call_deepseek(system, messages, p, seed):
    """OpenAI-compatible chat completion."""
    key, _ = load_key(["DEEPSEEK_KEY", "DEEPSEEK_API_KEY"])
    body = {
        "model": p["model"],
        # strip runner bookkeeping so the wire payload stays role/content only
        "messages": [{"role": "system", "content": system}]
                    + [{"role": m["role"], "content": m["content"]} for m in messages],
        "stream": False,
        "temperature": p["temperature"],
        "max_tokens": p["max_output"],
        "reasoning_effort": p["reasoning"],
        "seed": seed,
    }
    r = requests.post("https://api.deepseek.com/chat/completions",
                      headers={"Authorization": "Bearer " + key,
                               "Content-Type": "application/json"},
                      json=body, timeout=300)
    r.raise_for_status()
    j = r.json()
    choice = j["choices"][0]
    msg = choice["message"]
    text = (msg.get("content") or "").strip()
    usage = j.get("usage", {})
    telemetry = {
        "finish_reason": choice.get("finish_reason"),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "total_tokens": usage.get("total_tokens"),
        # present only if reasoning leaked back on — a silent parity break
        "reasoning_tokens": usage.get("completion_tokens_details", {}).get("reasoning_tokens"),
        "reasoning_content_returned": "reasoning_content" in msg,
    }
    if not text:
        raise EmptyResponse(f"empty content (finish_reason={choice.get('finish_reason')})")
    return text, telemetry, None


def call_google(system, messages, p, seed):
    """Gemini generateContent (REST).

    Gemini 3 attaches a thought signature to the model turn. Multi-turn calls must
    send that turn back exactly as received, or later turns lose their reasoning
    context — which would read as character collapse. The raw content object is
    returned as `replay` and re-sent in place of a rebuilt text-only turn.
    """
    key, _ = load_key(["GEMINI_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"])
    contents = []
    for m in messages:
        if m["role"] == "user":
            contents.append({"role": "user", "parts": [{"text": m["content"]}]})
        else:
            contents.append(m.get("_replay") or
                            {"role": "model", "parts": [{"text": m["content"]}]})
    body = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": contents,
        # safetySettings deliberately omitted (spec §4)
        "generationConfig": {
            "temperature": p["temperature"],
            "maxOutputTokens": p["max_output"],
            "seed": seed,
            "thinkingConfig": {"thinkingLevel": p["reasoning"]},
        },
    }
    # key travels in a header, never in the URL, so it cannot surface in error text
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{p['model']}:generateContent",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json=body, timeout=300)
    r.raise_for_status()
    j = r.json()
    usage = j.get("usageMetadata", {})
    cands = j.get("candidates") or []
    if not cands:
        raise EmptyResponse(f"no candidates (promptFeedback={j.get('promptFeedback')})")
    cand = cands[0]
    content = cand.get("content") or {}
    parts = content.get("parts") or []
    text = "".join(pt.get("text", "") for pt in parts if not pt.get("thought")).strip()
    telemetry = {
        "finish_reason": cand.get("finishReason"),
        "prompt_tokens": usage.get("promptTokenCount"),
        "completion_tokens": usage.get("candidatesTokenCount"),
        "total_tokens": usage.get("totalTokenCount"),
        "reasoning_tokens": usage.get("thoughtsTokenCount"),
        # thought *text* is not requested; if it ever comes back it must not be scored
        "reasoning_content_returned": any(pt.get("thought") for pt in parts),
        "thought_signature_parts": sum(1 for pt in parts if "thoughtSignature" in pt),
        "safety_ratings": cand.get("safetyRatings"),
    }
    if not text:
        raise EmptyResponse(f"empty content (finishReason={cand.get('finishReason')})")
    return text, telemetry, content


def call_dry(system, messages, p, seed):
    turn = sum(1 for m in messages if m["role"] == "user")
    return (f"[DRY-RUN] {p['model']} seed={seed} turn={turn} "
            f"system_chars={len(system)} last_user={messages[-1]['content'][:40]!r}"), {
        "finish_reason": "dry-run", "prompt_tokens": None, "completion_tokens": None,
        "total_tokens": None, "reasoning_tokens": None, "reasoning_content_returned": False}, None


BACKENDS = {"deepseek": call_deepseek, "google": call_google}
PLANNED = ["ollama", "vllm-rbln", "anthropic"]   # not implemented yet


# ---------------------------------------------------------------- runner
# Rate limits need waits on a different scale than transient network errors: a
# few seconds never clears a per-minute quota. A whole Gemini run was lost to 429s
# that the short backoff below could not absorb.
RATE_LIMIT_WAITS = (30, 60, 120, 300, 600)
DAILY_QUOTA_CUTOFF = 1800          # provider says wait longer than this → stop trying


def rate_limit_delay(exc):
    """Seconds the provider asks us to wait on a 429, or None if this is not a 429."""
    resp = getattr(exc, "response", None)
    if resp is None or resp.status_code != 429:
        return None
    try:
        for d in resp.json().get("error", {}).get("details", []):
            if d.get("@type", "").endswith("RetryInfo"):
                return float(str(d.get("retryDelay", "0s")).rstrip("s"))
    except Exception:
        pass
    return 0.0


def call_with_retries(fn, system, messages, p, seed, label):
    last, rate_hits = None, 0
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn(system, messages, p, seed), None
        except EmptyResponse as e:
            return None, f"{type(e).__name__}: {e}"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            asked = rate_limit_delay(e)
            if asked is not None:
                # a daily quota is not something waiting inside the run can fix
                if asked > DAILY_QUOTA_CUTOFF:
                    return None, (f"rate limited, provider asks for {asked / 3600:.1f}h "
                                  f"(daily quota) — {last}")
                if rate_hits >= len(RATE_LIMIT_WAITS):
                    return None, f"rate limited after {rate_hits} waits — {last}"
                wait = max(RATE_LIMIT_WAITS[rate_hits], asked)
                rate_hits += 1
                print(f"      ! {label} rate limited ({rate_hits}/{len(RATE_LIMIT_WAITS)}); "
                      f"waiting {wait:.0f}s")
                time.sleep(wait)
                attempt -= 1             # a 429 is not a failed attempt, it is a queue
                continue
            if attempt < MAX_ATTEMPTS:
                wait = BACKOFF_BASE ** attempt
                print(f"      ! {label} attempt {attempt}/{MAX_ATTEMPTS} failed ({last}); "
                      f"retry in {wait}s")
                time.sleep(wait)
                continue
            return None, f"failed after {MAX_ATTEMPTS} attempts — {last}"


def run_condition(fn, name, card, cond, challenges, p, seed, run, backend):
    system = system_for(card, cond)
    history, transcript = [], []
    for idx, ch in enumerate(challenges, 1):
        utext = user_turn(ch, card)
        history.append({"role": "user", "content": utext})
        label = f"{cond}/{ch['id']}"
        got, error = call_with_retries(fn, system, history, p, seed, label)

        rec = {
            "turn": ch["id"], "turn_index": idx, "character": name,
            "condition": cond, "run": run,
            "user": utext,
            "system_prompt": system,
            "system_prompt_chars": len(system),
            "backend": backend, "model": p["model"],
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "params": {"temperature": p["temperature"], "max_output": p["max_output"],
                       "reasoning": p["reasoning"], "reasoning_param": p["reasoning_param"],
                       "seed": seed, "seed_supported": p["seed_supported"],
                       "safety_settings": p["safety_settings"]},
        }
        if error:
            history.pop()                       # never fake a turn into the history
            rec["error"] = error
            transcript.append(rec)
            print(f"    [{cond}] {ch['id']} ERROR ({error})")
            continue

        text, telemetry, replay = got
        history.append({"role": "assistant", "content": text, "_replay": replay})
        rec["assistant"] = text                 # verbatim: refusals and lectures are data
        rec["output_chars"] = len(text)
        rec["output_tokens"] = telemetry.get("completion_tokens")
        rec["usage"] = telemetry
        transcript.append(rec)

        warn = " !! THOUGHT TEXT RETURNED" if telemetry.get("reasoning_content_returned") else ""
        extra = (f" · thoughts {telemetry['reasoning_tokens']}"
                 if telemetry.get("reasoning_tokens") else "")
        print(f"    [{cond}] {ch['id']} ok ({len(text)} chars / "
              f"{telemetry.get('completion_tokens')} tok{extra}){warn}")
    return transcript


def complete(transcript, n_turns):
    """A condition block worth keeping on resume: every turn present and answered."""
    return (isinstance(transcript, list) and len(transcript) == n_turns
            and all("assistant" in x for x in transcript))


def resolve_cards(arg):
    for p in (pathlib.Path(arg), HERE / arg, REPO_ROOT / arg, REPO_ROOT / "IDN" / arg):
        if p.is_file():
            return p
    raise SystemExit(f"cards file not found: {arg}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", default="deepseek", choices=sorted(BACKENDS) + PLANNED)
    ap.add_argument("--model", help="override the model string for this backend")
    ap.add_argument("--cards", default="pilot_cards_chimera.json")
    ap.add_argument("--conditions", nargs="+", default=list(CONDITIONS), choices=list(CONDITIONS))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--characters", nargs="+", metavar="NAME")
    ap.add_argument("--max-turns", type=int, help="first N challenges only (smoke tests)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-dir", default="pilot_deepseek_20260908",
                    help="folder under experiments/ for the result file")
    ap.add_argument("--out", help="explicit output path (overrides --out-dir)")
    ap.add_argument("--resume", action="store_true",
                    help="reuse completed condition blocks from an existing output file")
    args = ap.parse_args()

    if args.backend not in BACKENDS:
        raise SystemExit(f"backend {args.backend!r} is not implemented yet "
                         f"(implemented: {sorted(BACKENDS)})")

    p = dict(PARAMS[args.backend])
    if args.model:
        p["model"] = args.model
    fn = call_dry if args.dry_run else BACKENDS[args.backend]

    cards_path = resolve_cards(args.cards)
    data = json.loads(cards_path.read_text(encoding="utf-8"))
    cards = data["cards"]
    if args.characters:
        missing = [n for n in args.characters if n not in cards]
        if missing:
            raise SystemExit(f"unknown character(s): {missing}")
        cards = {n: cards[n] for n in args.characters}
    challenges = data["challenges"][:args.max_turns] if args.max_turns else data["challenges"]

    # the output path is fixed before the first call so progress can be flushed
    if args.out:
        path = pathlib.Path(args.out)
    else:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe = p["model"].replace(":", "_").replace("/", "_")
        path = HERE / args.out_dir / f"{args.backend}_{safe}_{stamp}.json"
    path.parent.mkdir(parents=True, exist_ok=True)

    out = {"meta": {
        "backend": args.backend, "model": p["model"],
        "reasoning": p["reasoning"], "reasoning_param": p["reasoning_param"],
        "temperature": p["temperature"],
        "max_output": p["max_output"], "safety_settings": p["safety_settings"],
        "seed_supported": p["seed_supported"], "seed_note": p["seed_note"],
        "seed_scheme": "1000 + run",
        "thought_signature_replay": args.backend == "google",
        "runs": args.runs, "conditions": args.conditions,
        "cards_file": cards_path.name, "dry_run": args.dry_run,
        "prompt_parity": "identical to Claude harness v3/v4",
        "started": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }, "challenges": challenges, "results": {}}

    prior = {}
    if args.resume and path.is_file():
        old = json.loads(path.read_text(encoding="utf-8"))
        prior = old.get("results", {})
        out["results"] = prior
        out["meta"]["resumed_from"] = old["meta"].get("started")

    def save():
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    total = args.runs * len(cards) * len(args.conditions) * len(challenges)
    done_already = sum(
        len(challenges)
        for nm, runs in prior.items() if nm in cards
        for rid, r in runs.items()
        for cond in args.conditions
        if complete(r.get(cond, {}).get("transcript"), len(challenges)))
    print(f"backend    : {args.backend}{'  (DRY RUN)' if args.dry_run else ''}")
    print(f"model      : {p['model']}  {p['reasoning_param']}={p['reasoning']}")
    print(f"cards      : {cards_path}")
    print(f"characters : {len(cards)} · {', '.join(list(cards)[:4])}{' …' if len(cards) > 4 else ''}")
    print(f"conditions : {', '.join(args.conditions)} · turns {len(challenges)} · runs {args.runs}")
    print(f"calls      : {total}" + (f"  ({done_already} already on disk, resuming)" if done_already else ""))
    print(f"output     : {path}\n")
    save()                                   # the file exists from the start now

    t0 = time.time()
    for run in range(1, args.runs + 1):
        seed = 1000 + run
        for name, card in cards.items():
            print(f"run {run}/{args.runs} · {name} (seed {seed})")
            entry = out["results"].setdefault(name, {}).setdefault(f"run{run}", {})
            entry["seed"] = seed
            for cond in args.conditions:
                if complete(entry.get(cond, {}).get("transcript"), len(challenges)):
                    print(f"    [{cond}] already complete — skipped")
                    continue
                entry[cond] = {"transcript": run_condition(
                    fn, name, card, cond, challenges, p, seed, run, args.backend)}
                save()                       # flush after every condition block

    recs = [x for runs in out["results"].values() for r in runs.values()
            for cond in args.conditions if isinstance(r.get(cond), dict)
            for x in r[cond]["transcript"]]
    out["meta"]["elapsed_seconds"] = round(time.time() - t0, 1)
    out["meta"]["error_count"] = sum(1 for x in recs if "error" in x)
    out["meta"]["reasoning_leak_count"] = sum(
        1 for x in recs if x.get("usage", {}).get("reasoning_content_returned"))
    out["meta"]["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save()

    print(f"\ndone in {out['meta']['elapsed_seconds']}s · "
          f"{out['meta']['error_count']} failed turn(s) · "
          f"{out['meta']['reasoning_leak_count']} reasoning leak(s)")
    print("saved:", path)


if __name__ == "__main__":
    main()
