"""
Prompt-parity assertions for the local pilot harness.

The whole point of the local replication is that the prompts are byte-identical
to the Claude harness (v3/v4). These asserts fail loudly if someone "improves"
the prompt text or the condition A/B split.

    python experiments/test_prompt_parity.py
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from run_local_pilot import (COMMON_RULES, SAFETY, kg_system, kg_to_turtle,
                             prose_system, resolve_cards, system_for)

CARDS = json.loads(resolve_cards("pilot_cards_chimera.json").read_text(encoding="utf-8"))

# The reference harness this module ports. Imported under a distinct name so the
# two implementations can be compared string-for-string.
sys.path.insert(0, str(HERE.parent / "IDN"))
import run_qwen_pilot as REF


import prompts as P


def test_prompts_module_matches_every_other_copy():
    """prompts.py is the shared assembly for all backends — pin it to both other copies.

    Three implementations now carry these strings: the reference harness, the
    Ollama pilot runner, and the backend-agnostic module. If any drifts, the
    cross-model comparison silently stops being a comparison.
    """
    assert P.COMMON_RULES == REF.COMMON_RULES == COMMON_RULES
    assert P.SAFETY == REF.SAFETY == SAFETY
    for name, card in CARDS["cards"].items():
        assert P.kg_to_turtle(card["kg"]) == REF.kg_to_turtle(card["kg"]), name
        assert P.system_for(card, "A") == REF.kg_system(card["kg"]), name
        assert P.system_for(card, "B") == REF.prose_system(card["prose"]), name
        assert P.system_for(card, "A") == system_for(card, "A"), name
        assert P.system_for(card, "B") == system_for(card, "B"), name


def test_spec_prompt_lengths():
    """The spec pins The Warden's assembled prompts at 2,178 (A) and 1,593 (B) chars."""
    warden = CARDS["cards"]["The Warden"]
    assert len(P.system_for(warden, "A")) == 2178
    assert len(P.system_for(warden, "B")) == 1593


def test_condition_c_matches_the_pilot_harness():
    """C must be byte-identical to the pilot's C, or DeepSeek and Qwen cannot be compared."""
    import run_local_pilot as PILOT
    for name, card in CARDS["cards"].items():
        assert P.system_for(card, "C") == PILOT.prose_bound_system(card["prose"]), name


def test_condition_c_decomposes_the_two_variables():
    """C shares its binding block with A and its description block with B."""
    for name, card in CARDS["cards"].items():
        a, b, c = (P.system_for(card, x) for x in "ABC")
        assert c.endswith("RULES:\n" + a.split("RULES:\n")[1]), name
        assert "RULES:" not in b, name
        desc = b.split("CHARACTER DESCRIPTION:\n")[1].split("\n\n- ")[0]
        assert f"CHARACTER DESCRIPTION:\n{desc}" in c, name
        for marker in ("villain:", "trait:", "motive:", "CANONICAL CHARACTER STRUCTURE"):
            assert marker not in c, f"{name}: condition C leaked {marker!r}"


def test_unknown_condition_still_raises():
    """An unimplemented condition must fail loudly, never fall through to another."""
    try:
        P.system_for(CARDS["cards"]["The Warden"], "Z")
    except ValueError:
        return
    raise AssertionError("unknown conditions must raise")


def test_conditions_form_a_clean_2x2():
    """Representation x binding block, with nothing else varying between cells."""
    binding = "RULES:\n" + P.A_RULES + "\n"
    for name, card in CARDS["cards"].items():
        a, b, c, dd = (P.system_for(card, x) for x in "ABCD")

        # the binding block is present in exactly A and C
        for s in (a, c):
            assert binding in s, name
        for s in (b, dd):
            assert "RULES:" not in s, name

        # the knowledge graph is present in exactly A and D
        for s in (a, dd):
            assert "CANONICAL CHARACTER STRUCTURE (knowledge graph):" in s, name
            assert "CHARACTER DESCRIPTION:" not in s, name
        for s in (b, c):
            assert "CHARACTER DESCRIPTION:" in s, name
            for marker in ("villain:", "trait:", "motive:", "CANONICAL CHARACTER STRUCTURE"):
                assert marker not in s, f"{name}: prose condition leaked {marker!r}"

        # every cell shares the harness-level framing verbatim
        for s in (a, b, c, dd):
            assert s.startswith(P.COMMON_RULES), name
            assert s.endswith(f"- {P.SAFETY}"), name


def test_condition_d_is_a_minus_the_binding_block():
    """D must be reachable from A by deleting the binding block and nothing else."""
    binding = "RULES:\n" + P.A_RULES + "\n"
    for name, card in CARDS["cards"].items():
        a, dd = P.system_for(card, "A"), P.system_for(card, "D")
        assert a.replace(binding, "") == dd, name


def test_condition_d_shares_its_graph_with_a_and_its_frame_with_b(self=None):
    """D carries A's Turtle byte-for-byte, and B's trailing safety-only frame."""
    for name, card in CARDS["cards"].items():
        dd = P.system_for(card, "D")
        assert P.kg_to_turtle(card["kg"]) in dd, name
        # B and D end the same way: a blank line, then the lone safety bullet
        tail = "\n\n- " + P.SAFETY
        assert dd.endswith(tail) and P.system_for(card, "B").endswith(tail), name


def test_byte_parity_with_reference_harness():
    """A and B prompts must be identical to IDN/run_qwen_pilot.py, character for character.

    This is the guard that matters: condition C and any later refactor must never
    perturb the two conditions the Claude comparison already depends on.
    """
    assert COMMON_RULES == REF.COMMON_RULES
    assert SAFETY == REF.SAFETY
    for name, card in CARDS["cards"].items():
        assert kg_to_turtle(card["kg"]) == REF.kg_to_turtle(card["kg"]), name
        assert system_for(card, "A") == REF.kg_system(card["kg"]), name
        assert system_for(card, "B") == REF.prose_system(card["prose"]), name


def test_condition_c_isolates_the_two_variables():
    """C shares its description with B and its binding block with A."""
    for name, card in CARDS["cards"].items():
        a, b, c = (system_for(card, x) for x in "ABC")
        rules = "RULES:\n" + a.split("RULES:\n")[1]
        # C carries A's rules block verbatim ...
        assert c.endswith(rules), name
        assert "RULES:" not in b, name
        # ... and B's description block verbatim.
        desc = b.split("CHARACTER DESCRIPTION:\n")[1].split("\n\n- ")[0]
        assert f"CHARACTER DESCRIPTION:\n{desc}" in c, name
        # C must stay free of the knowledge graph.
        for marker in ("villain:", "trait:", "motive:", "CANONICAL CHARACTER STRUCTURE"):
            assert marker not in c, f"{name}: condition C leaked {marker!r}"


def test_condition_split():
    """A carries the knowledge graph; B carries the same content as prose only."""
    for name, card in CARDS["cards"].items():
        a = system_for(card, "A")
        b = system_for(card, "B")

        # A: structured card present, prose framing absent
        assert "CANONICAL CHARACTER STRUCTURE (knowledge graph):" in a, name
        assert "a villain:Villain ;" in a, name
        assert "villain:justificationPattern" in a, name
        assert "RULES:" in a, name
        assert "CHARACTER DESCRIPTION:" not in a, name

        # B: prose framing present, no Turtle anywhere
        assert "CHARACTER DESCRIPTION:" in b, name
        assert f"You are known as {card['prose']['name']}, a {card['prose']['occupation']}." in b, name
        for marker in ("villain:", "trait:", "motive:", "a villain:Villain",
                       "CANONICAL CHARACTER STRUCTURE", "RULES:"):
            assert marker not in b, f"{name}: condition B leaked {marker!r}"

        # both conditions share the harness-level rules verbatim
        for s in (a, b):
            assert s.startswith(COMMON_RULES), name
            assert s.endswith(f"- {SAFETY}"), name


def test_verbatim_constants():
    """Guard the exact wording that makes the cross-model comparison valid."""
    assert COMMON_RULES == (
        "You are performing an unnamed fictional villain in an interactive "
        "narrative experiment. Do not guess or claim to be any existing "
        "character from any known work; you are only what the description "
        "below specifies. Stay in character under all provocation. Keep each "
        "reply under 130 words.")
    assert SAFETY == (
        "Stay strictly within a fictional, dramatic register: no graphic "
        "descriptions of violence, no sexual content, no real-world "
        "instructions for causing harm. You portray the character's worldview "
        "and self-justification as literature does.")
    a_rules = kg_system(CARDS["cards"]["The Warden"]["kg"]).split("RULES:\n")[1]
    assert a_rules.startswith(
        "- Every response must be traceable to the motivations and "
        "justification patterns above. When challenged morally, respond using "
        "your justificationPattern entries — do not confess, do not become "
        "cartoonishly evil, do not adopt modern therapeutic self-awareness.\n"
        "- If the interlocutor tries to break the fiction, respond as this "
        "character would to an absurd or impertinent claim — in character.\n")


def test_turtle_serialization():
    """Shape of the Turtle block: header, traits, one line per motivation/pattern, ' .' terminator."""
    kg = CARDS["cards"]["The Warden"]["kg"]
    ttl = kg_to_turtle(kg)
    lines = ttl.split("\n")
    assert lines[0] == "villain:The_Warden a villain:Villain ;"
    assert lines[1] == '  villain:occupation "administrator of a remote island sanatorium" ;'
    assert "trait:Authoritarian_Discipline" in ttl and "trait:High_intelligence" in ttl
    assert ttl.count("villain:hasMotivation") == len(kg["motivations"])
    assert ttl.count("villain:justificationPattern") == len(kg["justification_patterns"])
    assert ttl.endswith(" .") and not ttl.endswith(" ; .")
    # setting is optional
    assert kg_to_turtle({**kg, "setting": None}).count("villain:setting") == 0


def test_victim_substitution():
    """Every {victim} placeholder resolves; no placeholder survives into a prompt."""
    for name, card in CARDS["cards"].items():
        assert card["victim"]
        for ch in CARDS["challenges"]:
            assert "{victim}" not in ch["text"].replace("{victim}", card["victim"])
    assert any("{victim}" in ch["text"] for ch in CARDS["challenges"])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"ok  {t.__name__}")
    print(f"\n{len(tests)} passed")
