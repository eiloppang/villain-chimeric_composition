# 1020 — 논문용 프롬프트 그림

| 파일 | 내용 |
| --- | --- |
| `fig_binding_instruction.pdf` / `.png` | 결속 지침(`A_RULES`) 원문과 네 조건에서의 위치 |
| `fig_judge_prompt.pdf` / `.png` | GPT-5.6 Terra 채점 프롬프트(SYSTEM + USER) 원문 |
| `make_prompt_figures.py` | 위 두 그림 생성 스크립트 |

크기는 더블컬럼 폭 7.0 in. PDF는 벡터, PNG는 600 dpi. 둘 다 그대로 넣으면 되고,
캡션은 이미지에 굽지 않았으니 본문에서 붙이면 된다.

## 출처

그림에 들어간 문자열은 전부 **실행 코드에서 읽어 온다**. 다시 타이핑하지 않았다.

- 결속 지침 · 안전 규칙 · 공통 규칙 → `experiments/prompts.py`의 `A_RULES`, `SAFETY`,
  `COMMON_RULES`를 import
- 채점 프롬프트 → `experiments/judge.py`의 `judge_once()` f-string을 파싱해서 가져온 뒤,
  f-string 자리표시자 3개만 `« … »` 설명으로 치환. 치환 후 남은 자리표시자가 있으면
  스크립트가 assert로 멈춘다.

따라서 코드의 프롬프트가 바뀌면 스크립트를 다시 돌리는 것만으로 그림이 따라간다.

## 조건 표기

그림은 원고 표기(A / A′ / B / B′)를 쓴다. 공개 트랜스크립트의 키와의 대응은
그림 1 하단 각주에도 적어 두었다.

| 원고 | 데이터 키 | 내용 |
| --- | --- | --- |
| A | `A` | 지식그래프 + 결속 지침 |
| A′ | `D` | 지식그래프만 |
| B | `C` | 산문 + 결속 지침 |
| B′ | `B` | 산문만 |

## 재생성

```
python experiments/figures/make_prompt_figures.py
```

## 캡션 초안

- **Figure 1.** The behavioural binding instruction. (a) The four conditions differ only
  in the character representation (Turtle knowledge graph vs. prose) and in the presence
  of the binding block; the common rules and the safety line are identical throughout.
  (b) The binding block as injected, verbatim.
- **Figure 2.** The judging prompt. Each pair of transcripts is judged twice with the
  conditions swapped between the X and Y slots; an axis is scored only when both orders
  agree.
