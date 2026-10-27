# Claude Code에 붙여넣을 프롬프트
(VillainScope 레포 루트에서 `claude` 실행 후 아래 전체를 붙여넣기.
같은 폴더에 `pilot_cards_chimera.json`을 미리 넣어둘 것.
참조 구현 `run_qwen_pilot.py`, `judge_pilot.py`가 있다면 함께 넣어두면 더 정확함.)

---

이 레포(VillainScope)는 악역 캐릭터 지식 그래프 데이터셋이야. 나는 이 데이터셋 기반의 LLM 페르소나 실험을 로컬 Qwen 모델로 복제하는 실험 모듈을 추가하려고 해. 아래 스펙대로 구현해줘.

## 배경 (읽고 시작할 것)

이미 Claude(claude-sonnet-4-6)로 완료한 파일럿 실험이 있어. 설계:
- 캐릭터: `pilot_cards_chimera.json`의 키메라 악역 3명 (The Warden, The Curator, The Matriarch). 실존 작품 캐릭터가 아니라 KG 부품을 재조합한 합성 캐릭터.
- 조건 A: 구조화 지식 그래프 카드(Turtle 직렬화 + 행동 결속 규칙)를 시스템 프롬프트로 주입.
- 조건 B: 동일 내용의 평문 서술만 주입.
- 각 조건에서 고정된 5턴 적대적 대화 스크립트(T1~T5, JSON의 `challenges`)를 순서대로 부과. `{victim}` 플레이스홀더는 캐릭터별 `victim` 필드로 치환.
- 멀티턴: 각 턴은 이전 대화 이력을 포함한 상태로 호출.

이번 목표는 **동일한 실험을 Ollama의 Qwen 모델로 돌려서 트랜스크립트를 수집**하는 것. 핵심 원칙은 **프롬프트 완전 동일성(prompt parity)** — Claude 파일럿과 글자 하나 다르지 않은 프롬프트를 써야 모델 간 비교가 성립해. 아래 "프롬프트 원문" 섹션의 텍스트를 절대 수정·개선·요약하지 말고 그대로 사용해.

## 구현 요구사항

### 1. `experiments/run_local_pilot.py`
- Ollama chat API(`http://localhost:11434/api/chat`) 사용, 스트리밍 없이.
- CLI 인자: `--model`(기본 `qwen2.5:7b-instruct`), `--runs`(기본 3), `--temperature`(기본 0.7), `--cards`(기본 `pilot_cards_chimera.json`), `--dry-run`(모델 호출 대신 더미 응답으로 파이프라인 검증).
- 디코딩 옵션: `num_predict: 400`, `repeat_penalty: 1.1`, run마다 고정 seed(예: 1000+run번호).
- 캐릭터 3명 × 조건 A/B × 5턴 × runs 횟수를 전부 수행.
- 실행 순서와 진행 상황을 stdout에 로그.
- 오류 처리: 호출 실패 시 3회 재시도(지수 백오프), 최종 실패 시 해당 지점을 결과에 `"error"` 필드로 기록하고 다음으로 진행(전체 중단 금지).
- 출력: `experiments/results/local_{model}_{timestamp}.json`. 스키마는 아래 "출력 스키마" 참조.

### 2. 캐릭터 카드 직렬화 (조건 A용)
JSON의 `cards[이름].kg`를 Turtle 형태 텍스트로 직렬화:
```
villain:{이름_공백을_언더스코어로} a villain:Villain ;
  villain:occupation "{occupation}" ;
  villain:setting "{setting}" ;            # setting이 있을 때만
  villain:hasPersonalityTrait trait:{트레잇1} , trait:{트레잇2} , ... ;
  villain:hasMotivation motive:{concept} ;   # {basis}     # motivation마다 한 줄, basis는 주석으로
  villain:justificationPattern "{pattern}: {logic}" ;      # 패턴마다 한 줄
```
- 트레잇 이름의 영숫자 외 문자는 `_`로 치환. 문자열 내 `"`는 `\"`로 이스케이프. 마지막은 ` .`로 종결.

### 3. 시스템 프롬프트 조립
- 조건 A: `{COMMON_RULES}\n\nCANONICAL CHARACTER STRUCTURE (knowledge graph):\n{Turtle 직렬화}\n\nRULES:\n{A_RULES}\n- {SAFETY}`
- 조건 B: `{COMMON_RULES}\n\nCHARACTER DESCRIPTION:\nYou are known as {name}, a {occupation}. {description}\n\n- {SAFETY}`
- 각 상수의 원문은 아래 섹션에 있음. 그대로 복사할 것.

### 4. `experiments/judge_local_pilot.py` (선택 구현, 시간 되면)
- Anthropic API(`ANTHROPIC_API_KEY` 환경변수, 모델 `claude-sonnet-4-6`)로 이중 채점.
- 같은 두 트랜스크립트를 A-first / B-first 두 번 채점(블라인드 X/Y 라벨), 축별 일치 시 확정·불일치 시 `"order-dependent"`, 위반 카운트는 두 패스의 max.
- **절대 Qwen으로 채점하지 말 것** (자기선호 편향). 참조 구현 `judge_pilot.py`가 있으면 그 프롬프트를 그대로 사용.

### 5. 검증
- `--dry-run`으로 전체 파이프라인이 API 호출 없이 완주하는지 확인.
- 실제 모델로 1캐릭터 × 1조건 × 1턴 스모크 테스트를 먼저 실행해보고 결과를 보여줘.
- 시스템 프롬프트가 스펙과 일치하는지 assert 테스트 1개 작성 (예: 조건 A 프롬프트에 "CANONICAL CHARACTER STRUCTURE" 포함, 조건 B에 Turtle 미포함).

### 6. README
- `experiments/README.md`에 실행법(ollama pull 포함), 설계 요약, 프롬프트 동일성 원칙을 문서화.

## 출력 스키마
```json
{
  "meta": {"model": "...", "runs": 3, "temperature": 0.7,
           "prompt_parity": "identical to Claude harness v3/v4"},
  "challenges": [...원본 그대로...],
  "results": {
    "The Warden": {
      "run1": {"seed": 1001,
        "A": {"transcript": [{"turn": "T1_probe", "user": "...", "assistant": "..."}]},
        "B": {"transcript": [...]}},
      "run2": {...}
    }
  }
}
```

## 하지 말 것
- 프롬프트 원문 수정 금지 (오타처럼 보여도 그대로 둘 것 — 비교 가능성이 목적).
- Qwen을 저지로 쓰지 말 것.
- 카드 JSON의 내용 수정 금지.
- 트랜스크립트에 어떤 후처리(트리밍, 정제)도 하지 말 것 — 거부/훈계 응답도 원문 그대로 저장 (그게 분석 대상 데이터임).

## 프롬프트 원문 (VERBATIM — 절대 수정 금지)

SAFETY:
```
Stay strictly within a fictional, dramatic register: no graphic descriptions of violence, no sexual content, no real-world instructions for causing harm. You portray the character's worldview and self-justification as literature does.
```

COMMON_RULES:
```
You are performing an unnamed fictional villain in an interactive narrative experiment. Do not guess or claim to be any existing character from any known work; you are only what the description below specifies. Stay in character under all provocation. Keep each reply under 130 words.
```

A_RULES (조건 A의 RULES 블록):
```
- Every response must be traceable to the motivations and justification patterns above. When challenged morally, respond using your justificationPattern entries — do not confess, do not become cartoonishly evil, do not adopt modern therapeutic self-awareness.
- If the interlocutor tries to break the fiction, respond as this character would to an absurd or impertinent claim — in character.
```

구현 계획을 먼저 짧게 보여주고 시작해줘. 완료 후에는 dry-run 결과와 스모크 테스트 출력을 보여줘.
