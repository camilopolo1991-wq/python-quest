#!/usr/bin/env python3
"""
quest.py - the Python Quest game in your terminal.

Run it from the repo folder:

    python quest.py            show your hero, XP, streak and next exercise
    python quest.py next       show the instructions for your next exercise
    python quest.py check      test your current exercise (or: check m1-03a)
    python quest.py hint       get the next hint (hints are free)
    python quest.py solution   show the solution (you get no XP for that exercise)
    python quest.py list       see the whole map
    python quest.py setup      personalize: your name, language, hero color, daily goal
    python quest.py web        open the game in your browser (with Claude Code as your tutor)
    python quest.py verify     (for maintainers) prove every solution passes its tests

Only the Python standard library is used, so there is nothing to install.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LESSONS = ROOT / "lessons"
SAVE_DIR = ROOT / ".quest"
SAVE_FILE = SAVE_DIR / "progress.json"
CONFIG_FILE = SAVE_DIR / "config.json"
EVENTS: list[dict] = []   # XP events from the last action (the web view reads these)

# ---------------------------------------------------------------- game rules
XP_EXERCISE = 10       # each exercise passed the first time it is passed
XP_FIX = 10            # passing after a failed check, without viewing the solution
XP_LESSON = 50         # every exercise in a lesson passed
XP_BUILD = 150         # a Build project passed
XP_STREAK = 20         # each extra day in a row
# 60 levels, a new rank every 5 levels. Level 60 is Python Master.
RANKS = ["Curious", "Apprentice", "Coder", "Builder", "Debugger", "Scripter",
         "Hacker", "Engineer", "Architect", "Wizard", "Sage", "Python Master"]


def xp_for_level(n: int) -> int:
    """Total XP needed to reach level n. Grows a bit faster each level."""
    return int(round(40 * (n - 1) ** 1.5 / 10.0)) * 10


LEVELS = [(n, f"{RANKS[min((n - 1) // 5, len(RANKS) - 1)]}" + (f" {(n - 1) % 5 + 1}" if n < 60 else ""), xp_for_level(n))
          for n in range(1, 61)]

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if os.name == "nt":
    os.system("")  # turns on colors in the Windows terminal


def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


GOLD, TEAL, CORAL, BLUE, DIM, BOLD = "93", "96", "91", "94", "2", "1"


# ---------------------------------------------------------------- data
def load_exercises() -> list[dict]:
    """Every exercise, in course order. Each lives in lessons/<module>/<lesson>/<exercise>/."""
    found = []
    for test_file in sorted(LESSONS.glob("*/*/*/test.json")):
        folder = test_file.parent
        spec = json.loads(test_file.read_text(encoding="utf-8"))
        spec["folder"] = folder
        spec["module"] = folder.parent.parent.name
        spec["lesson"] = folder.parent.name
        found.append(spec)
    return found


def load_save() -> dict:
    if SAVE_FILE.exists():
        return json.loads(SAVE_FILE.read_text(encoding="utf-8"))
    return {"xp": 0, "streak": 0, "best_streak": 0, "last_day": None,
            "passed": [], "failed_once": [], "seen_solution": [], "lessons_done": [],
            "hints_used": {}, "log": []}


def write_save(save: dict) -> None:
    SAVE_DIR.mkdir(exist_ok=True)
    SAVE_FILE.write_text(json.dumps(save, indent=2), encoding="utf-8")


DEFAULT_MODEL = "claude-sonnet-5-5"
MODELS = [  # (model id for Claude Code, label). "" = whatever your Claude Code uses by default.
    ("claude-sonnet-5-5", "Sonnet 5.5 · balanced (default)"),
    ("claude-opus-5-5", "Opus 5.5 · smartest, slower"),
    ("claude-haiku-5-5", "Haiku 5.5 · fastest"),
    ("claude-fable-5-2", "Fable 5.2"),
    ("", "My Claude Code default"),
]
DEFAULT_CONFIG = {"name": "Coder", "language": "en", "hero_color": "blue", "daily_goal": 3,
                  "claude_model": DEFAULT_MODEL, "config_version": 2}


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        if saved.get("config_version", 1) < 2:  # older saves had no model picker
            saved["claude_model"] = DEFAULT_MODEL
            saved["config_version"] = 2
        cfg.update(saved)
    return cfg


def write_config(cfg: dict) -> None:
    SAVE_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def cmd_setup() -> None:
    cfg = load_config()
    print(c("\n  Let's make this game yours. Press Enter to keep the value in [brackets].\n", GOLD))

    def ask(label: str, key: str, choices: list[str] | None = None) -> None:
        hint = f" ({'/'.join(choices)})" if choices else ""
        value = input(f"  {label}{hint} [{cfg[key]}]: ").strip()
        if value and (not choices or value in choices):
            cfg[key] = int(value) if isinstance(DEFAULT_CONFIG[key], int) and value.isdigit() else value

    ask("Your name", "name")
    ask("Tutor language", "language", ["en", "es"])
    ask("Hero color", "hero_color", ["blue", "red", "green", "purple", "gold"])
    ask("Exercises per day goal", "daily_goal")
    print("  Models for Pip: " + ", ".join(m or "(empty = Claude Code default)" for m, _ in MODELS))
    ask("Claude model for Pip", "claude_model", [m for m, _ in MODELS])
    write_config(cfg)
    print(c(f"\n  Saved. Welcome, {cfg['name']}! Run: python quest.py web\n", TEAL))


def level_for(xp: int) -> tuple[int, str, int]:
    current = LEVELS[0]
    for lv in LEVELS:
        if xp >= lv[2]:
            current = lv
    return current


def next_level(lv: tuple[int, str, int]):
    for other in LEVELS:
        if other[0] == lv[0] + 1:
            return other
    return None


def find(exercises: list[dict], ex_id: str | None, save: dict) -> dict | None:
    if ex_id:
        for ex in exercises:
            if ex["id"] == ex_id:
                return ex
        print(c(f"No exercise called {ex_id}. Try: python quest.py list", CORAL))
        return None
    for ex in exercises:
        if ex["id"] not in save["passed"]:
            return ex
    return None


# ---------------------------------------------------------------- running code
def run_program(path: Path, inputs: list[str], timeout: float = 5.0) -> tuple[str, str, bool]:
    """Runs a student's file. Returns (stdout, stderr, timed_out)."""
    try:
        proc = subprocess.run(
            [sys.executable, path.name], cwd=path.parent, input="\n".join(inputs) + "\n",
            capture_output=True, text=True, timeout=timeout, encoding="utf-8",
        )
        return proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired:
        return "", "", True


def call_function(path: Path, expression: str, timeout: float = 5.0) -> tuple[str, str, bool]:
    """Loads the file without running its main block, evaluates one expression, prints repr()."""
    code = (
        "import runpy, sys, io\n"
        "real = sys.stdout; sys.stdout = io.StringIO()\n"
        f"ns = runpy.run_path({path.name!r}, run_name='quest_test')\n"
        "sys.stdout = real\n"
        f"print(repr(eval({expression!r}, ns)))\n"
    )
    try:
        proc = subprocess.run([sys.executable, "-c", code], cwd=path.parent, capture_output=True,
                              text=True, timeout=timeout, input="", encoding="utf-8")
        return proc.stdout.strip(), proc.stderr, False
    except subprocess.TimeoutExpired:
        return "", "", True


FRIENDLY = {
    "NameError": "Python doesn't know that name. Check the spelling, or create the variable first. Text needs quotes.",
    "SyntaxError": "Python couldn't read a line. Look for a missing colon :, a bracket ( ) or a quote mark.",
    "IndentationError": "The spaces at the start of a line are off. Lines inside if, for, while or def need 4 spaces.",
    "TypeError": "You mixed things that don't fit, like text + a number. Try str(), int() or float().",
    "ValueError": "A value has the wrong shape, like int('hola').",
    "ZeroDivisionError": "You divided by zero.",
    "EOFError": "Your program asked input() more times than the test gives answers.",
    "IndexError": "That list position doesn't exist. Lists start counting at 0.",
    "KeyError": "That key isn't in the dictionary.",
    "AttributeError": "That kind of value doesn't have this method. Check the spelling after the dot.",
    "FileNotFoundError": "Python can't find that file. Check the name and the folder.",
}


def explain_error(stderr: str) -> str:
    last = [line for line in stderr.strip().splitlines() if line.strip()]
    if not last:
        return ""
    name = last[-1].split(":")[0].strip()
    line_no = ""
    for line in last:
        if 'File "' in line and "line " in line and ("exercise.py" in line or "build.py" in line):
            line_no = line.split("line ")[1].split(",")[0]
    where = f" (line {line_no})" if line_no else ""
    tip = FRIENDLY.get(name, "Read the last line of the error: it names the problem.")
    return f"{c(last[-1], CORAL)}{where}\n  {c('What this means:', BOLD)} {tip}"


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def run_tests(ex: dict, file_name: str | None = None) -> tuple[bool, list[str]]:
    """Runs every test in test.json. Returns (all passed, report lines)."""
    path = ex["folder"] / (file_name or ex.get("file", "exercise.py"))
    report, ok_all = [], True
    for test in ex["tests"]:
        label = test.get("label", "test")
        if "call" in test:
            out, err, slow = call_function(path, test["call"])
        else:
            out, err, slow = run_program(path, test.get("inputs", []))
        ok, why = True, ""
        if slow:
            ok, why = False, "Your program ran too long. Is there a loop that never stops?"
        elif err.strip() and "Traceback" in err:
            ok, why = False, explain_error(err)
        elif "call" in test:
            if out != repr(test["equals"]):
                ok, why = False, f"Expected {repr(test['equals'])}, got {out or '(nothing)'}"
        else:
            text = out
            for piece in test.get("contains", []):
                if piece.lower() not in text.lower():
                    ok, why = False, f"Your output should include: {piece!r}"
                    break
            for piece in test.get("not_contains", []):
                if ok and piece.lower() in text.lower():
                    ok, why = False, f"Your output should NOT include: {piece!r}"
            if ok and "exact" in test and normalize(text) != normalize(test["exact"]):
                ok, why = False, "Output doesn't match exactly.\n  Expected:\n" + \
                    "\n".join("    " + s for s in test["exact"].splitlines()) + \
                    "\n  Got:\n" + "\n".join("    " + s for s in (text.strip().splitlines() or ["(nothing)"]))
            if ok and "source_contains" in test:
                src = path.read_text(encoding="utf-8")
                for piece in test["source_contains"]:
                    if piece not in src:
                        ok, why = False, f"Your code should use {piece!r}"
                        break
        ok_all &= ok
        mark = c("✓", TEAL) if ok else c("✗", CORAL)
        report.append(f"  {mark} {label}" + (f"\n    {why}" if why else ""))
    return ok_all, report


# ---------------------------------------------------------------- XP + streak
def today() -> str:
    return dt.date.today().isoformat()


def touch_streak(save: dict) -> int:
    """First pass of the day keeps the streak going. Returns the bonus XP."""
    t = today()
    last = save.get("last_day")
    if last == t:
        return 0
    bonus = 0
    if last and (dt.date.fromisoformat(t) - dt.date.fromisoformat(last)).days == 1:
        save["streak"] += 1
        bonus = XP_STREAK
    else:
        save["streak"] = 1
    save["last_day"] = t
    save["best_streak"] = max(save.get("best_streak", 0), save["streak"])
    return bonus


def give(save: dict, amount: int, what: str) -> None:
    if amount <= 0:
        return
    before = level_for(save["xp"])
    save["xp"] += amount
    save["log"] = ([{"day": today(), "xp": amount, "what": what}] + save["log"])[:30]
    print(c(f"  +{amount} XP  {what}", GOLD))
    EVENTS.append({"xp": amount, "what": what})
    after = level_for(save["xp"])
    if after[0] > before[0]:
        EVENTS.append({"levelUp": after[1]})
        print(c(f"\n  ★ LEVEL UP! You are now level {after[0]}: {after[1].upper()} ★\n", GOLD + ";1"))


# ---------------------------------------------------------------- screens
HERO = [
    "   ▄▄▄▄▄▄   ",
    "  █▀▀▀▀▀▀█  ",
    "  █ ●  ● █  ",
    "  █  ▀▀  █  ",
    "   ▀█▄▄█▀   ",
    "  ▄██▀▀██▄  ",
    "  █ ████ █  ",
    "   █▀  ▀█   ",
]


def bar(xp: int) -> str:
    lv = level_for(xp)
    nx = next_level(lv)
    if not nx:
        return c("█" * 24, GOLD) + "  MAX"
    done = int(24 * (xp - lv[2]) / (nx[2] - lv[2]))
    return c("█" * done, GOLD) + c("░" * (24 - done), DIM) + f"  {nx[2] - xp} XP to {nx[1]}"


def cmd_status(exercises, save) -> None:
    lv = level_for(save["xp"])
    print()
    side = [
        c("PYTHON QUEST · " + load_config()["name"].upper(), GOLD + ";1"),
        f"Level {lv[0]} · {c(lv[1].upper(), BLUE + ';1')}",
        f"XP {save['xp']}",
        bar(save["xp"]),
        f"Streak {c(str(save['streak']) + ' day(s)', CORAL)}  (best {save.get('best_streak', 0)})",
        f"Exercises {len(save['passed'])}/{len(exercises)}",
        "",
        "",
    ]
    for art, text in zip(HERO, side):
        print(c(art, TEAL) + "  " + text)
    ex = find(exercises, None, save)
    print()
    if ex:
        print(f"  Next: {c(ex['id'], GOLD)}  {ex['title']}")
        print(f"  Open: {ex['folder'].relative_to(ROOT) / ex.get('file', 'exercise.py')}")
        print(f"  Then: {c('python quest.py check', BOLD)}")
    else:
        print(c("  You finished every exercise here. Time for a personal project!", GOLD))
    print()


def cmd_next(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    lesson_md = ex["folder"].parent / "README.md"
    print()
    print(c(f"  {ex['id']} · {ex['title']}", GOLD + ";1"))
    if lesson_md.exists():
        print(c(f"  Lesson notes: {lesson_md.relative_to(ROOT)}", DIM))
    print()
    for line in ex["task"]:
        print(f"  • {line}")
    print()
    print(f"  Edit:  {ex['folder'].relative_to(ROOT) / ex.get('file', 'exercise.py')}")
    print(f"  Run:   cd {ex['folder'].relative_to(ROOT)} && python {ex.get('file', 'exercise.py')}")
    print(f"  Check: python quest.py check {ex['id']}")
    print()


def cmd_check(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    print(c(f"\n  Checking {ex['id']} · {ex['title']}\n", BOLD))
    ok, report = run_tests(ex)
    print("\n".join(report))
    print()
    if not ok:
        if ex["id"] not in save["failed_once"]:
            save["failed_once"].append(ex["id"])
        write_save(save)
        print(c("  Not yet. Fix one ✗ at a time, run your file to see what it prints, then check again.", CORAL))
        print(c("  Stuck? python quest.py hint", DIM))
        print()
        return
    first_time = ex["id"] not in save["passed"]
    if not first_time:
        print(c("  Still passing. You already got the XP for this one.\n", TEAL))
        return
    save["passed"].append(ex["id"])
    print(c("  ★ PASSED ★", TEAL + ";1"))
    give(save, touch_streak(save), f"Streak day {save['streak']}")
    if ex["id"] in save["seen_solution"]:
        print(c("  No XP: you looked at the solution. That's okay, try the next one on your own.", DIM))
    else:
        give(save, XP_BUILD if ex.get("build") else XP_EXERCISE, ("Build: " if ex.get("build") else "Exercise: ") + ex["title"])
        if ex["id"] in save["failed_once"]:
            give(save, XP_FIX, "You fixed your own error")
    # whole lesson done?
    lesson_key = f"{ex['module']}/{ex['lesson']}"
    siblings = [e["id"] for e in exercises if f"{e['module']}/{e['lesson']}" == lesson_key]
    if lesson_key not in save["lessons_done"] and all(s in save["passed"] for s in siblings) and not ex.get("build"):
        save["lessons_done"].append(lesson_key)
        give(save, XP_LESSON, f"Lesson complete: {ex['lesson']}")
    write_save(save)
    nxt = find(exercises, None, save)
    if nxt:
        print(f"\n  Next up: {c(nxt['id'], GOLD)} {nxt['title']}  →  python quest.py next\n")


def cmd_hint(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    hints = ex.get("hints", [])
    used = save["hints_used"].get(ex["id"], 0)
    if not hints:
        print("  No hints for this one. Read the lesson notes again, or ask Pip in the game page.")
        return
    shown = min(used + 1, len(hints))
    save["hints_used"][ex["id"]] = shown
    write_save(save)
    print()
    for i, h in enumerate(hints[:shown], 1):
        print(f"  {c('Hint ' + str(i), GOLD)}: {h}")
    if shown < len(hints):
        print(c("\n  Run hint again for a bigger hint.", DIM))
    print()


def cmd_solution(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    if ex["id"] not in save["seen_solution"] and "--yes" not in sys.argv:
        print(c("\n  Seeing the solution means no XP for this exercise.", CORAL))
        print("  If you're sure, run: python quest.py solution " + ex["id"] + " --yes\n")
        return
    if ex["id"] not in save["seen_solution"]:
        save["seen_solution"].append(ex["id"])
        write_save(save)
    sol = ex["folder"] / "solution.py"
    print()
    print(sol.read_text(encoding="utf-8"))


def cmd_list(exercises, save) -> None:
    current_module = None
    for ex in exercises:
        if ex["module"] != current_module:
            current_module = ex["module"]
            print("\n" + c(current_module.upper().replace("_", " "), GOLD + ";1"))
        mark = c("✓", TEAL) if ex["id"] in save["passed"] else c("·", DIM)
        tag = c(" BUILD", BLUE) if ex.get("build") else ""
        print(f"  {mark} {ex['id']:8} {ex['title']}{tag}")
    print()


def cmd_verify(exercises) -> int:
    bad = 0
    for ex in exercises:
        ok, report = run_tests(ex, "solution.py")
        print(("PASS " if ok else "FAIL ") + ex["id"])
        if not ok:
            bad += 1
            print("\n".join(report))
        starter_ok, _ = run_tests(ex)
        if starter_ok and not ex.get("starter_may_pass"):
            bad += 1
            print("  starter already passes:", ex["id"])
    print(f"\n{len(exercises) - bad}/{len(exercises)} exercises OK")
    return 1 if bad else 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not CONFIG_FILE.exists() and (not args or args[0] in ("status", "next", "check")) and sys.stdin.isatty():
        print(c("\n  Welcome to Python Quest! First, tell me about you.", GOLD + ";1"))
        cmd_setup()
    exercises = load_exercises()
    save = load_save()
    cmd = args[0] if args else "status"
    ex_id = args[1] if len(args) > 1 else None
    if cmd == "status":
        cmd_status(exercises, save)
    elif cmd == "next":
        cmd_next(exercises, save, ex_id)
    elif cmd == "check":
        cmd_check(exercises, save, ex_id)
    elif cmd == "hint":
        cmd_hint(exercises, save, ex_id)
    elif cmd == "solution":
        cmd_solution(exercises, save, ex_id)
    elif cmd == "list":
        cmd_list(exercises, save)
    elif cmd == "setup":
        cmd_setup()
    elif cmd == "web":
        import web_server
        web_server.serve()
    elif cmd == "verify":
        return cmd_verify(exercises)
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
