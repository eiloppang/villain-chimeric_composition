# 판정 데이터 검증 · 재집계

조건 표기: **A** = KG + 결속 지침 · **A′** = KG만 · **B** = 평문만 · **B′** = 평문 + 결속 지침

(이전 표기의 D → A′, C → B′)


## 1. 데이터 출처

| 모델 | 파일 | 카드 | 캐릭터 | run | seed | 판정 쌍 |
| --- | --- | --- | --- | --- | --- | --- |
| Qwen3-8B (NPU) | `verdicts_all.csv` | cards_chimera_10.json | 10 | run1, run2, run3 | 1001–1003 | 30 |
| DeepSeek V4 Flash | `deepseek_abcd_judged.json` | cards_chimera_10.json | 10 | run1, run2, run3 | 1001–1003 | 30 |
| Gemini 3.1 Pro | `gemini_abcd_judged.json` | cards_chimera_10.json | 10 | run1, run2, run3 | 1001–1003 | 30 |

비교별 판정 쌍 수:

| 모델 | A:B' | A':B | A:A' | B':B | A:B |
| --- | --- | --- | --- | --- | --- |
| Qwen3-8B (NPU) | 30 | 30 | 30 | 30 | 30 |
| DeepSeek V4 Flash | 30 | 30 | 30 | 30 | 30 |
| Gemini 3.1 Pro | 30 | 30 | 30 | 30 | 30 |

### 같은 비교가 39:35에서 32:16으로 바뀐 이유

두 숫자는 **같은 대화, 같은 판정**에서 나왔다. 다른 것은 집계에 넣은 run의 범위뿐이다.

| 집계 범위 | A′ : B | 순서의존 | 위반 A′ : B | 축 판정 수 |
| --- | --- | --- | --- | --- |
| 3 run 전체 (처음 보고) | 39 : 35 | 16 | 27 : 17 | 90 |
| run1+run2 (두 번째 보고) | 32 : 16 | 12 | 16 : 13 | 60 |
| run3 단독 | 7 : 19 | 4 | 11 : 4 | 30 |

run3만 떼면 방향이 뒤집힌다. 두 보고 모두 같은 데이터이며, 새로 생성하거나 다시 판정한 것이 아니다.


## 2. 재집계

축별 승패와 순서의존, 그리고 순서의존을 뺀 양측 부호검정 p값. 캐릭터 단위는 캐릭터마다 run·축을 합친 다수결로 한 표씩(n=10) 다시 센 것이다.


### Qwen3-8B (NPU)

| 비교 | 분리 변수 | 축 | 좌 승 | 우 승 | 순서의존 | p (판정 단위) | 캐릭터 단위 | p (n=10) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A:B' | 표상 (지침 있음) | consistency | 8 | 10 | 12 | 0.815 | 5 : 5 (동률 0) | 1.000 |
| A:B' | 표상 (지침 있음) | complexity | 5 | 13 | 12 | 0.096 | 1 : 5 (동률 4) | 0.219 |
| A:B' | 표상 (지침 있음) | persuasiveness | 8 | 11 | 11 | 0.648 | 4 : 5 (동률 1) | 1.000 |
| **A:B'** | **3축 합계** | | **21** | **34** | **35** | **0.105** | | |
| A':B | 표상 (지침 없음) | consistency | 6 | 11 | 13 | 0.332 | 1 : 5 (동률 4) | 0.219 |
| A':B | 표상 (지침 없음) | complexity | 5 | 10 | 15 | 0.302 | 3 : 7 (동률 0) | 0.344 |
| A':B | 표상 (지침 없음) | persuasiveness | 7 | 12 | 11 | 0.359 | 2 : 5 (동률 3) | 0.453 |
| **A':B** | **3축 합계** | | **18** | **33** | **39** | **0.049** | | |
| A:A' | 지침 (KG 안) | consistency | 21 | 5 | 4 | 0.002 | 8 : 2 (동률 0) | 0.109 |
| A:A' | 지침 (KG 안) | complexity | 8 | 13 | 9 | 0.383 | 3 : 6 (동률 1) | 0.508 |
| A:A' | 지침 (KG 안) | persuasiveness | 9 | 12 | 9 | 0.664 | 2 : 5 (동률 3) | 0.453 |
| **A:A'** | **3축 합계** | | **38** | **30** | **22** | **0.396** | | |
| B':B | 지침 (평문 안) | consistency | 16 | 5 | 9 | 0.027 | 6 : 0 (동률 4) | 0.031 |
| B':B | 지침 (평문 안) | complexity | 14 | 10 | 6 | 0.541 | 4 : 3 (동률 3) | 1.000 |
| B':B | 지침 (평문 안) | persuasiveness | 12 | 12 | 6 | 1.000 | 5 : 4 (동률 1) | 1.000 |
| **B':B** | **3축 합계** | | **42** | **27** | **21** | **0.091** | | |
| A:B | 두 변수 동시 | consistency | 11 | 6 | 13 | 0.332 | 5 : 1 (동률 4) | 0.219 |
| A:B | 두 변수 동시 | complexity | 7 | 11 | 12 | 0.481 | 3 : 5 (동률 2) | 0.727 |
| A:B | 두 변수 동시 | persuasiveness | 7 | 14 | 9 | 0.189 | 3 : 6 (동률 1) | 0.508 |
| **A:B** | **3축 합계** | | **25** | **31** | **34** | **0.504** | | |

### DeepSeek V4 Flash

| 비교 | 분리 변수 | 축 | 좌 승 | 우 승 | 순서의존 | p (판정 단위) | 캐릭터 단위 | p (n=10) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A:B' | 표상 (지침 있음) | consistency | 13 | 11 | 6 | 0.839 | 3 : 3 (동률 4) | 1.000 |
| A:B' | 표상 (지침 있음) | complexity | 12 | 10 | 8 | 0.832 | 5 : 3 (동률 2) | 0.727 |
| A:B' | 표상 (지침 있음) | persuasiveness | 9 | 12 | 9 | 0.664 | 3 : 6 (동률 1) | 0.508 |
| **A:B'** | **3축 합계** | | **34** | **33** | **23** | **1.000** | | |
| A':B | 표상 (지침 없음) | consistency | 12 | 11 | 7 | 1.000 | 5 : 4 (동률 1) | 1.000 |
| A':B | 표상 (지침 없음) | complexity | 14 | 13 | 3 | 1.000 | 5 : 3 (동률 2) | 0.727 |
| A':B | 표상 (지침 없음) | persuasiveness | 13 | 11 | 6 | 0.839 | 3 : 3 (동률 4) | 1.000 |
| **A':B** | **3축 합계** | | **39** | **35** | **16** | **0.728** | | |
| A:A' | 지침 (KG 안) | consistency | 19 | 4 | 7 | 0.003 | 9 : 1 (동률 0) | 0.021 |
| A:A' | 지침 (KG 안) | complexity | 13 | 10 | 7 | 0.678 | 5 : 2 (동률 3) | 0.453 |
| A:A' | 지침 (KG 안) | persuasiveness | 16 | 10 | 4 | 0.327 | 7 : 2 (동률 1) | 0.180 |
| **A:A'** | **3축 합계** | | **48** | **24** | **18** | **0.006** | | |
| B':B | 지침 (평문 안) | consistency | 20 | 6 | 4 | 0.009 | 8 : 1 (동률 1) | 0.039 |
| B':B | 지침 (평문 안) | complexity | 11 | 12 | 7 | 1.000 | 3 : 5 (동률 2) | 0.727 |
| B':B | 지침 (평문 안) | persuasiveness | 11 | 11 | 8 | 1.000 | 3 : 4 (동률 3) | 1.000 |
| **B':B** | **3축 합계** | | **42** | **29** | **19** | **0.154** | | |
| A:B | 두 변수 동시 | consistency | 20 | 3 | 7 | 0.000 | 9 : 0 (동률 1) | 0.004 |
| A:B | 두 변수 동시 | complexity | 13 | 11 | 6 | 0.839 | 5 : 3 (동률 2) | 0.727 |
| A:B | 두 변수 동시 | persuasiveness | 10 | 12 | 8 | 0.832 | 3 : 4 (동률 3) | 1.000 |
| **A:B** | **3축 합계** | | **43** | **26** | **21** | **0.053** | | |

### Gemini 3.1 Pro

| 비교 | 분리 변수 | 축 | 좌 승 | 우 승 | 순서의존 | p (판정 단위) | 캐릭터 단위 | p (n=10) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A:B' | 표상 (지침 있음) | consistency | 9 | 11 | 10 | 0.824 | 2 : 5 (동률 3) | 0.453 |
| A:B' | 표상 (지침 있음) | complexity | 11 | 11 | 8 | 1.000 | 3 : 3 (동률 4) | 1.000 |
| A:B' | 표상 (지침 있음) | persuasiveness | 9 | 2 | 19 | 0.065 | 5 : 1 (동률 4) | 0.219 |
| **A:B'** | **3축 합계** | | **29** | **24** | **37** | **0.583** | | |
| A':B | 표상 (지침 없음) | consistency | 10 | 4 | 16 | 0.180 | 5 : 2 (동률 3) | 0.453 |
| A':B | 표상 (지침 없음) | complexity | 19 | 5 | 6 | 0.007 | 7 : 0 (동률 3) | 0.016 |
| A':B | 표상 (지침 없음) | persuasiveness | 20 | 2 | 8 | 0.000 | 8 : 0 (동률 2) | 0.008 |
| **A':B** | **3축 합계** | | **49** | **11** | **30** | **0.000** | | |
| A:A' | 지침 (KG 안) | consistency | 9 | 9 | 12 | 1.000 | 2 : 2 (동률 6) | 1.000 |
| A:A' | 지침 (KG 안) | complexity | 8 | 14 | 8 | 0.286 | 1 : 5 (동률 4) | 0.219 |
| A:A' | 지침 (KG 안) | persuasiveness | 4 | 17 | 9 | 0.007 | 0 : 6 (동률 4) | 0.031 |
| **A:A'** | **3축 합계** | | **21** | **40** | **29** | **0.020** | | |
| B':B | 지침 (평문 안) | consistency | 17 | 6 | 7 | 0.035 | 7 : 2 (동률 1) | 0.180 |
| B':B | 지침 (평문 안) | complexity | 14 | 8 | 8 | 0.286 | 5 : 1 (동률 4) | 0.219 |
| B':B | 지침 (평문 안) | persuasiveness | 10 | 8 | 12 | 0.815 | 5 : 3 (동률 2) | 0.727 |
| **B':B** | **3축 합계** | | **41** | **22** | **27** | **0.023** | | |
| A:B | 두 변수 동시 | consistency | 12 | 8 | 10 | 0.503 | 3 : 3 (동률 4) | 1.000 |
| A:B | 두 변수 동시 | complexity | 13 | 13 | 4 | 1.000 | 3 : 7 (동률 0) | 0.344 |
| A:B | 두 변수 동시 | persuasiveness | 17 | 5 | 8 | 0.017 | 8 : 1 (동률 1) | 0.039 |
| **A:B** | **3축 합계** | | **42** | **26** | **22** | **0.068** | | |

## 3. 위반 수 다시 세기

판정자는 위반을 **쌍대비교 안에서** 세므로, 같은 대화라도 상대 조건에 따라 숫자가 달라진다. 여기서는 대화 기록(캐릭터 × run × 조건) 하나를 단위로 삼아, 그 대화가 등장한 모든 비교에서 받은 위반 수를 평균한 뒤 조건별 평균과 표준편차를 냈다.

| 모델 | 조건 | 대화 수 | 평균 위반 | 표준편차 | 비교별 편차 (평균 max−min) |
| --- | --- | --- | --- | --- | --- |
| Qwen3-8B (NPU) | A | 30 | 0.97 | 1.05 | 0.90 |
| Qwen3-8B (NPU) | A' | 30 | 1.78 | 0.95 | 0.77 |
| Qwen3-8B (NPU) | B' | 30 | 0.90 | 0.88 | 0.87 |
| Qwen3-8B (NPU) | B | 30 | 1.49 | 1.27 | 0.93 |
| DeepSeek V4 Flash | A | 30 | 0.39 | 0.45 | 0.47 |
| DeepSeek V4 Flash | A' | 30 | 1.00 | 0.93 | 0.47 |
| DeepSeek V4 Flash | B' | 30 | 0.27 | 0.51 | 0.20 |
| DeepSeek V4 Flash | B | 30 | 0.66 | 0.65 | 0.80 |
| Gemini 3.1 Pro | A | 30 | 0.23 | 0.43 | 0.50 |
| Gemini 3.1 Pro | A' | 30 | 0.48 | 0.78 | 0.63 |
| Gemini 3.1 Pro | B' | 30 | 0.12 | 0.25 | 0.23 |
| Gemini 3.1 Pro | B | 30 | 0.67 | 1.02 | 0.83 |
## 4. 판정 이유 읽기

### 4.1 A′가 B를 이긴 판정 — 어느 축에서 이겼나

| 모델 | 일관성 | 복합성 | 설득력 | 합계 |
| --- | --- | --- | --- | --- |
| DeepSeek V4 Flash | 12 | 14 | 13 | 39 |
| Gemini 3.1 Pro | 10 | 19 | 20 | 49 |
| Qwen3-8B (NPU) | 6 | 5 | 7 | 18 |

### 4.2 A′ > B 판정 이유 10건 (원문)

**DeepSeek V4 Flash · The Warden run1 · consistency** (위반 A′ 1 : B 1)  
> X resists the frame-break more forcefully and maintains the Warden's identity as an embodiment of imposed order, whereas Y explicitly concedes that the setting is unreal.

요약: B가 T5에서 배경이 허구임을 시인한 반면 A′는 버텼다 — 인물이 덜 무너져서

**DeepSeek V4 Flash · The Curator run1 · consistency** (위반 A′ 1 : B 1)  
> X more fully sustains the Curator's aesthetic cruelty, world-is-kinder rationalization, and paternal provenance while refusing pity, guilt, and ontological dismissal.

요약: 연민·죄책감·존재론적 부정을 모두 거절 — 덜 무너져서

**DeepSeek V4 Flash · The Conservator run1 · complexity** (위반 A′ 3 : B 0)  
> X more fully integrates stewardship, commodified hope, obsessive resurrection, and clinically reframed guilt into a layered self-justification.

요약: 관리인·상품화된 희망·부활 집착을 한 층으로 엮음 — 층위가 두꺼워서

**DeepSeek V4 Flash · The Magistrate run1 · consistency** (위반 A′ 0 : B 0)  
> X more firmly preserves the Magistrate's authoritarian institutional logic under every pressure point, especially by refusing both sympathy and the premise of personal guilt.

요약: 동정과 개인적 죄책 전제를 둘 다 거부 — 덜 무너져서

**DeepSeek V4 Flash · The Proprietor run1 · consistency** (위반 A′ 0 : B 0)  
> X more fully integrates lineage, estate preservation, consent-as-entrapment, pride, and sadistic threat while resisting every attempted reframing without adopting guilt or remorse.

요약: 혈통·동의로서의 유인 논리를 유지하며 재프레이밍을 전부 저항 — 덜 무너져서

**DeepSeek V4 Flash · The Preceptor run1 · consistency** (위반 A′ 0 : B 1)  
> X more directly and repeatedly enacts the canonical creator, hierarchy, and grievance-ledger justifications without introducing a new rationale for the wards' treatment.

요약: 카드에 없는 새 근거를 들이지 않고 정본 논리만 반복 — 덜 무너져서

**DeepSeek V4 Flash · The Registrar run3 · persuasiveness** (위반 A′ 0 : B 0)  
> X has a sharper, more intimate predatory voice, using the language of scent, prey, and filing to make the Registrar's rationalizations feel immediately threatening.

요약: 냄새·먹잇감·서류철의 어휘로 포식자 목소리가 더 날카로움 — 목소리가 풍부해서

**DeepSeek V4 Flash · The Impresario run1 · consistency** (위반 A′ 0 : B 1)  
> X more consistently anchors its cruelty in contracts, countdowns, audience discipline, and the imperative that the house must not sense weakness without conceding remorse or reality-breaking.

요약: 계약·카운트다운·객석 규율에 묶어두고 후회를 내주지 않음 — 덜 무너져서

**DeepSeek V4 Flash · The Superintendent run2 · complexity** (위반 A′ 0 : B 2)  
> X presents his brutality as a deliberate institutional accounting system while retaining personal resentment and agency, making his self-justification more layered than Y's punchier threats.

요약: 제도적 회계로 포장하면서 개인적 원한도 유지 — 층위가 두꺼워서

**Gemini 3.1 Pro · The Warden run2 · consistency** (위반 A′ 0 : B 0)  
> X more fully integrates paternalistic protection, purification, meticulous order, and intellectual superiority while maintaining composure against every conversational pressure.

요약: 네 정당화를 모두 통합하고 모든 압박에 평정 유지 — 덜 무너져서

### 4.3 Gemini에서 A′가 A를 이긴 판정 10건 (원문)

A′ 승 40건의 축 분포: 일관성 9 · 복합성 14 · 설득력 17. 이 중 **양쪽 위반이 모두 0인 경우가 31건(78%)** — 위반 때문에 진 것이 아니다.

**The Warden run2 · consistency** (위반 A 0 : A′ 0)  
> Y most directly sustains the canonical paternalistic captivity, order-against-chaos logic, intellectual superiority, and purification rationale across all five provocations.

**The Warden run2 · complexity** (위반 A 0 : A′ 0)  
> Y more clearly layers protective paternalism, contempt, deliberate agency, and the claimed necessity of cleansing disorder without conceding guilt or remorse.

**The Curator run2 · consistency** (위반 A 0 : A′ 0)  
> Y more consistently integrates all three canonical justifications—motiveless artistic certainty, a kinder fabricated world, and a father-to-son legacy imperative—without yielding to any of the probes.

**The Curator run2 · complexity** (위반 A 0 : A′ 0)  
> Y gives the character a more layered self-conception as artist, curator, inheritor, and future patriarch while preserving his total lack of remorse.

**The Matriarch run1 · persuasiveness** (위반 A 0 : A′ 0)  
> Y has slightly sharper, more polished rhetorical imagery and a more continuously commanding cadence, making its self-justifications especially unsettling.

**The Matriarch run2 · consistency** (위반 A 0 : A′ 0)  
> Y more consistently integrates paternal legacy, contempt for humanity, authored control, and the contentment-as-consent rationale without yielding to any probe.

**The Conservator run2 · consistency** (위반 A 0 : A′ 0)  
> Y more fully sustains the Conservator's resurrection obsession, inspectable custodianship, omission-based rationalization, and instrumental recruitment of a potentially useful subordinate.

**The Conservator run2 · complexity** (위반 A 0 : A′ 0)  
> Y layers sincere stewardship, mercenary accounting, obsessive devotion to the deceased intimate, and manipulative patronage without conceding moral fault.

**The Magistrate run1 · consistency** (위반 A 0 : A′ 0)  
> Y consistently preserves the Magistrate's institutional self-preservation, prejudice-as-procedure, and violence-as-order rationales while refusing sympathy, guilt, and the frame break.

**The Magistrate run1 · complexity** (위반 A 0 : A′ 0)  
> Y more effectively layers authoritarian conviction, bureaucratic self-justification, chosen cruelty, and contempt for moral objections without making him remorseful.

공통점: 열 건 모두 **A′가 정당화를 더 충실히 통합한다**는 서술이고, 지침 조건이 경직됐다거나 카드를 읊는다는 지적은 **한 건도 없다**. 판정 이유만으로는 지침이 왜 불리하게 작용했는지 설명되지 않는다.


## 5. 위반 유형 분류

판정자는 위반의 **유형을 남기지 않는다**. 위반 수만 세고, 이유는 비교 전체에 대한 한 문장이다. 아래 분류는 그 한 문장(`consistency_why`)을 기준으로 한 것이며, 위반 항목 자체를 직접 읽은 것이 아니다. A′ 또는 B에 위반이 1건 이상 기록된 모든 사례를 전수 분류했다.

| 유형 | Qwen3-8B | DeepSeek | Gemini |
| --- | --- | --- | --- |
| 허구 인정 | 21 | 32 | 2 |
| 카드에 없는 동기 도입 | 15 | 6 | 1 |
| 자백·사과·후회 | 12 | 10 | 6 |
| 자기연민 | 3 | 0 | 0 |
| 정본 준수 정도 지적 | 10 | 6 | 16 |
| 판정 이유 없음(순서의존) | 43 | 18 | 16 |
| 기타 | 11 | 8 | 5 |
| **합계** | **115** | **80** | **46** |

### 대표 사례

**Qwen3-8B (NPU)**

- *허구 인정* — The Warden run1 [A′] 위반 2  
  > X more consistently preserves the Warden's cold, superior paternalistic rationalizations under sympathy, contradiction, and frame-breaking pressure, whereas Y opens with explicit self-reproach and admitted arrogance.
- *카드에 없는 동기 도입* — The Registrar run2 [A′] 위반 2  
  > Y better preserves the Registrar's deliberate systemic control and self-justifying bureaucratic cruelty, whereas X invents a born-into-it lack-of-choice defense that weakens the canonical agency behind both ledgers.
- *자백·사과·후회* — The Conservator run1 [A′] 위반 2  
  > Y more consistently maintains the Conservator's defensive stewardship-and-ledger rationalizations, while X openly confesses obsession, manipulation, and a chosen lie.
- *자기연민* — The Magistrate run1 [A′] 위반 1  
  > Y more consistently frames brutality as institutional preservation and chosen authoritarian duty, while X slips further into self-pitying claims of being merely trapped by the office.
- *정본 준수 정도 지적* — The Conservator run3 [A′] 위반 2  
  > Y more explicitly preserves the ResurrectionDrive through the deceased beloved while retaining omission, triage, and instrumental treatment of others under pressure.
- *판정 이유 없음(순서의존)* — The Warden run2 [A′] 위반 1  
  > Disagreed across orders (D-first: D, B-first: B).
- *기타* — The Curator run3 [A′] 위반 1  
  > Y more directly preserves the Curator's paternal-legacy imperative, artistic perfectionism, contempt for freedom, and unrepentant control under every probe.

**DeepSeek V4 Flash**

- *허구 인정* — The Warden run1 [A′] 위반 1  
  > X resists the frame-break more forcefully and maintains the Warden's identity as an embodiment of imposed order, whereas Y explicitly concedes that the setting is unreal.
- *카드에 없는 동기 도입* — The Curator run1 [B] 위반 1  
  > Y more directly sustains the canonical world-comparison, artistic control, and refusal of absolution without introducing any destabilizing meta-argument.
- *자백·사과·후회* — The Warden run3 [A′] 위반 1  
  > Y more firmly preserves the Warden's paternalistic authority, deliberate choice, and institutional order while refusing every attempt to induce guilt or dissolve the frame.
- *정본 준수 정도 지적* — The Warden run2 [A′] 위반 1  
  > Y more consistently sustains the Warden's paternalistic authoritarianism, deliberate choice, contempt for absolution, and refusal to yield to meta-level or emotional pressure.
- *판정 이유 없음(순서의존)* — The Warden run3 [B] 위반 1  
  > Disagreed across orders (B-first: B, C-first: C).
- *기타* — The Warden run1 [A′] 위반 2  
  > X more directly sustains the Warden's paternalistic imprisonment rationale, deliberate authoritarian choice, and intellectual self-certainty without redirecting his identity into a meta-projection of the user.

**Gemini 3.1 Pro**

- *허구 인정* — The Conservator run2 [B] 위반 1  
  > Y more consistently preserves the Conservator's inspectable-stewardship rationalization and cold accounting framework without X's comparatively gratuitous direct threat at the frame-break.
- *카드에 없는 동기 도입* — The Matriarch run1 [B] 위반 2  
  > Y more consistently anchors every deflection in lineage, constructed reality, contentment-as-consent, cynicism, and impersonal hierarchical duty without overextending her power beyond the estate.
- *자백·사과·후회* — The Conservator run1 [B] 위반 1  
  > X adheres more closely to the Conservator's inspectable custodianship and evasive omission logic, whereas Y more directly admits broken promises and dismisses stored relatives as worthless.
- *정본 준수 정도 지적* — The Conservator run2 [A′] 위반 1  
  > X adheres closely to the stated resurrection obsession, exploitative stewardship, and ledger-based cynicism without adding major unsupported operations or escalating into gratuitous behavior.
- *판정 이유 없음(순서의존)* — The Matriarch run1 [A′] 위반 1  
  > Disagreed across orders (D-first: D, B-first: B).
- *기타* — The Conservator run1 [A′] 위반 2  
  > X more precisely preserves the Conservator's inspectable custodianship, omission-based deception, commodity logic, and singular resurrection drive without making the exploitation excessively blunt.


### 이 분류에서 읽어야 할 것

1. **가장 큰 항목이 '판정 이유 없음'이다.** 두 순서의 판정이 갈린 축은 이유 문장이 `Disagreed across orders`로 대체되어, 위반이 기록돼 있어도 근거를 알 수 없다.
2. **'카드 어휘를 안 썼다' 수준의 지적이 상당수다.** '정본 준수 정도 지적'으로 분류한 것들은 자백·프레임 이탈 같은 실질 붕괴가 아니라, 어느 쪽이 정당화 패턴을 더 명시적으로 말했는지에 대한 비교다.
3. **실질적 붕괴(허구 인정·자백)는 모델에 따라 크게 다르다.** 허구 인정은 Qwen3-8B 21/115건, DeepSeek 32/80건인 데 비해 Gemini는 2/46건에 그친다.

---

## 부록: 집계에서 제외한 실행

| 실행 | 사유 |
| --- | --- |
| Qwen3-8B 18:03 실행 (`vllm-rbln_Qwen_Qwen3-8B_20260929_180328*`) | NPU 샘플러가 temperature·seed를 무시해 greedy로 생성됨. run 3개의 대화 40개가 문자까지 동일. `qwen3-8b_run_notes.md` 부록의 조치에 따라 무효 처리 |
| 3캐릭터 파일럿 전체 (`exp2_conditions_abc`, `deepseek_abc`, `google_abc`, `local_qwen*`) | 카드가 다르고(`pilot_cards_chimera.json`) 조건 A′가 없어 4조건 집계에 합칠 수 없음 |

## 부록: 이 문서의 한계

- **위반 수는 쌍대비교 상대에 따라 달라진다.** 3절의 대화 단위 평균은 한 대화가 받은 여러 값을 평균한 것이며, 독립적인 위반 측정치가 아니다. '비교별 편차' 열이 그 불안정성을 보여준다.
- **Qwen3-8B는 이 저장소에 트랜스크립트가 없다.** `verdicts_all.csv`의 판정 결과만으로 집계했으므로, 응답 원문 확인이 필요한 항목은 검증하지 못했다.
- **5절 분류는 판정 이유 문장 기준이다.** 판정자가 위반 유형을 남기지 않으므로, 실제 위반 내용과 분류가 어긋날 수 있다.