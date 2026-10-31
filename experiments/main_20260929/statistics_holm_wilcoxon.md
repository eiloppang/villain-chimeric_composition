# Multiple-comparison correction · violation tests · order dependence

Condition labels (as in the paper): **A** = KG + binding instruction · **A′** = KG only · **B** = prose + binding instruction · **B′** = prose only. Data keys: A = `A`, A′ = `D`, B = `C`, B′ = `B`; the verbatim judge strings `Disagreed across orders (…)` use the data keys.

The data are the same as in `verification_reaggregation.md` (30 pairs per model, 10 characters × 3 runs).


## 1. Holm correction

Families were defined separately for each model. **Representation effect** = A:B·A′:B′ × 3 axes = 6 tests; **binding effect** = A:A′·B:B′ × 3 axes = 6 tests. Per-judgement and per-character (n=10) analyses were corrected separately. `statsmodels.stats.multitest.multipletests(method='holm')`, α=0.05.


### Qwen3-8B (NPU)


**Representation effect · per judgement**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:B | consistency | 8 : 10 | 18 | 0.8145 | 1.0000 | no |
| A:B | complexity | 5 : 13 | 18 | 0.0963 | 0.5775 | no |
| A:B | persuasiveness | 8 : 11 | 19 | 0.6476 | 1.0000 | no |
| A′:B′ | consistency | 6 : 11 | 17 | 0.3323 | 1.0000 | no |
| A′:B′ | complexity | 5 : 10 | 15 | 0.3018 | 1.0000 | no |
| A′:B′ | persuasiveness | 7 : 12 | 19 | 0.3593 | 1.0000 | no |

**Representation effect · per character (n=10)**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:B | consistency | 5 : 5 (ties 0) | 10 | 1.0000 | 1.0000 | no |
| A:B | complexity | 1 : 5 (ties 4) | 6 | 0.2188 | 1.0000 | no |
| A:B | persuasiveness | 4 : 5 (ties 1) | 9 | 1.0000 | 1.0000 | no |
| A′:B′ | consistency | 1 : 5 (ties 4) | 6 | 0.2188 | 1.0000 | no |
| A′:B′ | complexity | 3 : 7 (ties 0) | 10 | 0.3438 | 1.0000 | no |
| A′:B′ | persuasiveness | 2 : 5 (ties 3) | 7 | 0.4531 | 1.0000 | no |

**Binding effect · per judgement**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:A′ | consistency | 21 : 5 | 26 | 0.0025 | 0.0150 | **yes** |
| A:A′ | complexity | 8 : 13 | 21 | 0.3833 | 1.0000 | no |
| A:A′ | persuasiveness | 9 : 12 | 21 | 0.6636 | 1.0000 | no |
| B:B′ | consistency | 16 : 5 | 21 | 0.0266 | 0.1330 | no |
| B:B′ | complexity | 14 : 10 | 24 | 0.5413 | 1.0000 | no |
| B:B′ | persuasiveness | 12 : 12 | 24 | 1.0000 | 1.0000 | no |

**Binding effect · per character (n=10)**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:A′ | consistency | 8 : 2 (ties 0) | 10 | 0.1094 | 0.5469 | no |
| A:A′ | complexity | 3 : 6 (ties 1) | 9 | 0.5078 | 1.0000 | no |
| A:A′ | persuasiveness | 2 : 5 (ties 3) | 7 | 0.4531 | 1.0000 | no |
| B:B′ | consistency | 6 : 0 (ties 4) | 6 | 0.0312 | 0.1875 | no |
| B:B′ | complexity | 4 : 3 (ties 3) | 7 | 1.0000 | 1.0000 | no |
| B:B′ | persuasiveness | 5 : 4 (ties 1) | 9 | 1.0000 | 1.0000 | no |

### DeepSeek V4 Flash


**Representation effect · per judgement**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:B | consistency | 13 : 11 | 24 | 0.8388 | 1.0000 | no |
| A:B | complexity | 12 : 10 | 22 | 0.8318 | 1.0000 | no |
| A:B | persuasiveness | 9 : 12 | 21 | 0.6636 | 1.0000 | no |
| A′:B′ | consistency | 12 : 11 | 23 | 1.0000 | 1.0000 | no |
| A′:B′ | complexity | 14 : 13 | 27 | 1.0000 | 1.0000 | no |
| A′:B′ | persuasiveness | 13 : 11 | 24 | 0.8388 | 1.0000 | no |

**Representation effect · per character (n=10)**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:B | consistency | 3 : 3 (ties 4) | 6 | 1.0000 | 1.0000 | no |
| A:B | complexity | 5 : 3 (ties 2) | 8 | 0.7266 | 1.0000 | no |
| A:B | persuasiveness | 3 : 6 (ties 1) | 9 | 0.5078 | 1.0000 | no |
| A′:B′ | consistency | 5 : 4 (ties 1) | 9 | 1.0000 | 1.0000 | no |
| A′:B′ | complexity | 5 : 3 (ties 2) | 8 | 0.7266 | 1.0000 | no |
| A′:B′ | persuasiveness | 3 : 3 (ties 4) | 6 | 1.0000 | 1.0000 | no |

**Binding effect · per judgement**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:A′ | consistency | 19 : 4 | 23 | 0.0026 | 0.0156 | **yes** |
| A:A′ | complexity | 13 : 10 | 23 | 0.6776 | 1.0000 | no |
| A:A′ | persuasiveness | 16 : 10 | 26 | 0.3269 | 1.0000 | no |
| B:B′ | consistency | 20 : 6 | 26 | 0.0094 | 0.0468 | **yes** |
| B:B′ | complexity | 11 : 12 | 23 | 1.0000 | 1.0000 | no |
| B:B′ | persuasiveness | 11 : 11 | 22 | 1.0000 | 1.0000 | no |

**Binding effect · per character (n=10)**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:A′ | consistency | 9 : 1 (ties 0) | 10 | 0.0215 | 0.1289 | no |
| A:A′ | complexity | 5 : 2 (ties 3) | 7 | 0.4531 | 1.0000 | no |
| A:A′ | persuasiveness | 7 : 2 (ties 1) | 9 | 0.1797 | 0.7188 | no |
| B:B′ | consistency | 8 : 1 (ties 1) | 9 | 0.0391 | 0.1953 | no |
| B:B′ | complexity | 3 : 5 (ties 2) | 8 | 0.7266 | 1.0000 | no |
| B:B′ | persuasiveness | 3 : 4 (ties 3) | 7 | 1.0000 | 1.0000 | no |

### Gemini 3.1 Pro


**Representation effect · per judgement**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:B | consistency | 9 : 11 | 20 | 0.8238 | 1.0000 | no |
| A:B | complexity | 11 : 11 | 22 | 1.0000 | 1.0000 | no |
| A:B | persuasiveness | 9 : 2 | 11 | 0.0654 | 0.2617 | no |
| A′:B′ | consistency | 10 : 4 | 14 | 0.1796 | 0.5387 | no |
| A′:B′ | complexity | 19 : 5 | 24 | 0.0066 | 0.0331 | **yes** |
| A′:B′ | persuasiveness | 20 : 2 | 22 | 0.0001 | 0.0007 | **yes** |

**Representation effect · per character (n=10)**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:B | consistency | 2 : 5 (ties 3) | 7 | 0.4531 | 1.0000 | no |
| A:B | complexity | 3 : 3 (ties 4) | 6 | 1.0000 | 1.0000 | no |
| A:B | persuasiveness | 5 : 1 (ties 4) | 6 | 0.2188 | 0.8750 | no |
| A′:B′ | consistency | 5 : 2 (ties 3) | 7 | 0.4531 | 1.0000 | no |
| A′:B′ | complexity | 7 : 0 (ties 3) | 7 | 0.0156 | 0.0781 | no |
| A′:B′ | persuasiveness | 8 : 0 (ties 2) | 8 | 0.0078 | 0.0469 | **yes** |

**Binding effect · per judgement**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:A′ | consistency | 9 : 9 | 18 | 1.0000 | 1.0000 | no |
| A:A′ | complexity | 8 : 14 | 22 | 0.2863 | 1.0000 | no |
| A:A′ | persuasiveness | 4 : 17 | 21 | 0.0072 | 0.0432 | **yes** |
| B:B′ | consistency | 17 : 6 | 23 | 0.0347 | 0.1734 | no |
| B:B′ | complexity | 14 : 8 | 22 | 0.2863 | 1.0000 | no |
| B:B′ | persuasiveness | 10 : 8 | 18 | 0.8145 | 1.0000 | no |

**Binding effect · per character (n=10)**

| comparison | axis | wins | n | raw p | adjusted p | significant after correction |
| --- | --- | --- | --- | --- | --- | --- |
| A:A′ | consistency | 2 : 2 (ties 6) | 4 | 1.0000 | 1.0000 | no |
| A:A′ | complexity | 1 : 5 (ties 4) | 6 | 0.2188 | 0.8984 | no |
| A:A′ | persuasiveness | 0 : 6 (ties 4) | 6 | 0.0312 | 0.1875 | no |
| B:B′ | consistency | 7 : 2 (ties 1) | 9 | 0.1797 | 0.8984 | no |
| B:B′ | complexity | 5 : 1 (ties 4) | 6 | 0.2188 | 0.8984 | no |
| B:B′ | persuasiveness | 5 : 3 (ties 2) | 8 | 0.7266 | 1.0000 | no |

## 2. Violation-reduction test (Wilcoxon signed-rank)

Per-dialogue mean violations were paired by character × run. A dialogue's violation count is the mean of the values it received across all pairwise comparisons in which it appeared (not an independent measurement — see `verification_reaggregation.md` Section 3).

Because many pairs had a difference of 0, we used `zero_method='wilcox'` (0 differences are discarded and the remaining pairs are tested). Holm correction was applied per family, split into binding (2) and representation (2).


### Qwen3-8B (NPU)

| family | comparison | pairs | mean (left) | mean (right) | median diff. | zero-diff pairs | W | raw p | adjusted p | significant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| binding | A vs A′ | 30 | 0.967 | 1.783 | -0.750 | 3 | 65.5 | 0.0030 | 0.0060 | **yes** |
| binding | B vs B′ | 30 | 0.900 | 1.489 | -0.500 | 1 | 114.5 | 0.0259 | 0.0259 | **yes** |
| representation | A vs B | 30 | 0.967 | 0.900 | +0.000 | 3 | 182.0 | 0.8664 | 0.8664 | no |
| representation | A′ vs B′ | 30 | 1.783 | 1.489 | +0.417 | 2 | 99.5 | 0.0184 | 0.0367 | **yes** |

### DeepSeek V4 Flash

| family | comparison | pairs | mean (left) | mean (right) | median diff. | zero-diff pairs | W | raw p | adjusted p | significant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| binding | A vs A′ | 30 | 0.389 | 1.000 | -0.417 | 6 | 43.5 | 0.0023 | 0.0046 | **yes** |
| binding | B vs B′ | 30 | 0.267 | 0.656 | -0.333 | 7 | 46.5 | 0.0053 | 0.0053 | **yes** |
| representation | A vs B | 30 | 0.389 | 0.267 | +0.000 | 14 | 44.0 | 0.2124 | 0.4247 | no |
| representation | A′ vs B′ | 30 | 1.000 | 0.656 | +0.000 | 5 | 119.0 | 0.2413 | 0.4247 | no |

### Gemini 3.1 Pro

| family | comparison | pairs | mean (left) | mean (right) | median diff. | zero-diff pairs | W | raw p | adjusted p | significant |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| binding | A vs A′ | 30 | 0.233 | 0.483 | +0.000 | 16 | 18.0 | 0.0301 | 0.0301 | **yes** |
| binding | B vs B′ | 30 | 0.117 | 0.667 | -0.167 | 11 | 30.0 | 0.0087 | 0.0175 | **yes** |
| representation | A vs B | 30 | 0.233 | 0.117 | +0.000 | 17 | 30.5 | 0.2935 | 0.5869 | no |
| representation | A′ vs B′ | 30 | 0.483 | 0.667 | +0.000 | 12 | 61.5 | 0.2955 | 0.5869 | no |

## 3. Order-dependent judgement counts

Counts summed over the three axes. Each comparison has 90 axis judgements per model (10 characters × 3 runs × 3 axes).

| model | A:B | A′:B′ | A:A′ | B:B′ | A:B′ | total |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-8B (NPU) | 35 / 90 (39%) | 39 / 90 (43%) | 22 / 90 (24%) | 21 / 90 (23%) | 34 / 90 (38%) | 151 |
| DeepSeek V4 Flash | 23 / 90 (26%) | 16 / 90 (18%) | 18 / 90 (20%) | 19 / 90 (21%) | 21 / 90 (23%) | 97 |
| Gemini 3.1 Pro | 37 / 90 (41%) | 30 / 90 (33%) | 29 / 90 (32%) | 27 / 90 (30%) | 22 / 90 (24%) | 145 |

Order-dependent judgements are consistently more frequent in the representation-effect comparisons (A:B, A′:B′) than in the binding-effect comparisons (A:A′, B:B′). This indicates that the judge has difficulty distinguishing outputs from the two representations.
