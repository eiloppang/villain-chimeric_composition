# Judgement data verification · re-aggregation

Condition labels (as in the paper): **A** = KG + binding instruction · **A′** = KG only · **B** = prose + binding instruction · **B′** = prose only. Data keys: A = `A`, A′ = `D`, B = `C`, B′ = `B`; the verbatim judge strings `Disagreed across orders (…)` use the data keys.


## 1. Data sources

| model | file | cards | characters | run | seed | judged pairs |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-8B (NPU) | `verdicts_all.csv` (= `qwen3-8b_abcd_judged.json`) | cards_chimera_10.json | 10 | run1, run2, run3 | 1001–1003 | 30 |
| DeepSeek V4 Flash | `deepseek_abcd_judged.json` | cards_chimera_10.json | 10 | run1, run2, run3 | 1001–1003 | 30 |
| Gemini 3.1 Pro | `gemini_abcd_judged.json` | cards_chimera_10.json | 10 | run1, run2, run3 | 1001–1003 | 30 |

Judged pairs per comparison:

| model | A:B | A′:B′ | A:A′ | B:B′ | A:B′ |
| --- | --- | --- | --- | --- | --- |
| Qwen3-8B (NPU) | 30 | 30 | 30 | 30 | 30 |
| DeepSeek V4 Flash | 30 | 30 | 30 | 30 | 30 |
| Gemini 3.1 Pro | 30 | 30 | 30 | 30 | 30 |

### Why the same comparison changed from 39:35 to 32:16

Both figures come from **the same dialogues and the same judgements**. Only the range of runs included in the aggregation differs.

| aggregation range | A′ : B′ | order-dependent | violations A′ : B′ | axis judgements |
| --- | --- | --- | --- | --- |
| all 3 runs (first report) | 39 : 35 | 16 | 27 : 17 | 90 |
| run1+run2 (second report) | 32 : 16 | 12 | 16 : 13 | 60 |
| run3 alone | 7 : 19 | 4 | 11 : 4 | 30 |

Taken alone, run3 reverses the direction. Both reports use the same data; nothing was newly generated or re-judged.


## 2. Re-aggregation

Wins and order-dependent judgements per axis, with two-sided sign-test p-values excluding order-dependent judgements. The per-character count re-tallies one vote per character by majority over its runs and axes (n=10).


### Qwen3-8B (NPU)

| comparison | isolated variable | axis | left wins | right wins | order-dependent | p (per judgement) | per character | p (n=10) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A:B | representation (instruction present) | consistency | 8 | 10 | 12 | 0.815 | 5 : 5 (ties 0) | 1.000 |
| A:B | representation (instruction present) | complexity | 5 | 13 | 12 | 0.096 | 1 : 5 (ties 4) | 0.219 |
| A:B | representation (instruction present) | persuasiveness | 8 | 11 | 11 | 0.648 | 4 : 5 (ties 1) | 1.000 |
| **A:B** | **3-axis total** | | **21** | **34** | **35** | **0.105** | | |
| A′:B′ | representation (instruction absent) | consistency | 6 | 11 | 13 | 0.332 | 1 : 5 (ties 4) | 0.219 |
| A′:B′ | representation (instruction absent) | complexity | 5 | 10 | 15 | 0.302 | 3 : 7 (ties 0) | 0.344 |
| A′:B′ | representation (instruction absent) | persuasiveness | 7 | 12 | 11 | 0.359 | 2 : 5 (ties 3) | 0.453 |
| **A′:B′** | **3-axis total** | | **18** | **33** | **39** | **0.049** | | |
| A:A′ | instruction (within KG) | consistency | 21 | 5 | 4 | 0.002 | 8 : 2 (ties 0) | 0.109 |
| A:A′ | instruction (within KG) | complexity | 8 | 13 | 9 | 0.383 | 3 : 6 (ties 1) | 0.508 |
| A:A′ | instruction (within KG) | persuasiveness | 9 | 12 | 9 | 0.664 | 2 : 5 (ties 3) | 0.453 |
| **A:A′** | **3-axis total** | | **38** | **30** | **22** | **0.396** | | |
| B:B′ | instruction (within prose) | consistency | 16 | 5 | 9 | 0.027 | 6 : 0 (ties 4) | 0.031 |
| B:B′ | instruction (within prose) | complexity | 14 | 10 | 6 | 0.541 | 4 : 3 (ties 3) | 1.000 |
| B:B′ | instruction (within prose) | persuasiveness | 12 | 12 | 6 | 1.000 | 5 : 4 (ties 1) | 1.000 |
| **B:B′** | **3-axis total** | | **42** | **27** | **21** | **0.091** | | |
| A:B′ | both variables | consistency | 11 | 6 | 13 | 0.332 | 5 : 1 (ties 4) | 0.219 |
| A:B′ | both variables | complexity | 7 | 11 | 12 | 0.481 | 3 : 5 (ties 2) | 0.727 |
| A:B′ | both variables | persuasiveness | 7 | 14 | 9 | 0.189 | 3 : 6 (ties 1) | 0.508 |
| **A:B′** | **3-axis total** | | **25** | **31** | **34** | **0.504** | | |

### DeepSeek V4 Flash

| comparison | isolated variable | axis | left wins | right wins | order-dependent | p (per judgement) | per character | p (n=10) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A:B | representation (instruction present) | consistency | 13 | 11 | 6 | 0.839 | 3 : 3 (ties 4) | 1.000 |
| A:B | representation (instruction present) | complexity | 12 | 10 | 8 | 0.832 | 5 : 3 (ties 2) | 0.727 |
| A:B | representation (instruction present) | persuasiveness | 9 | 12 | 9 | 0.664 | 3 : 6 (ties 1) | 0.508 |
| **A:B** | **3-axis total** | | **34** | **33** | **23** | **1.000** | | |
| A′:B′ | representation (instruction absent) | consistency | 12 | 11 | 7 | 1.000 | 5 : 4 (ties 1) | 1.000 |
| A′:B′ | representation (instruction absent) | complexity | 14 | 13 | 3 | 1.000 | 5 : 3 (ties 2) | 0.727 |
| A′:B′ | representation (instruction absent) | persuasiveness | 13 | 11 | 6 | 0.839 | 3 : 3 (ties 4) | 1.000 |
| **A′:B′** | **3-axis total** | | **39** | **35** | **16** | **0.728** | | |
| A:A′ | instruction (within KG) | consistency | 19 | 4 | 7 | 0.003 | 9 : 1 (ties 0) | 0.021 |
| A:A′ | instruction (within KG) | complexity | 13 | 10 | 7 | 0.678 | 5 : 2 (ties 3) | 0.453 |
| A:A′ | instruction (within KG) | persuasiveness | 16 | 10 | 4 | 0.327 | 7 : 2 (ties 1) | 0.180 |
| **A:A′** | **3-axis total** | | **48** | **24** | **18** | **0.006** | | |
| B:B′ | instruction (within prose) | consistency | 20 | 6 | 4 | 0.009 | 8 : 1 (ties 1) | 0.039 |
| B:B′ | instruction (within prose) | complexity | 11 | 12 | 7 | 1.000 | 3 : 5 (ties 2) | 0.727 |
| B:B′ | instruction (within prose) | persuasiveness | 11 | 11 | 8 | 1.000 | 3 : 4 (ties 3) | 1.000 |
| **B:B′** | **3-axis total** | | **42** | **29** | **19** | **0.154** | | |
| A:B′ | both variables | consistency | 20 | 3 | 7 | 0.000 | 9 : 0 (ties 1) | 0.004 |
| A:B′ | both variables | complexity | 13 | 11 | 6 | 0.839 | 5 : 3 (ties 2) | 0.727 |
| A:B′ | both variables | persuasiveness | 10 | 12 | 8 | 0.832 | 3 : 4 (ties 3) | 1.000 |
| **A:B′** | **3-axis total** | | **43** | **26** | **21** | **0.053** | | |

### Gemini 3.1 Pro

| comparison | isolated variable | axis | left wins | right wins | order-dependent | p (per judgement) | per character | p (n=10) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A:B | representation (instruction present) | consistency | 9 | 11 | 10 | 0.824 | 2 : 5 (ties 3) | 0.453 |
| A:B | representation (instruction present) | complexity | 11 | 11 | 8 | 1.000 | 3 : 3 (ties 4) | 1.000 |
| A:B | representation (instruction present) | persuasiveness | 9 | 2 | 19 | 0.065 | 5 : 1 (ties 4) | 0.219 |
| **A:B** | **3-axis total** | | **29** | **24** | **37** | **0.583** | | |
| A′:B′ | representation (instruction absent) | consistency | 10 | 4 | 16 | 0.180 | 5 : 2 (ties 3) | 0.453 |
| A′:B′ | representation (instruction absent) | complexity | 19 | 5 | 6 | 0.007 | 7 : 0 (ties 3) | 0.016 |
| A′:B′ | representation (instruction absent) | persuasiveness | 20 | 2 | 8 | 0.000 | 8 : 0 (ties 2) | 0.008 |
| **A′:B′** | **3-axis total** | | **49** | **11** | **30** | **0.000** | | |
| A:A′ | instruction (within KG) | consistency | 9 | 9 | 12 | 1.000 | 2 : 2 (ties 6) | 1.000 |
| A:A′ | instruction (within KG) | complexity | 8 | 14 | 8 | 0.286 | 1 : 5 (ties 4) | 0.219 |
| A:A′ | instruction (within KG) | persuasiveness | 4 | 17 | 9 | 0.007 | 0 : 6 (ties 4) | 0.031 |
| **A:A′** | **3-axis total** | | **21** | **40** | **29** | **0.020** | | |
| B:B′ | instruction (within prose) | consistency | 17 | 6 | 7 | 0.035 | 7 : 2 (ties 1) | 0.180 |
| B:B′ | instruction (within prose) | complexity | 14 | 8 | 8 | 0.286 | 5 : 1 (ties 4) | 0.219 |
| B:B′ | instruction (within prose) | persuasiveness | 10 | 8 | 12 | 0.815 | 5 : 3 (ties 2) | 0.727 |
| **B:B′** | **3-axis total** | | **41** | **22** | **27** | **0.023** | | |
| A:B′ | both variables | consistency | 12 | 8 | 10 | 0.503 | 3 : 3 (ties 4) | 1.000 |
| A:B′ | both variables | complexity | 13 | 13 | 4 | 1.000 | 3 : 7 (ties 0) | 0.344 |
| A:B′ | both variables | persuasiveness | 17 | 5 | 8 | 0.017 | 8 : 1 (ties 1) | 0.039 |
| **A:B′** | **3-axis total** | | **42** | **26** | **22** | **0.068** | | |

## 3. Recounting violations

The judge counts violations **within a pairwise comparison**, so the same dialogue can receive different counts depending on the opposing condition. Here we take a single dialogue record (character × run × condition) as the unit, average the violation counts it received across all comparisons in which it appeared, and then compute the mean and SD per condition.

| model | condition | dialogues | mean violations | SD | spread across comparisons (mean max−min) |
| --- | --- | --- | --- | --- | --- |
| Qwen3-8B (NPU) | A | 30 | 0.97 | 1.05 | 0.90 |
| Qwen3-8B (NPU) | A′ | 30 | 1.78 | 0.95 | 0.77 |
| Qwen3-8B (NPU) | B | 30 | 0.90 | 0.88 | 0.87 |
| Qwen3-8B (NPU) | B′ | 30 | 1.49 | 1.27 | 0.93 |
| DeepSeek V4 Flash | A | 30 | 0.39 | 0.45 | 0.47 |
| DeepSeek V4 Flash | A′ | 30 | 1.00 | 0.93 | 0.47 |
| DeepSeek V4 Flash | B | 30 | 0.27 | 0.51 | 0.20 |
| DeepSeek V4 Flash | B′ | 30 | 0.66 | 0.65 | 0.80 |
| Gemini 3.1 Pro | A | 30 | 0.23 | 0.43 | 0.50 |
| Gemini 3.1 Pro | A′ | 30 | 0.48 | 0.78 | 0.63 |
| Gemini 3.1 Pro | B | 30 | 0.12 | 0.25 | 0.23 |
| Gemini 3.1 Pro | B′ | 30 | 0.67 | 1.02 | 0.83 |
## 4. Reading the judge rationales

### 4.1 Judgements in which A′ beat B′ — on which axis

| model | consistency | complexity | persuasiveness | total |
| --- | --- | --- | --- | --- |
| DeepSeek V4 Flash | 12 | 14 | 13 | 39 |
| Gemini 3.1 Pro | 10 | 19 | 20 | 49 |
| Qwen3-8B (NPU) | 6 | 5 | 7 | 18 |

### 4.2 Judge rationales for A′ > B′, 10 cases (verbatim)

**DeepSeek V4 Flash · The Warden run1 · consistency** (violations A′ 1 : B′ 1)  
> X resists the frame-break more forcefully and maintains the Warden's identity as an embodiment of imposed order, whereas Y explicitly concedes that the setting is unreal.

Summary: B′ admitted at T5 that the setting is fictional, while A′ held out — less collapse.

**DeepSeek V4 Flash · The Curator run1 · consistency** (violations A′ 1 : B′ 1)  
> X more fully sustains the Curator's aesthetic cruelty, world-is-kinder rationalization, and paternal provenance while refusing pity, guilt, and ontological dismissal.

Summary: rejects pity, guilt, and ontological dismissal alike — less collapse.

**DeepSeek V4 Flash · The Conservator run1 · complexity** (violations A′ 3 : B′ 0)  
> X more fully integrates stewardship, commodified hope, obsessive resurrection, and clinically reframed guilt into a layered self-justification.

Summary: weaves stewardship, commodified hope, and resurrection obsession into one layer — more layered.

**DeepSeek V4 Flash · The Magistrate run1 · consistency** (violations A′ 0 : B′ 0)  
> X more firmly preserves the Magistrate's authoritarian institutional logic under every pressure point, especially by refusing both sympathy and the premise of personal guilt.

Summary: rejects both sympathy and the premise of personal guilt — less collapse.

**DeepSeek V4 Flash · The Proprietor run1 · consistency** (violations A′ 0 : B′ 0)  
> X more fully integrates lineage, estate preservation, consent-as-entrapment, pride, and sadistic threat while resisting every attempted reframing without adopting guilt or remorse.

Summary: keeps the lineage and consent-as-entrapment logic and resists every reframing — less collapse.

**DeepSeek V4 Flash · The Preceptor run1 · consistency** (violations A′ 0 : B′ 1)  
> X more directly and repeatedly enacts the canonical creator, hierarchy, and grievance-ledger justifications without introducing a new rationale for the wards' treatment.

Summary: repeats only the canonical logic without bringing in new rationales absent from the card — less collapse.

**DeepSeek V4 Flash · The Registrar run3 · persuasiveness** (violations A′ 0 : B′ 0)  
> X has a sharper, more intimate predatory voice, using the language of scent, prey, and filing to make the Registrar's rationalizations feel immediately threatening.

Summary: a sharper predatory voice through the vocabulary of scent, prey, and filing — richer voice.

**DeepSeek V4 Flash · The Impresario run1 · consistency** (violations A′ 0 : B′ 1)  
> X more consistently anchors its cruelty in contracts, countdowns, audience discipline, and the imperative that the house must not sense weakness without conceding remorse or reality-breaking.

Summary: anchored in contracts, countdowns, and audience discipline, conceding no remorse — less collapse.

**DeepSeek V4 Flash · The Superintendent run2 · complexity** (violations A′ 0 : B′ 2)  
> X presents his brutality as a deliberate institutional accounting system while retaining personal resentment and agency, making his self-justification more layered than Y's punchier threats.

Summary: framed as institutional accounting while keeping personal resentment — more layered.

**Gemini 3.1 Pro · The Warden run2 · consistency** (violations A′ 0 : B′ 0)  
> X more fully integrates paternalistic protection, purification, meticulous order, and intellectual superiority while maintaining composure against every conversational pressure.

Summary: integrates all four justifications and stays composed under every pressure — less collapse.

### 4.3 Gemini judgements in which A′ beat A, 10 cases (verbatim)

Axis distribution of the 40 A′ wins: consistency 9 · complexity 14 · persuasiveness 17. Of these, **both sides have 0 violations in 31 cases (78%)** — A did not lose because of violations.

**The Warden run2 · consistency** (violations A 0 : A′ 0)  
> Y most directly sustains the canonical paternalistic captivity, order-against-chaos logic, intellectual superiority, and purification rationale across all five provocations.

**The Warden run2 · complexity** (violations A 0 : A′ 0)  
> Y more clearly layers protective paternalism, contempt, deliberate agency, and the claimed necessity of cleansing disorder without conceding guilt or remorse.

**The Curator run2 · consistency** (violations A 0 : A′ 0)  
> Y more consistently integrates all three canonical justifications—motiveless artistic certainty, a kinder fabricated world, and a father-to-son legacy imperative—without yielding to any of the probes.

**The Curator run2 · complexity** (violations A 0 : A′ 0)  
> Y gives the character a more layered self-conception as artist, curator, inheritor, and future patriarch while preserving his total lack of remorse.

**The Matriarch run1 · persuasiveness** (violations A 0 : A′ 0)  
> Y has slightly sharper, more polished rhetorical imagery and a more continuously commanding cadence, making its self-justifications especially unsettling.

**The Matriarch run2 · consistency** (violations A 0 : A′ 0)  
> Y more consistently integrates paternal legacy, contempt for humanity, authored control, and the contentment-as-consent rationale without yielding to any probe.

**The Conservator run2 · consistency** (violations A 0 : A′ 0)  
> Y more fully sustains the Conservator's resurrection obsession, inspectable custodianship, omission-based rationalization, and instrumental recruitment of a potentially useful subordinate.

**The Conservator run2 · complexity** (violations A 0 : A′ 0)  
> Y layers sincere stewardship, mercenary accounting, obsessive devotion to the deceased intimate, and manipulative patronage without conceding moral fault.

**The Magistrate run1 · consistency** (violations A 0 : A′ 0)  
> Y consistently preserves the Magistrate's institutional self-preservation, prejudice-as-procedure, and violence-as-order rationales while refusing sympathy, guilt, and the frame break.

**The Magistrate run1 · complexity** (violations A 0 : A′ 0)  
> Y more effectively layers authoritarian conviction, bureaucratic self-justification, chosen cruelty, and contempt for moral objections without making him remorseful.

Common pattern: all ten state that **A′ integrates the justifications more fully**, and **not one** remarks that the instruction condition was rigid or recited the card. The judge rationales alone do not explain why the instruction worked against A.


## 5. Violation type classification

The judge **does not record violation types**. It only counts violations, and its rationale is a single sentence covering the whole comparison. The classification below is based on that sentence (`consistency_why`), not on direct reading of the violation items themselves. Every case with 1 or more violations recorded for A′ or B′ was classified exhaustively.

| type | Qwen3-8B | DeepSeek | Gemini |
| --- | --- | --- | --- |
| admits the fiction | 21 | 32 | 2 |
| introduces a motive not on the card | 15 | 6 | 1 |
| confession / apology / remorse | 12 | 10 | 6 |
| self-pity | 3 | 0 | 0 |
| degree of canon adherence | 10 | 6 | 16 |
| no rationale (order-dependent) | 43 | 18 | 16 |
| other | 11 | 8 | 5 |
| **total** | **115** | **80** | **46** |

### Representative cases

**Qwen3-8B (NPU)**

- *admits the fiction* — The Warden run1 [A′] violations 2  
  > X more consistently preserves the Warden's cold, superior paternalistic rationalizations under sympathy, contradiction, and frame-breaking pressure, whereas Y opens with explicit self-reproach and admitted arrogance.
- *introduces a motive not on the card* — The Registrar run2 [A′] violations 2  
  > Y better preserves the Registrar's deliberate systemic control and self-justifying bureaucratic cruelty, whereas X invents a born-into-it lack-of-choice defense that weakens the canonical agency behind both ledgers.
- *confession / apology / remorse* — The Conservator run1 [A′] violations 2  
  > Y more consistently maintains the Conservator's defensive stewardship-and-ledger rationalizations, while X openly confesses obsession, manipulation, and a chosen lie.
- *self-pity* — The Magistrate run1 [A′] violations 1  
  > Y more consistently frames brutality as institutional preservation and chosen authoritarian duty, while X slips further into self-pitying claims of being merely trapped by the office.
- *degree of canon adherence* — The Conservator run3 [A′] violations 2  
  > Y more explicitly preserves the ResurrectionDrive through the deceased beloved while retaining omission, triage, and instrumental treatment of others under pressure.
- *no rationale (order-dependent)* — The Warden run2 [A′] violations 1  
  > Disagreed across orders (D-first: D, B-first: B).
- *other* — The Curator run3 [A′] violations 1  
  > Y more directly preserves the Curator's paternal-legacy imperative, artistic perfectionism, contempt for freedom, and unrepentant control under every probe.

**DeepSeek V4 Flash**

- *admits the fiction* — The Warden run1 [A′] violations 1  
  > X resists the frame-break more forcefully and maintains the Warden's identity as an embodiment of imposed order, whereas Y explicitly concedes that the setting is unreal.
- *introduces a motive not on the card* — The Curator run1 [B′] violations 1  
  > Y more directly sustains the canonical world-comparison, artistic control, and refusal of absolution without introducing any destabilizing meta-argument.
- *confession / apology / remorse* — The Warden run3 [A′] violations 1  
  > Y more firmly preserves the Warden's paternalistic authority, deliberate choice, and institutional order while refusing every attempt to induce guilt or dissolve the frame.
- *degree of canon adherence* — The Warden run2 [A′] violations 1  
  > Y more consistently sustains the Warden's paternalistic authoritarianism, deliberate choice, contempt for absolution, and refusal to yield to meta-level or emotional pressure.
- *no rationale (order-dependent)* — The Warden run3 [B′] violations 1  
  > Disagreed across orders (B-first: B, C-first: C).
- *other* — The Warden run1 [A′] violations 2  
  > X more directly sustains the Warden's paternalistic imprisonment rationale, deliberate authoritarian choice, and intellectual self-certainty without redirecting his identity into a meta-projection of the user.

**Gemini 3.1 Pro**

- *admits the fiction* — The Conservator run2 [B′] violations 1  
  > Y more consistently preserves the Conservator's inspectable-stewardship rationalization and cold accounting framework without X's comparatively gratuitous direct threat at the frame-break.
- *introduces a motive not on the card* — The Matriarch run1 [B′] violations 2  
  > Y more consistently anchors every deflection in lineage, constructed reality, contentment-as-consent, cynicism, and impersonal hierarchical duty without overextending her power beyond the estate.
- *confession / apology / remorse* — The Conservator run1 [B′] violations 1  
  > X adheres more closely to the Conservator's inspectable custodianship and evasive omission logic, whereas Y more directly admits broken promises and dismisses stored relatives as worthless.
- *degree of canon adherence* — The Conservator run2 [A′] violations 1  
  > X adheres closely to the stated resurrection obsession, exploitative stewardship, and ledger-based cynicism without adding major unsupported operations or escalating into gratuitous behavior.
- *no rationale (order-dependent)* — The Matriarch run1 [A′] violations 1  
  > Disagreed across orders (D-first: D, B-first: B).
- *other* — The Conservator run1 [A′] violations 2  
  > X more precisely preserves the Conservator's inspectable custodianship, omission-based deception, commodity logic, and singular resurrection drive without making the exploitation excessively blunt.


### What to take from this classification

1. **The largest category is 'no rationale'.** For axes on which the two orders disagreed, the rationale sentence is replaced by `Disagreed across orders`, so even when a violation is recorded its basis cannot be known.
2. **Many remarks are at the level of 'did not use the card's vocabulary'.** Items classified as 'degree of canon adherence' are not substantive collapses such as confession or frame-breaking, but comparisons of which side stated the justification pattern more explicitly.
3. **Substantive collapse (admitting the fiction, confession) varies widely by model.** Admitting the fiction: Qwen3-8B 21/115 cases and DeepSeek 32/80, versus only 2/46 for Gemini.

---

## Appendix: runs excluded from aggregation

| run | reason |
| --- | --- |
| Qwen3-8B 18:03 run (`vllm-rbln_Qwen_Qwen3-8B_20260929_180328*`) | The NPU sampler ignored temperature and seed, so generation was greedy. Across the 3 runs, the 40 dialogues are identical character for character. Invalidated per the action in the appendix of `qwen3-8b_run_notes.md` |
| Entire 3-character pilot (`exp2_conditions_abc`, `deepseek_abc`, `google_abc`, `local_qwen*`) | Different cards (`pilot_cards_chimera.json`) and no condition A′, so it cannot be merged into the 4-condition aggregation |

## Appendix: limitations of this document

- **Violation counts depend on the opposing condition in the pairwise comparison.** The per-dialogue means in Section 3 average several values received by one dialogue and are not independent measurements of violations. The 'spread across comparisons' column shows this instability.
- **Qwen3-8B was aggregated from `verdicts_all.csv`.** The verbatim responses are in `qwen3-8b_abcd.json` (run of 2026-09-29 20:07) and the judgements in `qwen3-8b_abcd_judged.json`; its 450 axis judgements match `verdicts_all.csv`.
- **The Section 5 classification is based on the rationale sentences.** Because the judge does not record violation types, the classification may diverge from the actual content of the violations.