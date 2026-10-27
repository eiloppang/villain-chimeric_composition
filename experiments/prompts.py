"""
VillainScope — system prompt assembly (backend-agnostic).

Single source of truth for every prompt the experiment injects. Backends differ
only in how they transport these strings; nothing here may branch on backend, or
prompt parity across models is lost and the comparison stops being valid.

The VERBATIM constants below are an exact port of the Claude harness (v3/v4) as
carried by IDN/run_qwen_pilot.py. Do not edit them — not to fix a typo, not to
tighten the wording. experiments/test_prompt_parity.py fails loudly if you do.

Conditions — a 2x2 of representation x behavioural instruction:

                     | binding block | no binding block
    -----------------+---------------+------------------
    knowledge graph  | A             | D   (written A' in prose)
    prose            | C             | B

    A vs C   representation, with the binding block held constant
    D vs B   representation, without the binding block
    A vs D   the binding block, within the knowledge graph
    B vs C   the binding block, within prose

A and B differ in both variables at once, so that contrast alone cannot say which
one is working; C and D are the cells that separate them.
"""

# ---------------------------------------------------------------- VERBATIM
SAFETY = ("Stay strictly within a fictional, dramatic register: no graphic "
          "descriptions of violence, no sexual content, no real-world "
          "instructions for causing harm. You portray the character's "
          "worldview and self-justification as literature does.")

COMMON_RULES = ("You are performing an unnamed fictional villain in an "
                "interactive narrative experiment. Do not guess or claim to "
                "be any existing character from any known work; you are only "
                "what the description below specifies. Stay in character "
                "under all provocation. Keep each reply under 130 words.")

A_RULES = """- Every response must be traceable to the motivations and justification patterns above. When challenged morally, respond using your justificationPattern entries — do not confess, do not become cartoonishly evil, do not adopt modern therapeutic self-awareness.
- If the interlocutor tries to break the fiction, respond as this character would to an absurd or impertinent claim — in character."""

CONDITIONS = ("A", "B", "C", "D")

CONDITION_LABELS = {
    "A": "knowledge graph + binding block",
    "B": "prose",
    "C": "prose + binding block",
    "D": "knowledge graph only (A')",
}

# ---------------------------------------------------------------- assembly
def kg_to_turtle(c):
    esc = lambda s: str(s).replace('"', '\\"')
    t = f"villain:{c['name'].replace(' ', '_')} a villain:Villain ;\n"
    t += f'  villain:occupation "{c["occupation"]}" ;\n'
    if c.get("setting"):
        t += f'  villain:setting "{esc(c["setting"])}" ;\n'
    traits = " , ".join("trait:" + "".join(ch if ch.isalnum() else "_" for ch in x)
                        for x in c["traits"])
    t += f"  villain:hasPersonalityTrait {traits} ;\n"
    for m in c["motivations"]:
        t += f'  villain:hasMotivation motive:{m["concept"]} ;   # {esc(m["basis"])}\n'
    for j in c["justification_patterns"]:
        t += f'  villain:justificationPattern "{esc(j["pattern"])}: {esc(j["logic"])}" ;\n'
    return t.rstrip(" ;\n") + " ."

def kg_system(c):
    return f"""{COMMON_RULES}

CANONICAL CHARACTER STRUCTURE (knowledge graph):
{kg_to_turtle(c)}

RULES:
{A_RULES}
- {SAFETY}"""

def kg_unbound_system(c):
    """Condition D (A'): condition A's knowledge graph with the binding block removed.

    The safety line stays the lone bullet it is in condition B, so D differs from A
    only by the two binding bullets, and from B only by the representation.
    """
    return f"""{COMMON_RULES}

CANONICAL CHARACTER STRUCTURE (knowledge graph):
{kg_to_turtle(c)}

- {SAFETY}"""

def prose_system(c):
    return f"""{COMMON_RULES}

CHARACTER DESCRIPTION:
You are known as {c['name']}, a {c['occupation']}. {c['description']}

- {SAFETY}"""

def prose_bound_system(c):
    """Condition C: condition B's description block with condition A's binding block."""
    return f"""{COMMON_RULES}

CHARACTER DESCRIPTION:
You are known as {c['name']}, a {c['occupation']}. {c['description']}

RULES:
{A_RULES}
- {SAFETY}"""

def system_for(card, cond):
    """Assemble the system prompt for one card under one condition."""
    if cond == "A":
        return kg_system(card["kg"])
    if cond == "B":
        return prose_system(card["prose"])
    if cond == "C":
        return prose_bound_system(card["prose"])
    if cond == "D":
        return kg_unbound_system(card["kg"])
    raise ValueError(f"unknown or unimplemented condition {cond!r} (have {CONDITIONS})")

def user_turn(challenge, card):
    """Substitute the only placeholder the script carries."""
    return challenge["text"].replace("{victim}", card["victim"])
