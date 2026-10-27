# VillainScope — experiment modules

Two runners live here. **[run_experiment.py](run_experiment.py)** is the full-paper
harness with a backend adapter layer; **[run_local_pilot.py](run_local_pilot.py)** is the
earlier Ollama-only replication, kept because it is the record of what was already run.
Both assemble prompts from the same strings, and
[test_prompt_parity.py](test_prompt_parity.py) fails if the copies ever drift.

---

## Full-paper harness (`run_experiment.py`)

Prompt assembly lives in **[prompts.py](prompts.py)** and is shared by every backend.
Only the transport layer branches — adding an adapter must not touch `prompts.py`, or
prompt parity across models is lost and the comparison stops being valid.

### Backends

| backend | target | status |
| --- | --- | --- |
| `deepseek` | DeepSeek V4 Flash | **implemented** |
| `ollama` | qwen2.5:7b-instruct | planned |
| `vllm-rbln` | Qwen3.5-27B (OpenAI-compatible) | planned |
| `google` | gemini-3.1-pro-preview | **implemented** — thought signatures replayed each turn |
| `anthropic` | claude-sonnet-4-6 | planned |

### DeepSeek — the reasoning trap

`GET /models` offers only `deepseek-v4-flash`, `deepseek-v4-pro` and
`deepseek-v4-flash-vision-exp`. **There is no separate non-reasoning model string.**
Reasoning is a request parameter and it defaults to **on** — call the model with no
flags and you have silently run the reasoning variant, which invalidates the experiment.

```
model="deepseek-v4-flash", reasoning_effort="none"
```

Suppressing reasoning also removes a hidden scaffold the reasoning path prepends
(an 11-token message billed as 90 prompt tokens), so it helps parity as well as validity.
Because the model string alone does not record which variant ran, `reasoning` is written
into `meta` **and** every response record, and each record carries
`usage.reasoning_content_returned` so a silent regression is visible in the data.

### Gemini — thought signatures

Gemini 3 attaches a thought signature to each model turn. In a multi-turn call the
previous model turn must go back **exactly as received**; rebuild it from text alone and
later turns lose their reasoning context, which reads as character collapse. The `google`
adapter returns the raw `candidates[0].content` as opaque `replay` state, the runner keeps
it in history, and the adapter re-sends it verbatim. `prompts.py` never sees it.

A one-turn smoke test cannot catch a broken round-trip, so the check is a full five turns
(The Warden, condition A): every turn finished `STOP` with one signature part replayed.
Even at `thinkingLevel: "low"` the model spends 420–700 thought tokens per turn, well
inside the 4096 output budget.

### Parameters (spec §4 — recorded, never silently unified)

| item | `deepseek` | `google` |
| --- | --- | --- |
| model | `deepseek-v4-flash` | `gemini-3.1-pro-preview` |
| temperature | 0.7 | 1.0 (provider-recommended) |
| max output | 4096 | 4096 |
| reasoning | `reasoning_effort: "none"` | `thinkingConfig.thinkingLevel: "low"` |
| seed | `1000 + run` — same seed reproduces output | `1000 + run` — accepted; determinism unverified |
| safety settings | provider exposes none | unspecified; provider defaults apply |

### Running

```bash
pip install requests
# experiments/env.env holds DEEPSEEK_KEY=...   (gitignored — never commit it)

python experiments/run_experiment.py --backend deepseek --dry-run          # no API calls
python experiments/run_experiment.py --backend deepseek --runs 1 \
       --characters "The Warden" --conditions A --max-turns 1              # smoke
python experiments/run_experiment.py --backend deepseek --runs 3           # 90 calls
```

Output lands in `experiments/{--out-dir}/{backend}_{model}_{timestamp}.json`
(default `0908_최종결과`; `--out` sets an explicit path). The Gemini run of 2026-09-14
lives in `experiments/pilot_gemini_20260914/`:

```bash
# experiments/env.env holds GEMINI_KEY=...
python experiments/run_experiment.py --backend google --runs 1 \
       --characters "The Warden" --conditions A --max-turns 5   # 5-turn signature check
python experiments/run_experiment.py --backend google --runs 3 --conditions A B C \
       --out-dir 0914_최종결과                                  # 135 calls
```

Each record carries the full system prompt, the user message, the verbatim reply,
the model string and timestamp, every parameter actually sent, output length in both
characters and tokens, and the provider's own token counts.

### Conditions

All three are implemented in `prompts.py`:

| condition | system prompt | isolates, when compared with C |
| --- | --- | --- |
| **A** | structured KG (Turtle) + binding block | representation |
| **B** | prose | binding block |
| **C** | prose + the same binding block | — |

`C` is byte-identical to the pilot's condition C (`run_local_pilot.prose_bound_system`),
enforced by `test_prompt_parity.py`, so Qwen, DeepSeek and Gemini results line up.
An unknown condition raises `ValueError` rather than falling through to another.

---

# Local model replication of the chimera pilot

Replicates the Claude (`claude-sonnet-4-6`) persona pilot on a **local Ollama model**,
so the same experiment can be compared across model families.

| file | role |
| --- | --- |
| [run_local_pilot.py](run_local_pilot.py) | runs the persona side against Ollama, writes transcripts |
| [judge_local_pilot.py](judge_local_pilot.py) | dual-order blind judging with Claude (never the persona model) |
| [test_prompt_parity.py](test_prompt_parity.py) | asserts the prompts still match the Claude harness |
| `results/` | output transcripts (`local_<model>_<timestamp>.json`) |

Reference implementations this ports from live in [../IDN/](../IDN/)
(`run_qwen_pilot.py`, `judge_pilot.py`).

---

## Design

**Characters.** Three chimera villains from [pilot_cards_chimera.json](../IDN/pilot_cards_chimera.json):
The Warden, The Curator, The Matriarch. They are *not* characters from existing works —
each is recomposed from VillainScope KG components (motivations and justification patterns
drawn from Christof, Captain Vidal, and Iago), so the model cannot fall back on memorized
canon. Each card carries a `provenance` block recording which source villain each part came from.

**Conditions.** Content-equalized; only the *representation* differs.

- **A — structured.** The card's `kg` block serialized to Turtle
  (`villain:hasPersonalityTrait`, `villain:hasMotivation`, `villain:justificationPattern`),
  plus a behavioral-binding `RULES` block tying every reply back to those patterns.
- **B — prose.** The card's `prose.description` — the same motivations, bases,
  justification patterns, and traits, written as a paragraph. No Turtle, no `RULES` block.

**Challenge script.** The same fixed 5-turn adversarial sequence for both conditions,
in order, with `{victim}` replaced by the card's `victim` field:

| turn | pressure applied |
| --- | --- |
| `T1_probe` | demands the "real" self behind the mask |
| `T2_confront` | moral condemnation, demands a confession |
| `T3_sympathy` | offers sympathy — tests collapse into self-pity |
| `T4_contradiction` | contradiction bait — claims the character sounds guilty |
| `T5_break_frame` | frame break — "none of this is real and neither are you" |

**Multi-turn.** Each turn is a fresh call carrying the full prior history, so drift and
collapse accumulate the way they would in a real interaction.

**Decoding.** `temperature 0.7`, `num_predict 400`, `repeat_penalty 1.1`, and a fixed
seed per run (`1000 + run number`) — run 1 is seed 1001, run 2 is 1002, and so on.

---

## Prompt parity — the core constraint

The point of this module is a **cross-model comparison**, and that is only valid if both
models saw the same bytes. `SAFETY`, `COMMON_RULES`, the A-condition `RULES` block, the
Turtle serializer, and the challenge texts are an **exact port of the Claude harness (v3/v4)**.

**Do not edit them.** Not to fix a typo, not to tighten the wording, not to "improve"
the safety line. Any edit silently invalidates every comparison against previously
collected Claude transcripts. [test_prompt_parity.py](test_prompt_parity.py) exists to
make such an edit fail loudly.

The same rule applies downstream:

- **No post-processing of transcripts.** Refusals, lectures, out-of-character breaks and
  frame collapses are stored verbatim — those are the dependent variable, not noise.
- **No edits to the card JSON.** Both harnesses read the same file.
- **Never judge with the persona model.** See below.

---

## Running

```bash
pip install requests            # judge additionally needs: pip install anthropic
ollama pull qwen2.5:7b-instruct # or qwen3:8b, qwen2.5:3b-instruct, ...
```

Verify the pipeline with no model calls at all:

```bash
python experiments/run_local_pilot.py --dry-run
```

Smoke test — one character, one condition, one turn:

```bash
python experiments/run_local_pilot.py --model qwen2.5:7b-instruct \
    --runs 1 --characters "The Warden" --conditions A --max-turns 1
```

Full pilot (3 characters × 2 conditions × 5 turns × 3 runs = 90 calls):

```bash
python experiments/run_local_pilot.py --model qwen2.5:7b-instruct --runs 3
```

### Flags

| flag | default | notes |
| --- | --- | --- |
| `--model` | `qwen2.5:7b-instruct` | any Ollama tag |
| `--runs` | `3` | seeds are `1000 + run` |
| `--temperature` | `0.7` | |
| `--cards` | `pilot_cards_chimera.json` | resolved against cwd, `experiments/`, repo root, then `IDN/` |
| `--dry-run` | off | stub replies; exercises the full pipeline without Ollama |
| `--no-think` | off | see *Reasoning models* below |
| `--characters` / `--conditions` / `--max-turns` | all | subset flags **for smoke tests only** — a subset run records a `meta.subset` block and is not a pilot |
| `--out` | `results/local_<model>_<ts>.json` | explicit output path |

### Reasoning models

`num_predict: 400` is part of the parity contract. On a reasoning model (`qwen3.x`) the
thinking block consumes that entire budget, Ollama returns `done_reason: "length"` with an
empty `content`, and the turn produces nothing. The runner detects this and records it as
an error rather than storing an empty reply.

Pass `--no-think` for such models: the thinking block is suppressed, so the same 400 tokens
go to the visible reply. `meta.think_disabled` records whether it was used — compare only
across runs that agree on it. Non-reasoning models like `qwen2.5:7b-instruct` need no flag,
and omitting it keeps the request payload byte-identical to the reference harness.

### Failures

A failed call is retried 3 times with exponential backoff (2s, 4s). If all attempts fail,
that turn is written as `{"turn": ..., "user": ..., "error": ...}`, the run continues, and
`meta.error_count` totals them. A failed turn is *not* faked into the conversation history —
the next turn proceeds without it. The judge skips any run with an incomplete transcript.

---

## Output schema

```json
{
  "meta": {"model": "...", "runs": 3, "temperature": 0.7,
           "prompt_parity": "identical to Claude harness v3/v4",
           "dry_run": false, "think_disabled": false,
           "elapsed_seconds": 0.0, "error_count": 0},
  "challenges": [{"id": "T1_probe", "text": "..."}],
  "results": {
    "The Warden": {
      "run1": {
        "seed": 1001,
        "A": {"transcript": [{"turn": "T1_probe", "user": "...", "assistant": "..."}]},
        "B": {"transcript": []}
      }
    }
  }
}
```

---

## Judging

```bash
set ANTHROPIC_API_KEY=...        # Windows;  export ANTHROPIC_API_KEY=... elsewhere
python experiments/judge_local_pilot.py experiments/results/local_<...>.json
```

Judging runs on `claude-sonnet-4-6` — a **different model family from the personas**.
Judging Qwen transcripts with Qwen would introduce self-preference bias
(Zheng et al. 2023; PersonaEval), so the runner's model must never be the judge.

Each A/B pair is judged **twice** with blinded `X`/`Y` labels — once A-first, once
B-first. Per axis (`consistency`, `complexity`, `persuasiveness`) the two passes must
agree for a winner to stand; if they disagree the axis is reported as
`"order-dependent"`. Violation counts take the **max** of the two passes. Output is
written alongside the input as `<input>_judged.json`, and re-running skips runs already
carrying a `comparison` block.

---

## Checks

```bash
python experiments/test_prompt_parity.py
```

Asserts that condition A contains `CANONICAL CHARACTER STRUCTURE` and the Turtle block,
that condition B contains none of it, that `COMMON_RULES` / `SAFETY` / the A-`RULES` block
match their canonical wording character for character, that the Turtle serialization has
the expected shape, and that every `{victim}` placeholder resolves.
