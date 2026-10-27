"""Render two print-ready prompt figures for the paper.

Figure 1  the behavioural binding instruction and the four conditions that carry it
Figure 2  the judging prompt given to GPT-5.6 Terra

Every quoted string is pulled from the running code, not retyped: the binding block
comes from experiments/prompts.py and the judge prompt from experiments/judge.py, so a
figure cannot drift from what was actually injected. Only the f-string placeholders in
the judge prompt are replaced, by angle-bracketed descriptions marked as substitutions.

    python experiments/figures/make_prompt_figures.py
"""
import pathlib
import re
import sys
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parent.parent
sys.path.insert(0, str(ROOT / "experiments"))
from prompts import A_RULES, SAFETY, COMMON_RULES  # noqa: E402

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

W = 7.0                      # double-column width
MONO = "DejaVu Sans Mono"
SANS = "DejaVu Sans"
ADV = 0.6021                 # DejaVu Sans Mono advance width, in em

INK = "#1a1a1a"
GREY = "#6b6b6b"
BIND_FILL, BIND_EDGE = "#f3e4d2", "#b06c2c"      # the binding block
SAFE_FILL, SAFE_EDGE = "#eef1f4", "#9aa5b1"      # the safety line
KG_FILL, KG_EDGE = "#e3ecf5", "#5a7fa6"
PR_FILL, PR_EDGE = "#f0ece4", "#9a8f7a"
CM_FILL, CM_EDGE = "#f4f4f4", "#b8b8b8"
CODE_FILL, CODE_EDGE = "#fbfbfa", "#c9c6c0"


def char_w(fs):
    return ADV * fs / 72.0


def wrap(text, fs, width_in, hang=2):
    """Wrap to the available inches, hanging-indenting bullet continuations."""
    n = max(20, int(width_in / char_w(fs)))
    out = []
    for para in text.split("\n"):
        if not para.strip():
            out.append("")
            continue
        sub = " " * hang if para.lstrip().startswith(("-", "1.", "2.", "3.")) else ""
        out += textwrap.wrap(para, n, subsequent_indent=sub,
                             break_long_words=False, break_on_hyphens=False) or [""]
    return out


def canvas(height):
    fig = plt.figure(figsize=(W, height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(height, 0)          # y grows downward, in inches
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, fill, edge, r=0.035, lw=0.7, ls="solid"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, linestyle=ls,
                                boxstyle="round,pad=0,rounding_size=%g" % r,
                                facecolor=fill, edgecolor=edge, linewidth=lw,
                                mutation_aspect=1))


def mono_block(ax, x, y, lines, fs, lh, color=INK, weight="normal"):
    for i, ln in enumerate(lines):
        ax.text(x, y + i * lh, ln, family=MONO, fontsize=fs, color=color,
                weight=weight, va="top", ha="left")
    return y + len(lines) * lh


def code_box(ax, x, y, w, lines, fs, lh, pad=0.075, fill=CODE_FILL, edge=CODE_EDGE,
             color=INK):
    h = len(lines) * lh + 2 * pad
    box(ax, x, y, w, h, fill, edge)
    mono_block(ax, x + pad + 0.02, y + pad, lines, fs, lh, color=color)
    return y + h


# ============================================================ Figure 1
def figure_one():
    fs_h, fs_lab, fs_mono = 9.0, 7.0, 7.1
    lh = 0.128
    m = 0.2
    inner = W - 2 * m

    bind_lines = wrap(A_RULES, fs_mono, inner - 0.34)
    safe_lines = wrap("- " + SAFETY, fs_mono, inner - 0.34)
    common_lines = wrap(COMMON_RULES, fs_mono, inner - 0.34)

    chip_h, chip_gap = 0.40, 0.075
    rows = 4
    chips_block = 0.20 + rows * chip_h + (rows - 1) * chip_gap

    H = (m + 0.30 + chips_block + 0.42 + 0.20 + len(bind_lines) * lh + 0.15
         + 0.20 + len(safe_lines) * lh + 0.15 + 0.34
         + 0.20 + len(common_lines) * lh + 0.15 + 0.19 + 0.30 + m)
    fig, ax = canvas(H)
    y = m

    ax.text(0, y, "  (a)  Where the instruction sits in the system prompt",
            family=SANS, fontsize=fs_h, weight="bold", color=INK, va="top")
    y += 0.30

    # four condition columns
    cols = [
        ("A",  "KG + binding",   KG_FILL, KG_EDGE, "CANONICAL CHARACTER\nSTRUCTURE  (Turtle KG)", True),
        ("A′", "KG only",   KG_FILL, KG_EDGE, "CANONICAL CHARACTER\nSTRUCTURE  (Turtle KG)", False),
        ("B",  "prose + binding", PR_FILL, PR_EDGE, "CHARACTER\nDESCRIPTION  (prose)", True),
        ("B′", "prose only", PR_FILL, PR_EDGE, "CHARACTER\nDESCRIPTION  (prose)", False),
    ]
    cw = (inner - 3 * 0.09) / 4
    for i, (name, sub, fill, edge, body, bound) in enumerate(cols):
        x = m + i * (cw + 0.09)
        ax.text(x + cw / 2, y, "%s   %s" % (name, sub), family=SANS, fontsize=fs_lab + 0.4,
                weight="bold", color=INK, ha="center", va="top")
        yy = y + 0.20
        chips = [(CM_FILL, CM_EDGE, "COMMON_RULES", INK, "solid"),
                 (fill, edge, body, INK, "solid")]
        if bound:
            chips.append((BIND_FILL, BIND_EDGE, "RULES:\nbinding instruction", INK, "solid"))
        else:
            chips.append(("#ffffff", "#c0c0c0", "(binding instruction\nabsent)", GREY, (0, (2.2, 1.8))))
        chips.append((SAFE_FILL, SAFE_EDGE, "safety line", INK, "solid"))
        for j, (f, e, t, tc, ls) in enumerate(chips):
            cy = yy + j * (chip_h + chip_gap)
            box(ax, x, cy, cw, chip_h, f, e, lw=0.75, ls=ls)
            ax.text(x + cw / 2, cy + chip_h / 2, t, family=MONO, fontsize=fs_lab - 0.5,
                    color=tc, ha="center", va="center", linespacing=1.45)
            if j < len(chips) - 1:
                ax.annotate("", xy=(x + cw / 2, cy + chip_h + chip_gap - 0.004),
                            xytext=(x + cw / 2, cy + chip_h + 0.004),
                            arrowprops=dict(arrowstyle="-|>", color="#8a8a8a",
                                            linewidth=0.6, mutation_scale=5))
    y += chips_block + 0.42

    ax.text(0, y, "  (b)  The binding instruction, verbatim  (391 characters)",
            family=SANS, fontsize=fs_h, weight="bold", color=INK, va="top")
    y += 0.30
    ax.text(m + 0.02, y, "RULES:", family=MONO, fontsize=fs_mono, weight="bold",
            color=INK, va="top")
    y += 0.175
    y = code_box(ax, m, y, inner, bind_lines, fs_mono, lh,
                 fill=BIND_FILL, edge=BIND_EDGE) + 0.14

    ax.text(m + 0.02, y, "— followed, in all four conditions, by the safety line:",
            family=SANS, fontsize=fs_lab, color=GREY, va="top", style="italic")
    y += 0.185
    y = code_box(ax, m, y, inner, safe_lines, fs_mono, lh,
                 fill=SAFE_FILL, edge=SAFE_EDGE) + 0.34

    ax.text(m + 0.02, y, "COMMON_RULES, identical in all four conditions:",
            family=SANS, fontsize=fs_lab, color=GREY, va="top", style="italic")
    y += 0.185
    y = code_box(ax, m, y, inner, common_lines, fs_mono, lh) + 0.19

    ax.text(m, y, "A and A′ differ only by the block in (b); so do B and B′. "
                  "Condition keys in the released transcripts: A=A, A′=D, B=C, B′=B.",
            family=SANS, fontsize=fs_lab - 0.6, color=GREY, va="top")
    return fig


# ============================================================ Figure 2
SYSTEM = ("You are an expert evaluator of character consistency in interactive "
          "narrative systems. Respond ONLY with a JSON object, no markdown "
          "fences, no preamble.")


def judge_user_template():
    """The judge prompt as judge.py builds it, with placeholders marked."""
    src = (ROOT / "experiments" / "judge.py").read_text(encoding="utf-8")
    body = src.split('    prompt = f"""', 1)[1].split('"""\n', 1)[0]
    subs = [("{kg_to_turtle(card_kg)}", "« reference knowledge graph, Turtle »"),
            ('{fmt(tX, "CHARACTER")}', "« 5-turn transcript, one condition »"),
            ('{fmt(tY, "CHARACTER")}', "« 5-turn transcript, the other condition »")]
    for a, b in subs:
        assert a in body, a
        body = body.replace(a, b)
    body = body.replace("{{", "{").replace("}}", "}")
    assert not re.search(r"\{[a-z_]+\(", body), "unsubstituted placeholder remains"
    return body


def figure_two():
    fs_h, fs_lab, fs_mono = 9.0, 7.0, 7.1
    lh = 0.128
    m = 0.2
    inner = W - 2 * m
    tw = inner - 0.34

    sys_lines = wrap(SYSTEM, fs_mono, tw)
    user = judge_user_template()
    user_lines = []
    for para in user.split("\n"):
        user_lines += wrap(para, fs_mono, tw, hang=3) or [""]
    # one line in the prompt; broken at commas here so it stays readable in print
    pad = " " * len("Return JSON: ")
    ret_lines = ['Return JSON: {"consistency":"X|Y","consistency_why":"one sentence",',
                 pad + '"complexity":"X|Y","complexity_why":"one sentence",',
                 pad + '"persuasiveness":"X|Y","persuasiveness_why":"one sentence",',
                 pad + '"violations_X":n,"violations_Y":n}']
    # the return line is already inside user_lines; drop it and re-add as its own box
    cut = next(i for i, l in enumerate(user_lines) if l.startswith("Return JSON:"))
    user_lines = user_lines[:cut]
    while user_lines and not user_lines[-1].strip():
        user_lines.pop()

    note = ("Each pair is judged twice, once with the conditions swapped between the "
            "X and Y slots. An axis counts as a win only if both orders agree; "
            "otherwise it is recorded as order-dependent. A transcript's violation "
            "count is the maximum of the two orders.")
    note_lines = wrap(note, fs_lab, inner - 0.1, hang=0)

    H = (m + 0.30 + 0.20 + len(sys_lines) * lh + 0.15 + 0.34
         + 0.20 + len(user_lines) * lh + 0.15 + 0.14
         + len(ret_lines) * lh + 0.15 + 0.36
         + len(note_lines) * 0.125 + 0.10 + m)
    fig, ax = canvas(H)
    y = m

    ax.text(0, y, "  GPT-5.6 Terra  ·  reasoning_effort = medium  ·  "
                  "temperature left at default  ·  max_completion_tokens = 4000",
            family=SANS, fontsize=fs_h - 1.2, weight="bold", color=INK, va="top")
    y += 0.30

    ax.text(m + 0.02, y, "SYSTEM", family=SANS, fontsize=fs_lab, weight="bold",
            color=GREY, va="top")
    y += 0.185
    y = code_box(ax, m, y, inner, sys_lines, fs_mono, lh) + 0.34

    ax.text(m + 0.02, y, "USER", family=SANS, fontsize=fs_lab, weight="bold",
            color=GREY, va="top")
    y += 0.185
    y = code_box(ax, m, y, inner, user_lines, fs_mono, lh) + 0.14
    y = code_box(ax, m, y, inner, ret_lines, fs_mono, lh,
                 fill="#f2f0ea", edge="#b9b3a6") + 0.30

    for i, ln in enumerate(note_lines):
        ax.text(m, y + i * 0.125, ln, family=SANS, fontsize=fs_lab - 0.6,
                color=GREY, va="top")
    y += len(note_lines) * 0.125 + 0.06
    ax.text(m, y, "« … » marks text substituted per comparison; everything else "
                  "is sent verbatim. The JSON schema is one line in the prompt.",
            family=SANS, fontsize=fs_lab - 0.6, color=GREY, va="top", style="italic")
    return fig


def save(fig, stem):
    for ext, kw in (("pdf", {}), ("png", {"dpi": 600})):
        p = OUT / ("%s.%s" % (stem, ext))
        fig.savefig(p, format=ext, facecolor="white", **kw)
        print("  %s  (%.2f x %.2f in)" % (p.name, *fig.get_size_inches()))
    plt.close(fig)


if __name__ == "__main__":
    print("writing to", OUT)
    save(figure_one(), "fig_binding_instruction")
    save(figure_two(), "fig_judge_prompt")
