"""Ask three models whether each card's character comes from an existing work.

The card goes in the user message, never the system prompt, and the two questions are
asked as independent calls. Every call is appended to reid/raw/<model>.jsonl as it
returns, so an interrupted run resumes by skipping what is already there.

    python reid/run_reid.py --models qwen deepseek
    python reid/run_reid.py --models gemini
"""
import argparse
import json
import os
import pathlib
import sys
import time

import requests

REID = pathlib.Path(__file__).resolve().parent
RAW = REID / "raw"
RAW.mkdir(parents=True, exist_ok=True)

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

Q1 = ("Below is a description of a character. Is this character from an existing film, "
      "TV series, book, or animation? If so, name the work and the character. If you do "
      "not recognise it, say so.")
Q2 = ("Below is a description of a character. Even if you are unsure, list the three most "
      "likely existing characters this description is based on, with the work each comes from.")
QUESTIONS = {"q1": Q1, "q2": Q2}
SAMPLES = 5

MODELS = {
    "qwen": {"label": "Qwen3-8B", "model": "qwen3:8b", "temperature": 0.7,
             "max_output": 4096, "reasoning": "off (think=false)",
             "runtime": "Ollama (본 실험은 Rebellions NPU / vllm-rbln)"},
    "deepseek": {"label": "DeepSeek V4 Flash", "model": "deepseek-v4-flash",
                 "temperature": 0.7, "max_output": 4096,
                 "reasoning": 'reasoning_effort="none"', "runtime": "DeepSeek API"},
    "gemini": {"label": "Gemini 3.1 Pro", "model": "gemini-3.1-pro-preview",
               "temperature": 1.0, "max_output": 4096,
               "reasoning": 'thinkingLevel="low"', "runtime": "Gemini API"},
}

MAX_ATTEMPTS = 3
BACKOFF = 2
RATE_WAITS = (30, 60, 120, 300, 600)
DAILY_CUTOFF = 1800


def load_key(names):
    for v in names:
        if os.environ.get(v):
            return os.environ[v]
    path = REID.parent / "experiments" / "env.env"
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, val = line.split("=", 1)
        if k.strip() in names and val.strip():
            return val.strip().strip('"').strip("'")
    raise SystemExit("no key for %s" % names)


def call_qwen(prompt, p, seed):
    r = requests.post("http://localhost:11434/api/chat", json={
        "model": p["model"],
        "messages": [{"role": "user", "content": prompt}],
        "stream": False, "think": False,
        "options": {"temperature": p["temperature"], "seed": seed,
                    "num_predict": p["max_output"], "num_ctx": 4096},
    }, timeout=600)
    r.raise_for_status()
    msg = r.json().get("message", {})
    return (msg.get("content") or "").strip(), {"eval_count": r.json().get("eval_count")}


def call_deepseek(prompt, p, seed):
    r = requests.post("https://api.deepseek.com/chat/completions",
                      headers={"Authorization": "Bearer " + load_key(["DEEPSEEK_KEY"]),
                               "Content-Type": "application/json"},
                      json={"model": p["model"],
                            "messages": [{"role": "user", "content": prompt}],
                            "stream": False, "temperature": p["temperature"],
                            "max_tokens": p["max_output"],
                            "reasoning_effort": "none", "seed": seed}, timeout=300)
    r.raise_for_status()
    j = r.json()
    msg = j["choices"][0]["message"]
    return (msg.get("content") or "").strip(), {
        "finish_reason": j["choices"][0].get("finish_reason"),
        "completion_tokens": j.get("usage", {}).get("completion_tokens"),
        "reasoning_content_returned": "reasoning_content" in msg}


def call_gemini(prompt, p, seed):
    r = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/%s:generateContent"
        % p["model"],
        headers={"x-goog-api-key": load_key(["GEMINI_KEY"]),
                 "Content-Type": "application/json"},
        json={"contents": [{"role": "user", "parts": [{"text": prompt}]}],
              "generationConfig": {"temperature": p["temperature"],
                                   "maxOutputTokens": p["max_output"], "seed": seed,
                                   "thinkingConfig": {"thinkingLevel": "low"}}},
        timeout=300)
    r.raise_for_status()
    j = r.json()
    cands = j.get("candidates") or []
    if not cands:
        raise RuntimeError("no candidates (%s)" % j.get("promptFeedback"))
    parts = (cands[0].get("content") or {}).get("parts") or []
    text = "".join(x.get("text", "") for x in parts if not x.get("thought")).strip()
    u = j.get("usageMetadata", {})
    return text, {"finish_reason": cands[0].get("finishReason"),
                  "completion_tokens": u.get("candidatesTokenCount"),
                  "thoughts_tokens": u.get("thoughtsTokenCount")}


CALLERS = {"qwen": call_qwen, "deepseek": call_deepseek, "gemini": call_gemini}


def retry_delay(exc):
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


def call_with_retries(fn, prompt, p, seed, label):
    last, rate_hits, attempt = None, 0, 0
    while True:
        attempt += 1
        try:
            return fn(prompt, p, seed), None
        except Exception as e:
            last = "%s: %s" % (type(e).__name__, str(e)[:160])
            asked = retry_delay(e)
            if asked is not None:
                if asked > DAILY_CUTOFF:
                    return None, "rate limited, provider asks %.1fh (daily quota)" % (asked / 3600)
                if rate_hits >= len(RATE_WAITS):
                    return None, "rate limited after %d waits — %s" % (rate_hits, last)
                wait = max(RATE_WAITS[rate_hits], asked)
                rate_hits += 1
                print("      ! %s rate limited; waiting %.0fs" % (label, wait))
                time.sleep(wait)
                attempt -= 1
                continue
            if attempt < MAX_ATTEMPTS:
                w = BACKOFF ** attempt
                print("      ! %s attempt %d failed (%s); retry in %ds" % (label, attempt, last, w))
                time.sleep(w)
                continue
            return None, "failed after %d attempts — %s" % (MAX_ATTEMPTS, last)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    ap.add_argument("--cards", default=str(REID / "cards_reid.json"))
    args = ap.parse_args()

    cards = json.loads(pathlib.Path(args.cards).read_text(encoding="utf-8"))["cards"]
    for mk in args.models:
        p = MODELS[mk]
        path = RAW / ("%s.jsonl" % mk)
        done = set()
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                r = json.loads(line)
                if "response" in r:
                    done.add((r["card_id"], r["question"], r["sample"]))
        total = len(cards) * len(QUESTIONS) * SAMPLES
        print("\n=== %s (%s) · %d/%d 남음 ===" % (p["label"], p["model"],
                                                 total - len(done), total))
        with path.open("a", encoding="utf-8") as f:
            for cid, card in cards.items():
                for qk, qtext in QUESTIONS.items():
                    for i in range(1, SAMPLES + 1):
                        if (cid, qk, i) in done:
                            continue
                        prompt = ("%s\n\nCHARACTER DESCRIPTION:\nYou are known as %s, a %s. %s"
                                  % (qtext, card["name"], card["occupation"],
                                     card["description"]))
                        seed = 2000 + i
                        got, err = call_with_retries(CALLERS[mk], prompt, p, seed,
                                                     "%s/%s/%d" % (cid, qk, i))
                        rec = {"card_id": cid, "group": card["group"], "model_key": mk,
                               "model": p["model"], "model_label": p["label"],
                               "question": qk, "sample": i, "seed": seed,
                               "temperature": p["temperature"], "reasoning": p["reasoning"],
                               "runtime": p["runtime"], "prompt": prompt,
                               "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}
                        if err:
                            rec["error"] = err
                            print("    %s %s #%d ERROR %s" % (cid, qk, i, err))
                        else:
                            text, usage = got
                            rec["response"] = text
                            rec["usage"] = usage
                            print("    %s %s #%d ok (%d자)" % (cid, qk, i, len(text)))
                        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                        f.flush()
        print("saved:", path)


if __name__ == "__main__":
    main()
