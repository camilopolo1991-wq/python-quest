#!/usr/bin/env python3
"""
quest.py - the Python Quest game in your terminal. / el juego Python Quest en tu terminal.

Run it from the repo folder:

    python3 quest.py            your hero, XP, streak and next exercise
    python3 quest.py next       instructions for your next exercise
    python3 quest.py check      test your current exercise (or: check m1-03a)
    python3 quest.py hint       get the next hint (hints are free)
    python3 quest.py solution   show the solution (you get no XP for that exercise)
    python3 quest.py list       see the whole map
    python3 quest.py setup      personalize: name, language (en/es), hero color, daily goal, Pip's model
    python3 quest.py web        open the game in your browser (with Claude Code as your tutor)
    python3 quest.py verify     (for maintainers) prove every solution passes, in every language

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
LANGS = ("en", "es")
EVENTS: list[dict] = []   # XP events from the last action (the web view reads these)

# ---------------------------------------------------------------- game rules
XP_EXERCISE = 10       # each exercise passed the first time it is passed
XP_FIX = 10            # passing after a failed check, without viewing the solution
XP_LESSON = 50         # every exercise in a lesson passed
XP_BUILD = 150         # a Build project passed
XP_STREAK = 20         # each extra day in a row
# 60 levels, a new rank every 5 levels. Level 60 is Python Master.
RANKS_BY_LANG = {
    "en": ["Curious", "Apprentice", "Coder", "Builder", "Debugger", "Scripter",
           "Hacker", "Engineer", "Architect", "Wizard", "Sage", "Python Master"],
    "es": ["Curioso", "Aprendiz", "Programador", "Constructor", "Depurador", "Automatizador",
           "Hacker", "Ingeniero", "Arquitecto", "Mago", "Sabio", "Maestro Python"],
}
RANKS = RANKS_BY_LANG["en"]

# ---------------------------------------------------------------- every message, in both languages
MSG = {
    "en": {
        "setup_intro": "\n  Let's make this game yours. Press Enter to keep the value in [brackets].\n",
        "ask_name": "Your name", "ask_lang": "Language", "ask_color": "Hero color",
        "ask_goal": "Exercises per day goal", "ask_model": "Claude model for Pip",
        "models": "  Models for Pip: ", "model_default": "(empty = your Claude Code default)",
        "saved": "\n  Saved. Welcome, {name}! Run: python3 quest.py web\n",
        "welcome_first": "\n  Welcome to Python Quest! First, tell me about you.",
        "no_exercise": "No exercise called {id}. Try: python3 quest.py list",
        "level": "Level", "streak": "Streak", "days": "day(s)", "best": "best",
        "exercises": "Exercises", "xp_to": "XP to", "max": "MAX",
        "next": "Next", "open": "Open", "then": "Then",
        "all_done": "  You finished every exercise here. Time for a personal project!",
        "lesson_notes": "Lesson notes", "edit": "Edit", "run": "Run", "check": "Check",
        "checking": "\n  Checking {id} · {title}\n",
        "not_yet": "  Not yet. Fix one ✗ at a time, run your file to see what it prints, then check again.",
        "stuck": "  Stuck? python3 quest.py hint",
        "still": "  Still passing. You already got the XP for this one.\n",
        "passed": "  ★ PASSED ★",
        "streak_day": "Streak day {n}",
        "no_xp_solution": "  No XP: you looked at the solution. That's okay, try the next one on your own.",
        "xp_build": "Build: {title}", "xp_ex": "Exercise: {title}", "xp_fix": "You fixed your own error",
        "xp_lesson": "Lesson complete: {title}",
        "next_up": "\n  Next up: {id} {title}  →  python3 quest.py next\n",
        "no_hints": "  No hints for this one. Read the lesson notes again, or ask Pip in the game page.",
        "hint": "Hint", "hint_more": "\n  Run hint again for a bigger hint.",
        "sol_warn": "\n  Seeing the solution means no XP for this exercise.",
        "sol_sure": "  If you're sure, run: python3 quest.py solution {id} --yes\n",
        "level_up": "\n  ★ LEVEL UP! You are now level {n}: {name} ★\n",
        "too_long": "Your program ran too long. Is there a loop that never stops?",
        "expected_got": "Expected {exp}, got {got}", "nothing": "(nothing)",
        "should_include": "Your output should include: {p!r}",
        "should_not": "Your output should NOT include: {p!r}",
        "no_match": "Output doesn't match exactly.", "expected": "Expected", "got": "Got",
        "should_use": "Your code should use {p!r}",
        "what_means": "What this means:", "line": "line",
        "read_last": "Read the last line of the error: it names the problem.",
        "build_tag": " BUILD",
    },
    "es": {
        "setup_intro": "\n  Hagamos este juego tuyo. Presiona Enter para dejar el valor entre [corchetes].\n",
        "ask_name": "Tu nombre", "ask_lang": "Idioma", "ask_color": "Color del héroe",
        "ask_goal": "Meta de ejercicios por día", "ask_model": "Modelo de Claude para Pip",
        "models": "  Modelos para Pip: ", "model_default": "(vacío = el de tu Claude Code)",
        "saved": "\n  Guardado. ¡Bienvenido, {name}! Ejecuta: python3 quest.py web\n",
        "welcome_first": "\n  ¡Bienvenido a Python Quest! Primero, cuéntame de ti.",
        "no_exercise": "No hay un ejercicio llamado {id}. Prueba: python3 quest.py list",
        "level": "Nivel", "streak": "Racha", "days": "día(s)", "best": "mejor",
        "exercises": "Ejercicios", "xp_to": "XP para", "max": "MÁX",
        "next": "Sigue", "open": "Abre", "then": "Luego",
        "all_done": "  Terminaste todos los ejercicios. ¡Hora de un proyecto propio!",
        "lesson_notes": "Notas de la lección", "edit": "Edita", "run": "Corre", "check": "Revisa",
        "checking": "\n  Revisando {id} · {title}\n",
        "not_yet": "  Todavía no. Arregla un ✗ a la vez, corre tu archivo para ver qué imprime y vuelve a revisar.",
        "stuck": "  ¿Atascado? python3 quest.py hint",
        "still": "  Sigue pasando. Ya ganaste los XP de este.\n",
        "passed": "  ★ ¡SUPERADO! ★",
        "streak_day": "Racha día {n}",
        "no_xp_solution": "  Sin XP: viste la solución. Tranquilo, intenta el siguiente por tu cuenta.",
        "xp_build": "Proyecto: {title}", "xp_ex": "Ejercicio: {title}", "xp_fix": "Arreglaste tu propio error",
        "xp_lesson": "Lección completa: {title}",
        "next_up": "\n  Sigue: {id} {title}  →  python3 quest.py next\n",
        "no_hints": "  Este no tiene pistas. Relee las notas de la lección o pregúntale a Pip en la página del juego.",
        "hint": "Pista", "hint_more": "\n  Vuelve a pedir hint para una pista más grande.",
        "sol_warn": "\n  Ver la solución significa cero XP en este ejercicio.",
        "sol_sure": "  Si estás seguro, ejecuta: python3 quest.py solution {id} --yes\n",
        "level_up": "\n  ★ ¡SUBISTE DE NIVEL! Ahora eres nivel {n}: {name} ★\n",
        "too_long": "Tu programa tardó demasiado. ¿Hay un ciclo que nunca termina?",
        "expected_got": "Se esperaba {exp}, salió {got}", "nothing": "(nada)",
        "should_include": "Tu salida debe incluir: {p!r}",
        "should_not": "Tu salida NO debe incluir: {p!r}",
        "no_match": "La salida no coincide exactamente.", "expected": "Se esperaba", "got": "Salió",
        "should_use": "Tu código debe usar {p!r}",
        "what_means": "Qué significa:", "line": "línea",
        "read_last": "Lee la última línea del error: ahí dice cuál es el problema.",
        "build_tag": " PROYECTO",
    },
}

FRIENDLY = {
    "en": {
        "NameError": "Python doesn't know that name. Check the spelling, or create the variable first. Text needs quotes.",
        "SyntaxError": "Python couldn't read a line. Look for a missing colon :, a bracket ( ) or a quote mark.",
        "IndentationError": "The spaces at the start of a line are off. Lines inside if, for, while or def need 4 spaces.",
        "TypeError": "You mixed things that don't fit, like text + a number. Try str(), int() or float().",
        "ValueError": "A value has the wrong shape, like int('hello').",
        "ZeroDivisionError": "You divided by zero.",
        "EOFError": "Your program asked input() more times than the test gives answers.",
        "IndexError": "That list position doesn't exist. Lists start counting at 0.",
        "KeyError": "That key isn't in the dictionary.",
        "AttributeError": "That kind of value doesn't have this method. Check the spelling after the dot.",
        "FileNotFoundError": "Python can't find that file. Check the name and the folder.",
    },
    "es": {
        "NameError": "Python no conoce ese nombre. Revisa cómo lo escribiste o crea la variable primero. El texto va entre comillas.",
        "SyntaxError": "Python no pudo leer una línea. Busca dos puntos :, un paréntesis ( ) o una comilla que falte.",
        "IndentationError": "Los espacios al inicio de una línea están mal. Lo que va dentro de if, for, while o def lleva 4 espacios.",
        "TypeError": "Mezclaste cosas que no encajan, como texto + número. Prueba str(), int() o float().",
        "ValueError": "Un valor tiene la forma equivocada, como int('hola').",
        "ZeroDivisionError": "Dividiste entre cero.",
        "EOFError": "Tu programa pidió input() más veces de las respuestas que da la prueba.",
        "IndexError": "Esa posición de la lista no existe. Las listas empiezan a contar en 0.",
        "KeyError": "Esa llave no está en el diccionario.",
        "AttributeError": "Ese tipo de valor no tiene ese método. Revisa lo que escribiste después del punto.",
        "FileNotFoundError": "Python no encuentra ese archivo. Revisa el nombre y la carpeta.",
    },
}


def xp_for_level(n: int) -> int:
    """Total XP needed to reach level n. Grows a bit faster each level."""
    return int(round(40 * (n - 1) ** 1.5 / 10.0)) * 10


def level_name(n: int, lang: str | None = None) -> str:
    ranks = RANKS_BY_LANG.get(lang or current_lang(), RANKS)
    return ranks[min((n - 1) // 5, len(ranks) - 1)] + (f" {(n - 1) % 5 + 1}" if n < 60 else "")


LEVEL_XP = [(n, xp_for_level(n)) for n in range(1, 61)]

USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
if os.name == "nt":
    os.system("")  # turns on colors in the Windows terminal


def c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


GOLD, TEAL, CORAL, BLUE, DIM, BOLD = "93", "96", "91", "94", "2", "1"


# ---------------------------------------------------------------- settings
DEFAULT_MODEL = "claude-sonnet-5-5"
MODELS = [  # (model id for Claude Code, English label, Spanish label). "" = Claude Code's own default.
    ("claude-sonnet-5-5", "Sonnet 5.5 · balanced (default)", "Sonnet 5.5 · equilibrado (por defecto)"),
    ("claude-opus-5-5", "Opus 5.5 · smartest, slower", "Opus 5.5 · el más listo, más lento"),
    ("claude-haiku-5-5", "Haiku 5.5 · fastest", "Haiku 5.5 · el más rápido"),
    ("claude-fable-5-2", "Fable 5.2", "Fable 5.2"),
    ("", "My Claude Code default", "El de mi Claude Code"),
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
    if cfg.get("language") not in LANGS:
        cfg["language"] = "en"
    return cfg


def current_lang() -> str:
    return load_config()["language"]


def t(key: str, lang: str | None = None, **kw) -> str:
    text = MSG[lang or current_lang()][key]
    return text.format(**kw) if kw else text


def write_config(cfg: dict) -> None:
    """Saves settings. If the language changed, untouched exercise files switch language too."""
    old = load_config()["language"] if CONFIG_FILE.exists() else None
    SAVE_DIR.mkdir(exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    if old and old != cfg["language"]:
        switch_language(old, cfg["language"])


# ---------------------------------------------------------------- data
def starter_path(ex: dict, lang: str) -> Path:
    return ex["folder"] / f"starter.{lang}.py"


def work_file(ex: dict) -> Path:
    """The learner's own file (exercise.py or build.py). Made from the starter on first use."""
    path = ex["folder"] / ex.get("file", "exercise.py")
    if not path.exists():
        path.write_text(starter_path(ex, ex["lang"]).read_text(encoding="utf-8"), encoding="utf-8")
    return path


def switch_language(old: str, new: str) -> None:
    """Swaps starter code to the new language, but never touches code the learner already wrote."""
    for ex in load_exercises(new):
        path = ex["folder"] / ex.get("file", "exercise.py")
        if path.exists() and path.read_text(encoding="utf-8") == starter_path(ex, old).read_text(encoding="utf-8"):
            path.write_text(starter_path(ex, new).read_text(encoding="utf-8"), encoding="utf-8")


def lesson_readme(folder: Path, lang: str) -> Path:
    return folder / f"README.{lang}.md"


def lesson_title(folder: Path, lang: str) -> str:
    readme = lesson_readme(folder, lang)
    if readme.exists():
        first = readme.read_text(encoding="utf-8").splitlines()[0]
        return first.lstrip("# ").strip()
    return folder.name


def load_exercises(lang: str | None = None) -> list[dict]:
    """Every exercise, in course order, in one language. Each lives in lessons/<module>/<lesson>/<exercise>/."""
    lang = lang or current_lang()
    found = []
    for test_file in sorted(LESSONS.glob("*/*/*/test.json")):
        folder = test_file.parent
        spec = json.loads(test_file.read_text(encoding="utf-8"))
        spec.update(spec.get(lang) or spec.get("en"))
        spec["lang"] = lang
        spec["folder"] = folder
        spec["module"] = folder.parent.parent.name
        spec["lesson"] = folder.parent.name
        spec["lesson_title"] = lesson_title(folder.parent, lang)
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


def cmd_setup() -> None:
    cfg = load_config()
    lang = cfg["language"]
    print(c(t("setup_intro", lang), GOLD))

    def ask(label: str, key: str, choices: list[str] | None = None) -> None:
        hint = f" ({'/'.join(choices)})" if choices else ""
        value = input(f"  {label}{hint} [{cfg[key]}]: ").strip()
        if value and (not choices or value in choices):
            cfg[key] = int(value) if isinstance(DEFAULT_CONFIG[key], int) and value.isdigit() else value

    ask(t("ask_lang", lang), "language", list(LANGS))
    lang = cfg["language"]
    ask(t("ask_name", lang), "name")
    ask(t("ask_color", lang), "hero_color", ["blue", "red", "green", "purple", "gold"])
    ask(t("ask_goal", lang), "daily_goal")
    print(t("models", lang) + ", ".join(m or t("model_default", lang) for m, *_ in MODELS))
    ask(t("ask_model", lang), "claude_model", [m for m, *_ in MODELS])
    write_config(cfg)
    print(c(t("saved", lang, name=cfg["name"]), TEAL))


def level_for(xp: int) -> tuple[int, str, int]:
    current = LEVEL_XP[0]
    for lv in LEVEL_XP:
        if xp >= lv[1]:
            current = lv
    return current[0], level_name(current[0]), current[1]


def next_level(lv: tuple[int, str, int]):
    n = lv[0] + 1
    return (n, level_name(n), xp_for_level(n)) if n <= 60 else None


def find(exercises: list[dict], ex_id: str | None, save: dict) -> dict | None:
    if ex_id:
        for ex in exercises:
            if ex["id"] == ex_id:
                return ex
        print(c(t("no_exercise", id=ex_id), CORAL))
        return None
    for ex in exercises:
        if ex["id"] not in save["passed"]:
            return ex
    return None


# ---------------------------------------------------------------- running code
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8"}  # ¡tildes y eñes! work on every terminal


def run_program(path: Path, inputs: list[str], timeout: float = 5.0) -> tuple[str, str, bool]:
    """Runs a student's file. Returns (stdout, stderr, timed_out)."""
    try:
        proc = subprocess.run(
            [sys.executable, path.name], cwd=path.parent, input="\n".join(inputs) + "\n",
            capture_output=True, text=True, timeout=timeout, encoding="utf-8", env=ENV,
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
                              text=True, timeout=timeout, input="", encoding="utf-8", env=ENV)
        return proc.stdout.strip(), proc.stderr, False
    except subprocess.TimeoutExpired:
        return "", "", True


def explain_error(stderr: str, lang: str | None = None) -> str:
    lang = lang or current_lang()
    last = [line for line in stderr.strip().splitlines() if line.strip()]
    if not last:
        return ""
    name = last[-1].split(":")[0].strip()
    line_no = ""
    for line in last:
        if 'File "' in line and "line " in line and line.split('"')[1].endswith(".py") and "<" not in line:
            line_no = line.split("line ")[1].split(",")[0]
    where = f" ({t('line', lang)} {line_no})" if line_no else ""
    tip = FRIENDLY[lang].get(name, t("read_last", lang))
    return f"{c(last[-1], CORAL)}{where}\n  {c(t('what_means', lang), BOLD)} {tip}"


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())


def run_tests(ex: dict, path: Path | None = None) -> tuple[bool, list[str]]:
    """Runs every test in test.json. Returns (all passed, report lines)."""
    lang = ex["lang"]
    path = path or work_file(ex)
    report, ok_all = [], True
    for test in ex["tests"]:
        label = test.get("label", "test")
        if "call" in test:
            out, err, slow = call_function(path, test["call"])
        else:
            out, err, slow = run_program(path, test.get("inputs", []))
        ok, why = True, ""
        if slow:
            ok, why = False, t("too_long", lang)
        elif err.strip() and "Traceback" in err:
            ok, why = False, explain_error(err, lang)
        elif "call" in test:
            if out != repr(test["equals"]):
                ok, why = False, t("expected_got", lang, exp=repr(test["equals"]), got=out or t("nothing", lang))
        else:
            text = out
            for piece in test.get("contains", []):
                if piece.lower() not in text.lower():
                    ok, why = False, t("should_include", lang, p=piece)
                    break
            for piece in test.get("not_contains", []):
                if ok and piece.lower() in text.lower():
                    ok, why = False, t("should_not", lang, p=piece)
            if ok and "exact" in test and normalize(text) != normalize(test["exact"]):
                ok, why = False, t("no_match", lang) + f"\n  {t('expected', lang)}:\n" + \
                    "\n".join("    " + s for s in test["exact"].splitlines()) + \
                    f"\n  {t('got', lang)}:\n" + "\n".join("    " + s for s in (text.strip().splitlines() or [t("nothing", lang)]))
            if ok and "source_contains" in test:
                src = path.read_text(encoding="utf-8")
                for piece in test["source_contains"]:
                    if piece not in src:
                        ok, why = False, t("should_use", lang, p=piece)
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
    day = today()
    last = save.get("last_day")
    if last == day:
        return 0
    bonus = 0
    if last and (dt.date.fromisoformat(day) - dt.date.fromisoformat(last)).days == 1:
        save["streak"] += 1
        bonus = XP_STREAK
    else:
        save["streak"] = 1
    save["last_day"] = day
    save["best_streak"] = max(save.get("best_streak", 0), save["streak"])
    return bonus


def give(save: dict, amount: int, what: str, kind: str = "other") -> None:
    if amount <= 0:
        return
    before = level_for(save["xp"])
    save["xp"] += amount
    save["log"] = ([{"day": today(), "xp": amount, "what": what, "kind": kind}] + save["log"])[:30]
    print(c(f"  +{amount} XP  {what}", GOLD))
    EVENTS.append({"xp": amount, "what": what})
    after = level_for(save["xp"])
    if after[0] > before[0]:
        EVENTS.append({"levelUp": after[1]})
        print(c(t("level_up", n=after[0], name=after[1].upper()), GOLD + ";1"))


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
        return c("█" * 24, GOLD) + "  " + t("max")
    done = int(24 * (xp - lv[2]) / (nx[2] - lv[2]))
    return c("█" * done, GOLD) + c("░" * (24 - done), DIM) + f"  {nx[2] - xp} {t('xp_to')} {nx[1]}"


def rel(path: Path) -> Path:
    return path.relative_to(ROOT)


def cmd_status(exercises, save) -> None:
    lv = level_for(save["xp"])
    print()
    side = [
        c("PYTHON QUEST · " + load_config()["name"].upper(), GOLD + ";1"),
        f"{t('level')} {lv[0]} · {c(lv[1].upper(), BLUE + ';1')}",
        f"XP {save['xp']}",
        bar(save["xp"]),
        f"{t('streak')} {c(str(save['streak']) + ' ' + t('days'), CORAL)}  ({t('best')} {save.get('best_streak', 0)})",
        f"{t('exercises')} {len(save['passed'])}/{len(exercises)}",
        "",
        "",
    ]
    for art, text in zip(HERO, side):
        print(c(art, TEAL) + "  " + text)
    ex = find(exercises, None, save)
    print()
    if ex:
        print(f"  {t('next')}: {c(ex['id'], GOLD)}  {ex['title']}")
        print(f"  {t('open')}: {rel(work_file(ex))}")
        print(f"  {t('then')}: {c('python3 quest.py check', BOLD)}")
    else:
        print(c(t("all_done"), GOLD))
    print()


def cmd_next(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    lesson_md = lesson_readme(ex["folder"].parent, ex["lang"])
    path = work_file(ex)
    print()
    print(c(f"  {ex['id']} · {ex['title']}", GOLD + ";1"))
    if lesson_md.exists():
        print(c(f"  {t('lesson_notes')}: {rel(lesson_md)}", DIM))
    print()
    for line in ex["task"]:
        print(f"  • {line}")
    print()
    print(f"  {t('edit')}:  {rel(path)}")
    print(f"  {t('run')}:   cd {rel(ex['folder'])} && python3 {path.name}")
    print(f"  {t('check')}: python3 quest.py check {ex['id']}")
    print()


def cmd_check(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    print(c(t("checking", id=ex["id"], title=ex["title"]), BOLD))
    ok, report = run_tests(ex)
    print("\n".join(report))
    print()
    if not ok:
        if ex["id"] not in save["failed_once"]:
            save["failed_once"].append(ex["id"])
        write_save(save)
        print(c(t("not_yet"), CORAL))
        print(c(t("stuck"), DIM))
        print()
        return
    first_time = ex["id"] not in save["passed"]
    if not first_time:
        print(c(t("still"), TEAL))
        return
    save["passed"].append(ex["id"])
    print(c(t("passed"), TEAL + ";1"))
    give(save, touch_streak(save), t("streak_day", n=save["streak"]), "streak")
    if ex["id"] in save["seen_solution"]:
        print(c(t("no_xp_solution"), DIM))
    else:
        build = ex.get("build")
        give(save, XP_BUILD if build else XP_EXERCISE,
             t("xp_build" if build else "xp_ex", title=ex["title"]), "build" if build else "exercise")
        if ex["id"] in save["failed_once"]:
            give(save, XP_FIX, t("xp_fix"), "fix")
    # whole lesson done?
    lesson_key = f"{ex['module']}/{ex['lesson']}"
    siblings = [e["id"] for e in exercises if f"{e['module']}/{e['lesson']}" == lesson_key]
    if lesson_key not in save["lessons_done"] and all(s in save["passed"] for s in siblings) and not ex.get("build"):
        save["lessons_done"].append(lesson_key)
        give(save, XP_LESSON, t("xp_lesson", title=ex["lesson_title"]), "lesson")
    write_save(save)
    nxt = find(exercises, None, save)
    if nxt:
        print(t("next_up", id=nxt["id"], title=nxt["title"]))


def cmd_hint(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    hints = ex.get("hints", [])
    used = save["hints_used"].get(ex["id"], 0)
    if not hints:
        print(t("no_hints"))
        return
    shown = min(used + 1, len(hints))
    save["hints_used"][ex["id"]] = shown
    write_save(save)
    print()
    for i, h in enumerate(hints[:shown], 1):
        print(f"  {c(t('hint') + ' ' + str(i), GOLD)}: {h}")
    if shown < len(hints):
        print(c(t("hint_more"), DIM))
    print()


def cmd_solution(exercises, save, ex_id=None) -> None:
    ex = find(exercises, ex_id, save)
    if not ex:
        return
    if ex["id"] not in save["seen_solution"] and "--yes" not in sys.argv:
        print(c(t("sol_warn"), CORAL))
        print(t("sol_sure", id=ex["id"]))
        return
    if ex["id"] not in save["seen_solution"]:
        save["seen_solution"].append(ex["id"])
        write_save(save)
    sol = ex["folder"] / f"solution.{ex['lang']}.py"
    print()
    print(sol.read_text(encoding="utf-8"))


def cmd_list(exercises, save) -> None:
    modules = {m["id"]: m for m in json.loads((LESSONS / "modules.json").read_text(encoding="utf-8"))}
    lang = exercises[0]["lang"] if exercises else current_lang()
    current_module = None
    for ex in exercises:
        if ex["module"] != current_module:
            current_module = ex["module"]
            m = modules.get(current_module, {})
            print("\n" + c(str(m.get(lang, {}).get("land", current_module)).upper(), GOLD + ";1"))
        mark = c("✓", TEAL) if ex["id"] in save["passed"] else c("·", DIM)
        tag = c(t("build_tag"), BLUE) if ex.get("build") else ""
        print(f"  {mark} {ex['id']:8} {ex['title']}{tag}")
    print()


def cmd_verify() -> int:
    """Every solution passes and every starter fails, in every language."""
    bad = total = 0
    for lang in LANGS:
        for ex in load_exercises(lang):
            total += 1
            ok, report = run_tests(ex, ex["folder"] / f"solution.{lang}.py")
            print(("PASS " if ok else "FAIL ") + f"{ex['id']} [{lang}]")
            if not ok:
                bad += 1
                print("\n".join(report))
                continue
            starter_ok, _ = run_tests(ex, starter_path(ex, lang))
            if starter_ok and not ex.get("starter_may_pass"):
                bad += 1
                print(f"  starter already passes: {ex['id']} [{lang}]")
    print(f"\n{total - bad}/{total} exercises OK")
    return 1 if bad else 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not CONFIG_FILE.exists() and (not args or args[0] in ("status", "next", "check")) and sys.stdin.isatty():
        print(c(t("welcome_first", "en") + " / " + t("welcome_first", "es").strip(), GOLD + ";1"))
        cmd_setup()
    cmd = args[0] if args else "status"
    if cmd == "verify":
        return cmd_verify()
    exercises = load_exercises()
    save = load_save()
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
    else:
        print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
