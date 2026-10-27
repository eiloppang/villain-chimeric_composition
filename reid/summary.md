# 재식별 검사 결과

판정 기준은 `PREREGISTRATION.md` §5 그대로다. `review`는 자동 판정하지 않고 `ambiguous.csv`로 보낸 응답이며, 아래 비율에서는 재식별로 세지 않았다.


## 1. 모델 × 군 × 질문별 재식별 비율

| 모델 | 군 | 질문 | 재식별 | 검토 필요 | 전체 | 비율 |
| --- | --- | --- | --- | --- | --- | --- |
| DeepSeek V4 Flash | control | q1 | 10 | 3 | 65 | 15% |
| DeepSeek V4 Flash | control | q2 | 30 | 2 | 65 | 46% |
| DeepSeek V4 Flash | chimera | q1 | 0 | 1 | 50 | 0% |
| DeepSeek V4 Flash | chimera | q2 | 2 | 0 | 50 | 4% |
| Gemini 3.1 Pro | control | q1 | 56 | 3 | 65 | 86% |
| Gemini 3.1 Pro | control | q2 | 54 | 0 | 65 | 83% |
| Gemini 3.1 Pro | chimera | q1 | 0 | 8 | 50 | 0% |
| Gemini 3.1 Pro | chimera | q2 | 11 | 1 | 50 | 22% |
| Qwen3-8B | control | q1 | 0 | 1 | 65 | 0% |
| Qwen3-8B | control | q2 | 8 | 0 | 65 | 12% |
| Qwen3-8B | chimera | q1 | 0 | 0 | 50 | 0% |
| Qwen3-8B | chimera | q2 | 0 | 2 | 50 | 0% |

## 2. 카드 단위 — Q1

5회 중 재식별 횟수. `한 번이라도`는 5회 중 1회 이상 재식별된 경우다.

| 카드 | 군 | DeepSeek V4 Flash | Gemini 3.1 Pro | Qwen3-8B | 한 번이라도 |
| --- | --- | --- | --- | --- | --- |
| chimera::The Warden | chimera | 0/5 | 0/5 | 0/5 | 아니오 |
| chimera::The Curator | chimera | 0/5 | 0/5 (검토 3) | 0/5 | 아니오 |
| chimera::The Matriarch | chimera | 0/5 | 0/5 (검토 5) | 0/5 | 아니오 |
| chimera::The Conservator | chimera | 0/5 | 0/5 | 0/5 | 아니오 |
| chimera::The Magistrate | chimera | 0/5 | 0/5 | 0/5 | 아니오 |
| chimera::The Proprietor | chimera | 0/5 (검토 1) | 0/5 | 0/5 | 아니오 |
| chimera::The Preceptor | chimera | 0/5 | 0/5 | 0/5 | 아니오 |
| chimera::The Registrar | chimera | 0/5 | 0/5 | 0/5 | 아니오 |
| chimera::The Impresario | chimera | 0/5 | 0/5 | 0/5 | 아니오 |
| chimera::The Superintendent | chimera | 0/5 | 0/5 | 0/5 | 아니오 |
| control::Iago | control | 0/5 | 5/5 | 0/5 | **예** |
| control::Captain Vidal | control | 0/5 | 5/5 | 0/5 | **예** |
| control::Child Catcher | control | 2/5 (검토 3) | 5/5 | 0/5 | **예** |
| control::Erfinder C.A. Rotwang | control | 1/5 | 5/5 | 0/5 | **예** |
| control::Jason Dixon | control | 0/5 | 5/5 | 0/5 | **예** |
| control::Dudley Liam Smith | control | 1/5 | 5/5 | 0/5 | **예** |
| control::El Indio | control | 0/5 | 4/5 | 0/5 | **예** |
| control::Little Bill Daggett | control | 0/5 | 5/5 | 0/5 | **예** |
| control::Dmitri | control | 0/5 | 5/5 | 0/5 | **예** |
| control::Randall Boggs | control | 1/5 | 5/5 | 0/5 | **예** |
| control::Christof | control | 5/5 | 5/5 | 0/5 (검토 1) | **예** |
| control::Romano | control | 0/5 | 2/5 (검토 3) | 0/5 | **예** |
| control::Rory Breaker | control | 0/5 | 0/5 | 0/5 | 아니오 |

## 3. 카드 단위 — Q2 (강제 추측)

`1순위`는 응답에서 가장 먼저 제시된 후보가 정답인 경우다.

| 카드 | 군 | DeepSeek V4 Flash 재식별 / 1순위 | Gemini 3.1 Pro 재식별 / 1순위 | Qwen3-8B 재식별 / 1순위 |
| --- | --- | --- | --- | --- |
| chimera::The Warden | chimera | 0/5 / 0 | 0/5 / 0 | 0/5 / 0 |
| chimera::The Curator | chimera | 0/5 / 0 | 3/5 / 1 | 0/5 / 0 |
| chimera::The Matriarch | chimera | 0/5 / 0 | 5/5 / 5 | 0/5 / 0 |
| chimera::The Conservator | chimera | 0/5 / 0 | 0/5 / 0 | 0/5 / 0 |
| chimera::The Magistrate | chimera | 0/5 / 0 | 2/5 / 0 | 0/5 / 0 |
| chimera::The Proprietor | chimera | 2/5 / 1 | 0/5 / 0 | 0/5 / 0 |
| chimera::The Preceptor | chimera | 0/5 / 0 | 0/5 / 0 | 0/5 / 0 |
| chimera::The Registrar | chimera | 0/5 / 0 | 1/5 / 0 | 0/5 / 0 |
| chimera::The Impresario | chimera | 0/5 / 0 | 0/5 / 0 | 0/5 / 0 |
| chimera::The Superintendent | chimera | 0/5 / 0 | 0/5 / 0 | 0/5 / 0 |
| control::Iago | control | 5/5 / 5 | 5/5 / 4 | 0/5 / 0 |
| control::Captain Vidal | control | 3/5 / 0 | 5/5 / 2 | 0/5 / 0 |
| control::Child Catcher | control | 5/5 / 5 | 5/5 / 4 | 4/5 / 0 |
| control::Erfinder C.A. Rotwang | control | 4/5 / 0 | 5/5 / 5 | 0/5 / 0 |
| control::Jason Dixon | control | 1/5 / 0 | 5/5 / 3 | 0/5 / 0 |
| control::Dudley Liam Smith | control | 2/5 / 0 | 5/5 / 2 | 0/5 / 0 |
| control::El Indio | control | 0/5 / 0 | 3/5 / 1 | 0/5 / 0 |
| control::Little Bill Daggett | control | 1/5 / 0 | 5/5 / 4 | 0/5 / 0 |
| control::Dmitri | control | 0/5 / 0 | 5/5 / 1 | 0/5 / 0 |
| control::Randall Boggs | control | 4/5 / 1 | 5/5 / 5 | 0/5 / 0 |
| control::Christof | control | 5/5 / 5 | 5/5 / 5 | 4/5 / 1 |
| control::Romano | control | 0/5 / 0 | 1/5 / 1 | 0/5 / 0 |
| control::Rory Breaker | control | 0/5 / 0 | 0/5 / 0 | 0/5 / 0 |

## 4. 키메라가 재식별된 경우

| 카드 | 모델 | 질문 | 샘플 | 맞힌 이름·작품 |
| --- | --- | --- | --- | --- |
| chimera::The Proprietor | DeepSeek V4 Flash | q2 | 3 | The Grand Budapest Hotel; Grand Budapest |
| chimera::The Proprietor | DeepSeek V4 Flash | q2 | 4 | The Grand Budapest Hotel; Grand Budapest |
| chimera::The Curator | Gemini 3.1 Pro | q2 | 1 | Iago; Othello |
| chimera::The Curator | Gemini 3.1 Pro | q2 | 4 | Christof; Iago; The Truman Show; Truman Show; Othello |
| chimera::The Curator | Gemini 3.1 Pro | q2 | 5 | Christof; The Truman Show; Truman Show |
| chimera::The Matriarch | Gemini 3.1 Pro | q2 | 1 | Christof; The Truman Show; Truman Show |
| chimera::The Matriarch | Gemini 3.1 Pro | q2 | 2 | Christof; The Truman Show; Truman Show |
| chimera::The Matriarch | Gemini 3.1 Pro | q2 | 3 | Christof; The Truman Show; Truman Show |
| chimera::The Matriarch | Gemini 3.1 Pro | q2 | 4 | Christof; The Truman Show; Truman Show |
| chimera::The Matriarch | Gemini 3.1 Pro | q2 | 5 | Christof; The Truman Show; Truman Show |
| chimera::The Magistrate | Gemini 3.1 Pro | q2 | 3 | Little Bill; Daggett; Unforgiven |
| chimera::The Magistrate | Gemini 3.1 Pro | q2 | 4 | Little Bill; Daggett; Unforgiven |
| chimera::The Registrar | Gemini 3.1 Pro | q2 | 4 | Child Catcher; Chitty Chitty Bang Bang |

## 5. 카드 구성 (대조군 개수 부족 기록)

| 카드 | 군 | 동기 | 정당화 | 어휘 점검 |
| --- | --- | --- | --- | --- |
| chimera::The Warden | chimera | 3 | 3 | 통과 |
| chimera::The Curator | chimera | 3 | 3 | 통과 |
| chimera::The Matriarch | chimera | 3 | 3 | 통과 |
| chimera::The Conservator | chimera | 3 | 3 | 통과 |
| chimera::The Magistrate | chimera | 3 | 3 | 통과 |
| chimera::The Proprietor | chimera | 3 | 3 | 통과 |
| chimera::The Preceptor | chimera | 3 | 3 | 통과 |
| chimera::The Registrar | chimera | 3 | 3 | 통과 |
| chimera::The Impresario | chimera | 3 | 3 | 통과 |
| chimera::The Superintendent | chimera | 3 | 3 | 통과 |
| control::Iago | control | 3 | 3 | 통과 |
| control::Captain Vidal | control | 3 | 2 | 통과 |
| control::Child Catcher | control | 3 | 1 | 통과 |
| control::Erfinder C.A. Rotwang | control | 3 | 2 | 통과 |
| control::Jason Dixon | control | 3 | 1 | 통과 |
| control::Dudley Liam Smith | control | 3 | 2 | 통과 |
| control::El Indio | control | 3 | 3 | 통과 |
| control::Little Bill Daggett | control | 3 | 2 | 통과 |
| control::Dmitri | control | 3 | 1 | 통과 |
| control::Randall Boggs | control | 3 | 1 | 통과 |
| control::Christof | control | 3 | 2 | 통과 |
| control::Romano | control | 3 | 2 | 통과 |
| control::Rory Breaker | control | 3 | 1 | 통과 |

## 6. 검토 필요 응답

자동 판정하지 않은 응답 **21건**. 사유별 분포: 비인식 표현과 후보 동시 제시 16, 정답 항목의 일부만 일치: Jason (Jason Dixon) 1, 위험 토큰 단독 일치 1, 정답 항목의 일부만 일치: Grand (Grand Budapest), Grand (The Grand Budapest Hotel) 3. 전체는 `ambiguous.csv`.