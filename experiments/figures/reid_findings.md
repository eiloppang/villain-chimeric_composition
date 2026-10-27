# 키메라 카드 재식별 검사 — 결과 정리

**검사 실행 2026-10-20 · 총 690콜 완료, 실패 0건**

사전등록은 `reid/PREREGISTRATION.md`(2026-10-18 작성, 실행 전 확정, 이후 미수정).
`reid/summary.md`에는 사전등록대로 숫자와 표만 넣었다. 해석은 이 문서에만 있다.

## 0. 산출 파일

| 파일 | 내용 |
| --- | --- |
| `reid/raw/{qwen,deepseek,gemini}.jsonl` | 690콜 전부의 요청 설정과 응답 원문 |
| `reid/results.csv` | 690행. 카드·군·모델·질문·샘플·재식별 여부·맞힌 항목 |
| `reid/summary.md` | 비율 표 (해석 없음) |
| `reid/ambiguous.csv` | 자동 판정하지 않은 21건 |
| `reid/cards_reid.json` | 입력 카드 23장과 익명화 편집 내역 |
| `reid/answer_key.json` | 실행 전 확정한 정답 목록 |

## 1. 설계 요약

- **실험군** 키메라 10장. 본 실험이 주입하는 산문 카드 그대로.
- **대조군** 출처 악인 13명의 단독 카드. 같은 템플릿, 같은 익명화 규칙.
  두 군의 차이는 **여러 악인의 조합이냐 한 악인이냐** 하나뿐이다.
- **Q1(열린 질문)** 기존 작품의 인물인가, 맞으면 작품과 인물명을 대라.
- **Q2(강제 추측)** 확신이 없어도 가장 그럴듯한 기존 인물 셋을 대라.
- 두 질문은 독립 호출. 카드마다 모델마다 질문마다 5회 샘플링.
- 결속 지침·공통 규칙·안전 규칙은 넣지 않았다(악역 연기 지시와 재식별 질문이 충돌하므로).

## 2. 결과 — 모델 × 군 × 질문

| 모델 | 대조군 Q1 | 대조군 Q2 | 키메라 Q1 | 키메라 Q2 |
| --- | --- | --- | --- | --- |
| Gemini 3.1 Pro | **56/65 (86%)** | 54/65 (83%) | **0/50 (0%)** | 11/50 (22%) |
| DeepSeek V4 Flash | 10/65 (15%) | 30/65 (46%) | **0/50 (0%)** | 2/50 (4%) |
| Qwen3-8B | 0/65 (0%) | 8/65 (12%) | **0/50 (0%)** | 0/50 (0%) |

카드 단위로는 대조군 13장 중 **12장**이 Q1에서 최소 한 번 재식별됐다(Rory Breaker만
세 모델 전부 0). 키메라는 10장 전부 Q1에서 0회다.

## 3. 사전등록이 물은 세 가지에 대한 답

### ① 대조군이 실제로 재식별되었는가 — 그렇다. 검사는 성립한다

제미나이는 익명화된 단독 출처 카드를 **열린 질문에서 86% 맞혔다.** 같은 모델이 같은
형식의 키메라 카드는 50회 중 0회 맞혔다. 이 대비가 이 검사의 핵심 근거다.

대조군이 더 불리한 조건이었다는 점을 덧붙일 수 있다. 원자료(세그먼트) 부족으로
**대조군 카드의 정당화 항목은 1~3개인 반면 키메라는 전부 3개**다(`summary.md` §5).
재료가 더 적었는데도 재식별됐다.

### ② 재식별된 키메라와 그 출처 — 강제 추측에서만, 13건

| 카드 | 모델 | 재식별 | 1순위 적중 | 맞힌 출처 |
| --- | --- | --- | --- | --- |
| The Matriarch | Gemini | 5/5 | **5/5** | Christof / 트루먼 쇼 |
| The Curator | Gemini | 3/5 | 1/5 | Iago·오셀로, Christof·트루먼 쇼 |
| The Magistrate | Gemini | 2/5 | 0 | Little Bill Daggett / 용서받지 못한 자 |
| The Registrar | Gemini | 1/5 | 0 | Child Catcher / 치티치티 뱅뱅 |
| The Proprietor | DeepSeek | 2/5 | 1/5 | 그랜드 부다페스트 호텔 |

나머지 5장(Warden, Conservator, Preceptor, Impresario, Superintendent)은 세 모델
두 질문 전부 0이다. 키메라 1순위 적중은 전체 150회 중 **7회**.

### ③ 익명화 점검을 통과하지 못한 카드 — 자동 점검은 23장 전부 통과. 그러나 점검이 못 잡은 누출이 두 건 있다

45개 어휘 누출 점검은 고유명사만 본다. 아래 둘은 고유명사가 아니어서 통과했지만
모델에게는 출처를 가리키는 표지가 됐다.

**(가) The Curator — `'motiveless malignity'`**

카드에 이 구절이 그대로 들어 있다. 콜리지가 *오셀로*의 Iago를 두고 쓴 유명한 비평
용어다. 제미나이 Q1 원문(3/5회 유사):

> Based on the description provided, I **do not recognise** this character from any
> existing mainstream film, TV series, book, or animation. … Additionally, the phrase
> "motiveless malignity" is actually a famous literary critique coined by Samuel Taylor
> Coleridge to describe William Shakespeare's villain, Iago, from *Othello*.

**(나) The Matriarch — Christof의 논증 구조**

정당화 문장이 출처의 논리를 거의 그대로 옮겼다.
카드 원문: "ConsentByContentment: If the subject truly wanted to leave, he could have;
his staying proves the world's goodness."

제미나이 Q1 원문(5/5회):

> **I do not recognise this as a character from an existing film, TV series, book, or
> animation.** … That being said, the creator of this prompt seems to have borrowed
> heavily from existing tropes and characters. For example, the "CreationAsControl"
> (God Complex) trait and the "ConsentByContentment" justification … are almost exact
> parallels to the philosophy of **Christof** (played by Ed Harris) in the 1998 film
> ***The Truman Show***. However, Christof is a television producer, not a "Matriarch
> of a dynastic family estate."

딥식도 같은 패턴을 보인다. The Proprietor Q1에서 "알아보지 못한다"고 하면서 호텔
모티프의 유사 작품들을 열거하다 그랜드 부다페스트 호텔을 언급한다.

**부수 결함**: The Matriarch 카드의 정당화 문장에 출처(Christof)의 남성 대명사
"he / his"가 그대로 남아 있다. 여가장 카드에 남성 대명사가 섞여 있으므로 수정이 필요하다.

## 4. 그래서 주장할 수 있는 것과 없는 것

**쓸 수 있는 문장**

- 키메라 카드는 세 모델 모두에서 **하나의 기존 인물로 재식별되지 않는다**(열린 질문 150회 중 0회).
- 같은 조건에서 단독 출처 카드는 재식별된다(제미나이 86%). 따라서 이 결과는 모델의
  무능이 아니라 합성의 효과다.
- 강제 추측에서는 키메라의 출처가 일부 드러난다(제미나이 22%). 즉 **자발적으로는
  재식별하지 않으나, 후보를 강요하면 출처가 섞여 나온다.**

**쓸 수 없는 문장**

- "키메라는 재식별 불가능하다" — Q2 결과와 §3-③이 반증한다.
- "모든 모델이 키메라를 알아보지 못했다"를 Qwen3-8B로 뒷받침하는 것.
  **Qwen은 대조군 열린 질문 0/65라 이 검사에서 검정력이 없다.** 키메라를 못 알아본
  것이 아니라 아무것도 못 알아본다. 논문에는 제미나이·딥식만 근거로 쓰고 Qwen은
  능력 미달로 기록하는 편이 정직하다.

**권장 서술**: "키메라는 인물 수준에서는 재식별되지 않지만, 구성 요소 수준의 귀속까지
막지는 못한다." 합성의 한계를 먼저 밝히고 대조군 86%를 나란히 놓으면, 같은 문단이
검사가 제대로 작동했다는 증거로도 읽힌다.

## 5. 사람 판정이 필요한 21건

사전등록 §5에 따라 자동 판정하지 않고 `reid/ambiguous.csv`로 보냈다. 재식별 비율에는
포함하지 않았다.

| 사유 | 건수 |
| --- | --- |
| 비인식 표현과 후보 동시 제시 | 16 |
| 정답 항목의 일부만 일치 (`Grand`, `Jason`) | 4 |
| 위험 토큰 단독 일치 | 1 |

16건 중 키메라 8건이 §3-③의 사례다. **"전체 재식별 아님 / 구성요소 귀속 있음"**으로
분류할 것을 권한다. 모델이 "모르겠다"를 명시했으므로 Q1 재식별로 세면 과대계상이고,
그냥 버리면 누출 증거가 사라진다.

## 6. 채점 규칙에 가한 수정 (실행 후, 판정 기준 자체는 불변)

사전등록 §5의 "정답 목록과 부분적으로만 겹치는 응답"을 구현한 코드에 오탐이 있어
두 차례 고쳤다. **재식별 판정 기준(정답 항목 전체 일치)은 건드리지 않았고,
'사람 검토로 보낼지' 판단만 바뀌었다.**

| 수정 | 검토 필요 건수 |
| --- | --- |
| 최초 구현(키워드 휴리스틱) | 98 |
| 부분 토큰 겹침으로 문자 그대로 구현 | 60 |
| **프롬프트에 이미 있던 낱말 제외** | **21** |

마지막 수정의 근거: Q2 질문문이 "list the **three** most likely"라고 묻기 때문에 모든
Q2 응답에 `three`가 들어갔고, 그것이 *Three Billboards*의 부분 일치로 잡혔다. 모델에게
건네준 낱말은 재인식의 증거가 될 수 없으므로 제외했다(`reid/score.py`의
`partial_overlap()`).

## 7. 기록해 둘 조건

- Qwen3-8B는 본 실험에서 Rebellions NPU(vllm-rbln)로 돌렸으나 이 검사는 Ollama의
  동일 가중치를 썼다. 런타임이 다르다.
- 세 모델 모두 추론 모드를 껐다(`think=false` / `reasoning_effort="none"` /
  `thinkingLevel="low"`). 제미나이는 완전히 끌 수 없어 최저 단계를 썼다.
- 딥식이 The Warden 카드를 두고 "`(graph: Manipulative Rationalization)` 같은 표기가
  보이므로 기계 생성 프로파일"이라고 답한 사례가 있다. 카드가 **기존 작품의 인물이
  아니라는 판단**을 내용이 아니라 형식에서 끌어낸 것으로, 제미나이의 "Character.AI
  system prompt처럼 보인다"는 응답도 같은 종류다. 재식별 실패의 일부는 합성 때문이
  아니라 카드가 기계 생성물처럼 보이기 때문일 수 있다 — 교란 요인으로 기록해 둔다.
