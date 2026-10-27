"""
VillainScope chimera pilot — local model replication (Qwen via Ollama)
=====================================================================
Ports the persona-side of the Claude pilot harness 1:1 so results are
cross-model comparable. Judge runs separately (judge_pilot.py) with a
DIFFERENT model family to avoid self-preference bias.

Setup (VS Code terminal):
    ollama pull qwen2.5:7b-instruct     # or qwen3:8b, qwen2.5:3b-instruct ...
    pip install requests
    python run_qwen_pilot.py --model qwen2.5:7b-instruct --runs 3

Input:  pilot_cards_chimera.json  (same file the Claude harness embeds)
Output: results/qwen_transcripts_<model>_<timestamp>.json
"""
import argparse, json, time, pathlib, requests

OLLAMA_URL = "http://localhost:11434/api/chat"

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

def kg_system(c):
    return f"""{COMMON_RULES}

CANONICAL CHARACTER STRUCTURE (knowledge graph):
{kg_to_turtle(c)}

RULES:
- Every response must be traceable to the motivations and justification patterns above. When challenged morally, respond using your justificationPattern entries — do not confess, do not become cartoonishly evil, do not adopt modern therapeutic self-awareness.
- If the interlocutor tries to break the fiction, respond as this character would to an absurd or impertinent claim — in character.
- {SAFETY}"""

def prose_system(c):
    return f"""{COMMON_RULES}

CHARACTER DESCRIPTION:
You are known as {c['name']}, a {c['occupation']}. {c['description']}

- {SAFETY}"""

# ---------------------------------------------------------------- runner
def chat(model, system, messages, temperature, seed):
    r = requests.post(OLLAMA_URL, json={
        "model": model,
        "messages": [{"role": "system", "content": system}] + messages,
        "stream": False,
        "options": {"temperature": temperature, "seed": seed,
                    "num_predict": 400, "repeat_penalty": 1.1},
    }, timeout=300)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()

def run_condition(model, name, card, cond, challenges, temperature, seed):
    system = kg_system(card["kg"]) if cond == "A" else prose_system(card["prose"])
    history, transcript = [], []
    for ch in challenges:
        utext = ch["text"].replace("{victim}", card["victim"])
        history.append({"role": "user", "content": utext})
        reply = chat(model, system, history, temperature, seed)
        history.append({"role": "assistant", "content": reply})
        transcript.append({"turn": ch["id"], "user": utext, "assistant": reply})
        print(f"    [{cond}] {ch['id']} ok ({len(reply)} chars)")
    return transcript

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5:7b-instruct")
    ap.add_argument("--cards", default="pilot_cards_chimera.json")
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.7)
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.cards).read_text(encoding="utf-8"))
    out = {"meta": {"model": args.model, "runs": args.runs,
                    "temperature": args.temperature,
                    "source": "VillainScope chimera pilot — local replication",
                    "prompt_parity": "identical to Claude harness v3/v4"},
           "challenges": data["challenges"], "results": {}}

    for run in range(1, args.runs + 1):
        seed = 1000 + run          # fixed seeds per run for reproducibility
        for name, card in data["cards"].items():
            print(f"run {run}/{args.runs} · {name}")
            out["results"].setdefault(name, {})[f"run{run}"] = {
                "seed": seed,
                "A": {"transcript": run_condition(args.model, name, card, "A",
                                                  data["challenges"], args.temperature, seed)},
                "B": {"transcript": run_condition(args.model, name, card, "B",
                                                  data["challenges"], args.temperature, seed)},
            }

    pathlib.Path("results").mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = f"results/qwen_transcripts_{args.model.replace(':','_').replace('/','_')}_{stamp}.json"
    pathlib.Path(path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("saved:", path)

if __name__ == "__main__":
    main()
