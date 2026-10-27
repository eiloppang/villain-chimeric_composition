"""Stage the files for the public GitHub repository and zip them.

The directory layout is kept exactly as it is in the working tree, because the scripts
find each other by relative path (judge.py imports prompts.py from its own directory,
run_reid.py reads experiments/env.env, build_cards.py reads IDN/cards_chimera_10.json).
Rearranging the folders would make a clone that no longer runs.

Before writing the archive every staged file is scanned for the live API keys and for
anything shaped like a key; the build aborts if one is found.

    python experiments/1027-최종결과/make_release.py
"""
import pathlib
import re
import shutil
import sys
import zipfile

OUT = pathlib.Path(__file__).resolve().parent
ROOT = OUT.parent.parent
STAGE = OUT / "_stage"
NAME = "VillainScope-experiments"

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# directories copied whole, minus the skip rules below
TREES = ["IDN", "reid", "conversion-dataset_2",
         "experiments/0908_최종결과", "experiments/0914_최종결과",
         "experiments/0929_최종결과", "experiments/1020-최종결과"]

# the manuscript itself is not published here
EXCLUDE = {"IDN/abstract.md", "IDN/methods_draft.md"}

# Korean paths are renamed for the public repository: they survive a clone badly
# (percent-encoded links, locale-dependent tools). Applied to the staged path and to
# the text of every staged .md/.py, longest first, so cross-references keep working.
RENAMES = [
    ("experiments/0908_최종결과", "experiments/pilot_deepseek_20260908"),
    ("experiments/0914_최종결과", "experiments/pilot_gemini_20260914"),
    ("experiments/0929_최종결과", "experiments/main_20260929"),
    ("experiments/1020-최종결과", "experiments/figures"),
    ("../0929_최종결과/", "../main_20260929/"),
    ('"0908_최종결과"', '"pilot_deepseek_20260908"'),
    ("deepseek_deepseek-v4-flash_20260908_212641", "deepseek_v4-flash_20260908"),
    ("0908_실험결과_보고.docx", "pilot_report.docx"),
    ("0914_실험결과_보고.docx", "pilot_report.docx"),
    ("vllm-rbln_Qwen_Qwen3-8B_20260929_200738_judged.json", "qwen3-8b_abcd_judged.json"),
    ("vllm-rbln_Qwen_Qwen3-8B_20260929_200738.json", "qwen3-8b_abcd.json"),
    ("검증_재집계.md", "verification_reaggregation.md"),
    ("통계보정.md", "statistics_holm_wilcoxon.md"),
    ("결과정리.md", "qwen3-8b_run_notes.md"),
    ("TheWarden_대화기록.md", "transcripts_the_warden.md"),
    ("TheMatriarch_자료모음.md", "materials_the_matriarch.md"),
    ("주입프롬프트_원문.md", "injected_prompts_verbatim.md"),
    ("전체응답_조건별.docx", "all_responses_by_condition.docx"),
    ("집계_비교쌍별.csv", "aggregate_by_pair.csv"),
    ("집계_캐릭터별.csv", "aggregate_by_character.csv"),
    ("판정_전체.csv", "verdicts_all.csv"),
    ("재식별검사_결과정리.md", "reid_findings.md"),
]
# "재식별검사_결과정리.md" must not be rewritten to the old name inside its own text,
# and "결과정리.md" is a suffix of it, so the longer keys run first
RENAMES.sort(key=lambda kv: -len(kv[0]))


def rename(s):
    for old, new in RENAMES:
        s = s.replace(old, new)
    return s

# individual files
FILES = [".gitignore",
         "experiments/prompts.py", "experiments/run_experiment.py",
         "experiments/judge.py", "experiments/judge_local_pilot.py",
         "experiments/run_local_pilot.py", "experiments/make_cards_10.py",
         "experiments/test_prompt_parity.py", "experiments/README.md",
         "experiments/claude_code_prompt_fullpaper.md",
         "필요한파일/experiments/env.env.example:experiments/env.env.example"]

SKIP_DIRS = {"__pycache__", ".git", "node_modules", ".venv", "_stage"}
SKIP_SUFFIX = {".pyc", ".zip", ".bak"}
SKIP_NAMES = {"env.env", ".env"}

REQUIREMENTS = """# data conversion (VillainScope knowledge graph)
rdflib>=7.0.0
pandas>=2.0.0

# experiment runners and judge
requests>=2.31.0
anthropic>=0.40.0

# figures
matplotlib>=3.8.0
"""


def keep(p: pathlib.Path) -> bool:
    if any(part in SKIP_DIRS for part in p.parts):
        return False
    if p.suffix.lower() in SKIP_SUFFIX or p.name in SKIP_NAMES:
        return False
    return True


def stage():
    if STAGE.exists():
        shutil.rmtree(STAGE)
    root = STAGE / NAME
    root.mkdir(parents=True)
    n = 0
    for tree in TREES:
        src = ROOT / tree
        if not src.is_dir():
            raise SystemExit("missing directory: %s" % tree)
        for f in src.rglob("*"):
            rel = f.relative_to(ROOT).as_posix()
            if not f.is_file() or not keep(f) or rel in EXCLUDE:
                continue
            dst = root / rename(rel)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
            n += 1
    for spec in FILES:
        src_rel, _, dst_rel = spec.partition(":")
        src = ROOT / src_rel
        if not src.is_file():
            raise SystemExit("missing file: %s" % src_rel)
        dst = root / rename(dst_rel or src_rel)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    # rewrite the path references inside the staged text so links still resolve
    for f in root.rglob("*"):
        if f.suffix.lower() not in (".md", ".py"):
            continue
        before = f.read_text(encoding="utf-8")
        after = rename(before)
        if after != before:
            f.write_text(after, encoding="utf-8")
    (root / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    shutil.copy2(OUT / "README.md", root / "README.md")
    return root, n + 2


def secret_scan(root):
    """Abort on the live keys, or on anything shaped like one."""
    live = []
    env = ROOT / "experiments" / "env.env"
    if env.is_file():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                v = line.split("=", 1)[1].strip().strip('"').strip("'")
                if len(v) >= 12:
                    live.append(v)
    shaped = re.compile(r"(sk-[A-Za-z0-9_\-]{16,}|AIza[A-Za-z0-9_\-]{20,}"
                        r"|gsk_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})")
    bad = []
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = f.relative_to(root)
        if any(v in text for v in live):
            bad.append("%s — 실제 키 값 포함" % rel)
        for m in shaped.findall(text):
            bad.append("%s — 키 형태 문자열 %s…" % (rel, m[:8]))
        if f.name in SKIP_NAMES:
            bad.append("%s — 키 파일 자체" % rel)
    return bad, len(live)


HANGUL = re.compile(r"[가-힣]")


def leftover_scan(root):
    """Korean file names, and stale references to the names that were renamed."""
    names = [f.relative_to(root).as_posix() for f in root.rglob("*")
             if f.is_file() and HANGUL.search(f.name)]
    stale = []
    for f in root.rglob("*"):
        if f.suffix.lower() not in (".md", ".py"):
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        for old, _ in RENAMES:
            if old in text:
                stale.append("%s → %s" % (f.relative_to(root).as_posix(), old))
    return names, sorted(set(stale))


def main():
    root, n = stage()
    names, stale = leftover_scan(root)
    if names:
        print("한글 파일명이 남음:")
        for x in names:
            print("  ", x)
    if stale:
        print("옛 이름 참조가 남음:")
        for x in stale:
            print("  ", x)
    bad, n_live = secret_scan(root)
    print("스테이징 %d개 파일 · 대조한 실제 키 %d개" % (n, n_live))
    if bad:
        print("\n중단: 비밀정보가 발견되었습니다")
        for b in bad:
            print("  ", b)
        raise SystemExit(1)
    print("키 누출 검사 통과")

    zpath = OUT / ("%s.zip" % NAME)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(root.rglob("*")):
            if f.is_file():
                z.write(f, f.relative_to(STAGE))
    shutil.rmtree(STAGE)
    print("\n%s  (%.1f MB, %d개 파일)"
          % (zpath.name, zpath.stat().st_size / 1e6, n))


if __name__ == "__main__":
    main()
