# VillainScope — Persona Experiments

Materials for the study of how a villain character should be given to a language model:
as a **knowledge graph** or as **prose**, and with or without an explicit **behavioural
binding instruction**. The repository holds the prompts, the runners, the judging
harness, every transcript and verdict produced, and a separate re-identification test of
the synthetic character cards.

The character data comes from [VillainScope](../../), a knowledge graph of 206 villain
characters from books, animation, film and television.

---

## What was run

**Characters.** Ten *chimeric* villains, each assembled from the knowledge-graph
components (motivations, justification patterns, traits) of three different source
villains, with every identifying detail generalised away. Provenance for each component
is recorded in `IDN/cards_chimera_10.json`.

**Conditions.** A 2×2 of representation × instruction. Every condition contains the same
character content; they differ only in how it is written and whether the binding
instruction is present.

| Paper | Key in the data files | Representation | Binding instruction |
| --- | --- | --- | --- |
| A | `A` | Turtle knowledge graph | present |
| A′ | `D` | Turtle knowledge graph | absent |
| B | `C` | prose | present |
| B′ | `B` | prose | absent |

> The data keys are **not** the paper's labels. `B` in a JSON file is prose *without*
> the instruction, which the paper calls B′. `experiments/prompts.py` is authoritative.

**Dialogue.** Each run is a fixed five-turn challenge dialogue: the character is
questioned, pressed morally, offered sympathy, baited into contradiction, and finally
told the fiction is not real.

**Models.** DeepSeek V4 Flash, Gemini 3.1 Pro, and Qwen3-8B (Rebellions NPU, vllm-rbln).
Reasoning modes were disabled wherever the provider allows it; the exact settings are
recorded in the `meta` block of every result file.

**Judging.** Blind pairwise comparison by GPT-5.6 Terra. Each pair of transcripts is
judged twice with the two conditions swapped between the X and Y slots; an axis counts
as a win only when both orders agree, and is otherwise recorded as `order-dependent`.
A judge may not grade output from its own model family — `judge.py` refuses.

---

## Layout

```
IDN/                            character cards and the pilot harness
  cards_chimera_10.json           the ten chimeric villains, with provenance
  pilot_cards_chimera.json        the three-character pilot set
  run_qwen_pilot.py               pilot runner (Ollama)
  judge_pilot.py                  pilot judge

experiments/
  prompts.py                      system-prompt assembly — single source of truth
  test_prompt_parity.py           pins prompts.py against both pilot harnesses
  run_experiment.py               full-paper runner, one adapter per backend
  judge.py                        dual-order blind pairwise judge
  make_cards_10.py                builds cards_chimera_10.json
  run_local_pilot.py              Ollama replication of the pilot
  judge_local_pilot.py
  env.env.example                 copy to env.env and fill in; env.env is gitignored

  pilot_deepseek_20260908/        DeepSeek pilot, conditions A/B only
  pilot_gemini_20260914/          Gemini pilot
  main_20260929/                  main run: three models × four conditions
  figures/                        prompt figures and the re-identification write-up

reid/                           re-identification test (see below)
conversion-dataset_2/           source RDF the cards were built from
```

### Result files

`<model>_abcd.json` holds the transcripts; `<model>_abcd_judged.json` is the same file
with the judge's verdicts merged in. Both carry a `meta` block recording the model
string, sampling parameters, and the judging configuration.

`experiments/main_20260929/` also holds the aggregated tables used in the analysis —
`aggregate_by_pair.csv`, `aggregate_by_character.csv`, `verdicts_all.csv` — and five
write-ups: verification and re-aggregation, the statistics with Holm correction, the
verbatim injected prompts for one character, and two per-character compilations of
transcripts and verdicts.

The reports and the per-character compilations are written in Korean; the transcripts,
prompts and verdicts they quote are in English and are reproduced verbatim.

---

## The re-identification test (`reid/`)

Chimeric cards are only useful if a model does not simply recognise the source
characters. `reid/` tests that directly, with a control group that proves the test has
power.

- `PREREGISTRATION.md` — written and fixed **before** any model was called
- `build_answer_key.py` → `answer_key.json` — accepted names and work titles, also fixed
  before the run
- `build_cards.py` → `cards_reid.json` — 10 chimeras plus 13 single-source control
  cards, built from the same segments, through the same template, under the same
  anonymisation rules; every edit is recorded per card
- `run_reid.py` → `raw/*.jsonl` — 23 cards × 3 models × 2 questions × 5 samples = 690
  calls, each saved as it returns
- `score.py` → `results.csv`, `summary.md`, `ambiguous.csv`

Headline: the control cards are re-identified (Gemini 86% on the open question) while
the chimeras are not (0 of 150 open-question responses across three models). Under
forced guessing the sources do partly surface. `experiments/figures/reid_findings.md`
reports this in full, including two anonymisation leaks the automated token check could
not catch.

---

## Reproducing

```bash
pip install -r requirements.txt
cp experiments/env.env.example experiments/env.env   # then fill in the keys you need

python experiments/test_prompt_parity.py             # prompts must match across harnesses
python experiments/make_cards_10.py                  # rebuild the character cards
python experiments/run_experiment.py --backend deepseek --conditions A B C D --runs 3
python experiments/judge.py experiments/<out>/deepseek_abcd.json IDN/cards_chimera_10.json --pair A:D

python reid/run_reid.py --models qwen deepseek gemini
python reid/score.py
```

Both runners save after every block and resume with `--resume`, so an interrupted run
does not lose what it already has.

`experiments/figures/make_prompt_figures.py` regenerates the two prompt figures.
It reads the strings out of `prompts.py` and `judge.py` rather than restating them, so a
figure cannot drift from what was actually sent.

---

## Known limits

- **One judge.** All verdicts come from a single model. A secondary judge was run on a
  sample of pairs only.
- **No KG-free baseline.** Every condition contains the same character content, so the
  design can separate representation from instruction but cannot speak to what a model
  does with no character specification at all.
- **The consistency axis overlaps the binding instruction.** The instruction tells the
  model not to confess, not to become cartoonish, and not to invent motives; the judge's
  violation definition names the same three things. Effects on consistency under the
  binding conditions should be read with that in mind.
- **Qwen3-8B runtime differs between the two studies** — Rebellions NPU (vllm-rbln) for
  the main experiment, Ollama for the re-identification test, same weights.
- **The aggregation and statistics scripts are not included.** The reports in
  `main_20260929/` were produced from the judged JSON files and the CSVs beside them,
  but the code that produced them was not kept.
- **The manuscript is not in this repository.** This is the experimental record only —
  prompts, runners, transcripts, verdicts and figures.

## License

MIT, as with the VillainScope dataset.
