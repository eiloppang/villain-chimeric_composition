# 키메라 카드 재식별 검사 — 사전등록

**작성 2026-10-18 · 실행 전 확정 · 이 파일은 실행 후 수정하지 않는다.**

---

## 1. 목적

키메라 카드가 모델에게 원작으로 재식별되는지를 직접 묻는다.
대조군(출처 악인 단독 카드)을 함께 돌려, 이 검사가 원작을 알아볼 능력을 가진 검사인지도 확인한다.
대조군이 재식별되지 않으면 이 검사는 키메라의 비식별성 근거로 쓸 수 없다.

## 2. 입력 카드

- **실험군**: 키메라 10장. `IDN/cards_chimera_10.json`의 `prose.description`을 본 실험과 같은
  산문 템플릿으로 제시한다. 결속 지침(`A_RULES`)은 포함하지 않는다.
- **대조군**: 출처 악인 13명 각각의 단독 카드. `conversion-dataset_2`의 `schema1:description`
  세그먼트에서 동기 최대 3개, 정당화 최대 3개를 취한다. 6개에 못 미치면 있는 만큼만 쓰고
  개수를 `reid/cards_reid.json`에 기록한다.
- 두 군의 차이는 **여러 악인의 조합이냐 한 악인이냐** 하나뿐이어야 한다. 템플릿·헤더·
  익명화 규칙은 동일하다.

### 카드에 넣는 블록 (시스템 프롬프트가 아니라 사용자 메시지에 넣는다)

```
CHARACTER DESCRIPTION:
You are known as {name}, a {occupation}. {description}
```

`COMMON_RULES`와 안전 규칙은 넣지 않는다. 둘 다 "악역을 연기하라"는 지시여서 재식별 질문과
충돌하기 때문이다.

### 익명화 규칙 (두 군 동일)

작품명, 등장인물명, 지명, 실존 인물명, 그 작품에서만 쓰이는 특징적 소품을 삭제하거나
상위 개념으로 일반화한다. 피해자 집단(예: children)처럼 고유명사가 아닌 서술은 유지한다.
적용한 편집은 `reid/cards_reid.json`의 `anonymization` 항목에 전부 기록한다.
45개 어휘 누출 점검을 두 군 모두에 돌리고 결과를 기록한다.

## 3. 모델과 호출

| 모델 | 식별자 | temperature | 사고 | max tokens |
| --- | --- | --- | --- | --- |
| Qwen3-8B | `qwen3:8b` (Ollama) | 0.7 | 끔 (`/no_think`) | 4096 |
| DeepSeek V4 Flash | `deepseek-v4-flash` | 0.7 | `reasoning_effort="none"` | 4096 |
| Gemini 3.1 Pro | `gemini-3.1-pro-preview` | 1.0 | `thinkingLevel="low"` | 4096 |

본 실험 Qwen3-8B는 Rebellions NPU(vllm-rbln)에서 돌렸으나, 이번 검사는 Ollama의 동일 모델
가중치를 쓴다. 런타임이 다르다는 점을 결과에 기록한다.

두 질문은 각각 **독립 호출**로 묻는다. 카드마다 모델마다 질문마다 **5회 샘플링**.
총 23장 × 3모델 × 2질문 × 5회 = **690회**.

### Q1 (열린 질문)

```
Below is a description of a character. Is this character from an existing film, TV series, book, or animation? If so, name the work and the character. If you do not recognise it, say so.
```

### Q2 (강제 추측)

```
Below is a description of a character. Even if you are unsure, list the three most likely existing characters this description is based on, with the work each comes from.
```

## 4. 정답 목록

카드마다 출처 악인 이름(별칭 포함)과 작품명(원제·번역제 포함)을 `reid/answer_key.json`에
실행 전에 저장한다. 키메라는 **출처 세 명 모두가 정답**이다.

## 5. 판정 기준

- 응답 하나가 정답 목록의 **인물명 또는 작품명을 하나라도 포함**하면 "재식별"로 센다.
- 문자열 일치로 자동 판정한다. 대소문자는 무시하고 단어 경계를 적용한다.
- **Q1**: 카드 단위로 5회 중 재식별 비율을 보고한다. 5회 중 1회라도 재식별되면
  "한 번이라도 재식별"로 따로 표시한다.
- **Q2**: 세 후보 가운데 정답이 하나라도 있으면 재식별. **1순위 적중**도 따로 센다.
  1순위는 응답에서 가장 먼저 제시된 후보로 판정한다.
- 다음은 자동 판정하지 않고 `reid/ambiguous.csv`로 모아 사람이 판정한다.
  - 일반명사와 겹치는 작품명 단일 토큰 일치: `Metropolis`, `Unforgiven`, `Othello`를 제외한
    짧은 토큰, 그리고 `Romano`, `Dmitri`, `Vidal`, `Indio`, `Dixon`, `Daggett` 등
    인물명 단독 일치로서 작품명이 함께 나오지 않은 경우
  - 정답 목록과 부분적으로만 겹치는 응답(예: 작품 시리즈명만, 배우명, 유사 인물명)
  - 모델이 "모르겠다"고 하면서 동시에 후보를 제시한 경우

## 6. 출력

- `reid/raw/*.jsonl` — 모든 호출의 요청 설정과 응답 원문
- `reid/results.csv` — 카드, 군, 모델, 질문, 샘플 번호, 응답 요약, 재식별 여부, 맞힌 이름
- `reid/summary.md` — 모델별·군별·질문별 재식별 비율. 키메라가 재식별된 경우 카드와 출처 목록
- `reid/ambiguous.csv` — 사람 판정이 필요한 응답

해석과 논문 문장은 쓰지 않는다. 숫자와 표만 싣는다.

## 7. 기존 자료 보호

`experiments/` 아래 기존 결과 파일은 읽기만 한다. 이번 작업의 산출물은 전부 `reid/` 아래에만 쓴다.
