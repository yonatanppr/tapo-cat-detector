"""Flag AI-writing tells and prose bloat in docs, comments and commit messages.

Usage:
  prose_guard.py FILE...     check files (commit-msg hook passes the message file)
  prose_guard.py --staged    check staged files (pre-commit hook)
  prose_guard.py --hook      Claude Code PostToolUse hook (JSON on stdin)
  prose_guard.py --selftest

A line containing "prose-guard: ignore" is skipped.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

EXTS = {".md", ".txt", ".rst", ".py"}
MAX_MD_LINES = 200  # ponytail: one cap for every doc; per-path caps if a GLOSSARY legitimately outgrows it
SELF = Path(__file__).resolve()

# Tells from the humanizer skill that a regex can catch with few false positives.
TELLS = [
    ("dash", r"[—–]| -- "),
    ("chatbot residue", r"\b(i hope this helps|great question|you're absolutely right|let me know if|feel free to|happy to help)\b"),
    ("staged run-up", r"\b(let's (dive|explore|break (this|it) down)|here's (the thing|what you need to know)|without further ado)\b"),
    ("not X but Y", r"\bnot (just|only|merely)\b[^.\n]{0,80}\bbut\b|\bit's not\b[^.\n]{1,40}, it's\b"),
    ("deep-sounding saying", r"\b(at its core|the real question is|what really matters|the heart of the matter)\b"),
    ("inflation", r"\b(plays? an? (key|crucial|pivotal|vital) role|stands as|serves as an?|a testament to)\b"),
    ("filler", r"\b(it(?:'s| is) worth noting|in conclusion|in today's|ever-evolving)\b"),
    ("AI word", r"\b(delve[sd]?|delving|tapestry|pivotal|crucial|meticulous(ly)?|seamless(ly)?|showcas(e|es|ed|ing)"
                r"|underscores|vibrant|intricate|intricacies|interplay|garner(ed)?|bolster(ed)?|leverag(e|es|ed|ing)|game-changer)\b"),
    ("bold label list", r"^\s*[-*] \*\*[^*]+:\*\*"),
]
TELLS = [(name, re.compile(rx, re.I)) for name, rx in TELLS]


def strip_code(text):
    """Blank out fenced blocks and inline code in markdown, keeping line numbers."""
    text = re.sub(r"```.*?```", lambda m: "\n" * m.group().count("\n"), text, flags=re.S)
    return re.sub(r"`[^`\n]*`", "``", text)


def check(name, text):
    problems = []
    is_md = name.endswith(".md")
    if is_md:
        text = strip_code(text)
        n = text.count("\n") + 1
        if n > MAX_MD_LINES:
            problems.append(f"{name}: {n} lines, cap is {MAX_MD_LINES}. Cut it down or split by topic.")
    for i, line in enumerate(text.splitlines(), 1):
        if "prose-guard: ignore" in line or (line.startswith("#") and name.endswith("COMMIT_EDITMSG")):
            continue
        for tell, rx in TELLS:
            m = rx.search(line)
            if m:
                problems.append(f"{name}:{i}: {tell}: {m.group().strip()!r}")
    return problems


def wanted(path):
    return Path(path).suffix in EXTS and Path(path).resolve() != SELF


def main(argv):
    sys.stderr.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252
    if argv == ["--selftest"]:
        return selftest()
    if argv == ["--hook"]:
        path = json.load(sys.stdin).get("tool_input", {}).get("file_path", "")
        if not (path and wanted(path) and Path(path).is_file()):
            return 0
        problems = check(path, Path(path).read_text(encoding="utf-8", errors="replace"))
        code = 2  # Claude Code feeds stderr back to the model on exit 2
    elif argv == ["--staged"]:
        out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                             capture_output=True, text=True, check=True).stdout
        problems = []
        for p in filter(wanted, out.splitlines()):
            staged = subprocess.run(["git", "show", f":{p}"], capture_output=True, check=True).stdout
            problems += check(p, staged.decode("utf-8", errors="replace"))
        code = 1
    else:
        problems = [p for f in argv for p in check(f, Path(f).read_text(encoding="utf-8", errors="replace"))]
        code = 1
    if problems:
        print("prose-guard: AI-writing tells found. Rewrite plainly (see the humanizer skill); "
              "add 'prose-guard: ignore' to a line only if it is a real exception.", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        return code
    return 0


def selftest():
    assert check("a.md", "The cat sits on the mat.") == []
    assert check("a.md", "Let's dive in.")[0].endswith("staged run-up: \"Let's dive\"")
    assert check("a.md", "Fast — and cheap.")
    assert check("a.md", "Run `a -- b` here.\n```\nx — y\n```") == []
    assert check("a.md", "It's not just a cat, but a lifestyle.")
    assert check("a.md", "We delve deep. prose-guard: ignore") == []
    assert check("a.md", "- **Speed:** fast")
    assert check("a.md", "x\n" * MAX_MD_LINES)
    assert check("COMMIT_EDITMSG", "# Please enter the commit message\nFix crash") == []
    assert check("a.py", "# This crucial helper\nkey = 1")
    assert check("a.py", "keys = {'robust': 1}\nnot_found = None") == []
    print("selftest ok")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
