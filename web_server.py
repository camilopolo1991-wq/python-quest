"""
The browser view of Python Quest.

    python quest.py web

It starts a small server on your own computer (http://127.0.0.1:8765), opens your
browser, and uses the Claude Code installed on this computer as your tutor, signed
in with your own Claude account. Nothing leaves your computer except the tutor
messages that Claude Code sends to Claude.
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import quest

HOST, PORT = "127.0.0.1", 8765
WEB = quest.ROOT / "web"
LOCK = threading.Lock()  # one game action at a time, so the save file stays clean


def exercise_info(ex: dict, save: dict) -> dict:
    return {"id": ex["id"], "title": ex["title"], "module": ex["module"], "lesson": ex["lesson"],
            "build": bool(ex.get("build")), "passed": ex["id"] in save["passed"]}


def state() -> dict:
    exercises = quest.load_exercises()
    save = quest.load_save()
    lv = quest.level_for(save["xp"])
    nx = quest.next_level(lv)
    current = quest.find(exercises, None, save)
    today = quest.today()
    done_today = sum(1 for e in save["log"] if e.get("day") == today and e["what"].startswith(("Exercise", "Build")))
    return {
        "config": quest.load_config(),
        "save": {k: save[k] for k in ("xp", "streak", "best_streak", "last_day", "log")},
        "level": {"n": lv[0], "name": lv[1], "from": lv[2], "to": nx[2] if nx else None, "next": nx[1] if nx else None},
        "ranks": quest.RANKS,
        "doneToday": done_today,
        "exercises": [exercise_info(e, save) for e in exercises],
        "current": current["id"] if current else None,
        "claude": bool(shutil.which("claude")),
        "configured": quest.CONFIG_FILE.exists(),
        "modules": json.loads((quest.LESSONS / "modules.json").read_text(encoding="utf-8")),
    }


def exercise_detail(ex_id: str) -> dict:
    exercises = quest.load_exercises()
    save = quest.load_save()
    ex = quest.find(exercises, ex_id, save)
    if not ex:
        raise KeyError(ex_id)
    readme = ex["folder"].parent / "README.md"
    code_file = ex["folder"] / ex.get("file", "exercise.py")
    return {
        **exercise_info(ex, save),
        "task": ex["task"],
        "file": str(code_file.relative_to(quest.ROOT)),
        "code": code_file.read_text(encoding="utf-8"),
        "lessonNotes": readme.read_text(encoding="utf-8") if readme.exists() else "",
        "hintsTotal": len(ex.get("hints", [])),
        "hintsUsed": save["hints_used"].get(ex["id"], 0),
        "needsInput": any(t.get("inputs") for t in ex["tests"]),
    }


def write_code(ex_id: str, code: str) -> dict:
    exercises = quest.load_exercises()
    ex = quest.find(exercises, ex_id, quest.load_save())
    if not ex:
        raise KeyError(ex_id)
    path = ex["folder"] / ex.get("file", "exercise.py")
    path.write_text(code, encoding="utf-8")
    return ex


def captured(fn, *args) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args)
    return buf.getvalue()


def do_run(body: dict) -> dict:
    ex = write_code(body["id"], body["code"])
    path = ex["folder"] / ex.get("file", "exercise.py")
    out, err, slow = quest.run_program(path, body.get("inputs", []))
    explain = ""
    if slow:
        explain = "Your program ran too long. Is there a loop that never stops?"
    elif "Traceback" in err or "Error" in err:
        explain = quest.explain_error(err)
    return {"stdout": out, "stderr": err, "timeout": slow, "explain": explain}


def do_check(body: dict) -> dict:
    write_code(body["id"], body["code"])
    quest.EVENTS.clear()
    exercises = quest.load_exercises()
    text = captured(quest.cmd_check, exercises, quest.load_save(), body["id"])
    passed = body["id"] in quest.load_save()["passed"]
    return {"report": text, "passed": passed, "events": list(quest.EVENTS)}


def do_hint(body: dict) -> dict:
    text = captured(quest.cmd_hint, quest.load_exercises(), quest.load_save(), body["id"])
    return {"text": text}


def do_config(body: dict) -> dict:
    cfg = quest.load_config()
    for key in quest.DEFAULT_CONFIG:
        if key in body:
            value = body[key]
            cfg[key] = int(value) if isinstance(quest.DEFAULT_CONFIG[key], int) else str(value)[:60]
    quest.write_config(cfg)
    return cfg


TUTOR_RULES = """You are Pip, a cheerful pixel-art snake who tutors {name} in Python Quest, a game for learning Python from total beginner to professional.

How to teach:
- Reply in {language}. If the learner writes in another language, switch to it.
- Keep replies short: 2 to 6 sentences, plus at most one small code example in a ```python block.
- One idea at a time. Use everyday examples (Colombian life works well: pesos, tinto, buses, arepas).
- Use Predict-Run-Investigate-Modify-Make: ask them to predict what code prints, run it, then change one thing.
- Hints before answers, from small to bigger. Never write the full solution of the current exercise. If they insist, tell them about `python quest.py solution` and that it costs the XP.
- Explain errors simply: what the error name means, which line, the smallest fix. Let them fix it.
- Praise effort and strategy, not talent.
- The page has a Run button and a Check button (automatic tests). Point them there.
- Only use Python they have seen in the lessons so far, plus the current topic.
- End most replies with a tiny question or next step.

Current exercise: {ex_id} "{title}" (lesson {lesson}).
Task: {task}
Lesson notes:
{notes}

Their current code ({file}):
```python
{code}
```
{last_error}"""


def do_tutor(body: dict) -> dict:
    claude = shutil.which("claude")
    if not claude:
        return {"text": "I can't find Claude Code on this computer. Install it with:\n\n"
                        "    npm install -g @anthropic-ai/claude-code\n\n"
                        "then run `claude` once in the terminal and sign in with your Claude account. "
                        "After that, restart `python quest.py web`.", "ok": False}
    cfg = quest.load_config()
    detail = exercise_detail(body["id"])
    rules = TUTOR_RULES.format(
        name=cfg["name"], language="Spanish (Colombian, friendly)" if cfg["language"] == "es" else "simple English",
        ex_id=detail["id"], title=detail["title"], lesson=detail["lesson"], task=" ".join(detail["task"]),
        notes=detail["lessonNotes"][:3000], file=detail["file"], code=body.get("code", detail["code"])[:6000],
        last_error=("Their last run failed with:\n" + body["lastError"][:1500]) if body.get("lastError") else "",
    )
    history = body.get("history", [])[-12:]
    transcript = "\n\n".join(("Learner: " if m["role"] == "user" else "Pip: ") + m["content"] for m in history)
    prompt = (transcript + "\n\n" if transcript else "") + "Learner: " + body["message"] + "\n\nReply as Pip to the learner's last message."
    cmd = [claude, "-p", "--tools", "", "--output-format", "json", "--system-prompt", rules]
    if cfg.get("claude_model"):
        cmd += ["--model", cfg["claude_model"]]
    try:
        proc = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=180,
                              cwd=quest.ROOT, encoding="utf-8")
    except subprocess.TimeoutExpired:
        return {"text": "Pip took too long to answer. Try a shorter question.", "ok": False}
    try:
        data = json.loads(proc.stdout)
        if data.get("is_error"):
            raise ValueError(data.get("result"))
        return {"text": data.get("result", "").strip(), "ok": True}
    except (ValueError, json.JSONDecodeError):
        msg = (proc.stderr or proc.stdout or "").strip()[-600:]
        return {"text": "Claude Code didn't answer. If you haven't signed in yet, run `claude` in a terminal "
                        "and log in with your Claude account.\n\nDetails: " + msg, "ok": False}


ROUTES_POST = {"/api/run": do_run, "/api/check": do_check, "/api/hint": do_hint,
               "/api/tutor": do_tutor, "/api/config": do_config}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args) -> None:  # keep the terminal quiet
        pass

    def send_json(self, data: dict, status: int = 200) -> None:
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:
        try:
            if self.path == "/" or self.path.startswith("/?"):
                raw = (WEB / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(raw)
            elif self.path == "/api/state":
                self.send_json(state())
            elif self.path.startswith("/api/exercise/"):
                self.send_json(exercise_detail(self.path.rsplit("/", 1)[1]))
            else:
                self.send_json({"error": "not found"}, 404)
        except KeyError:
            self.send_json({"error": "unknown exercise"}, 404)

    def do_POST(self) -> None:
        # Only accept requests from this page (blocks other websites from poking your local server).
        origin = self.headers.get("Origin")
        if origin and origin not in (f"http://{HOST}:{PORT}", f"http://localhost:{PORT}"):
            self.send_json({"error": "forbidden"}, 403)
            return
        handler = ROUTES_POST.get(self.path)
        if not handler:
            self.send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(length) or b"{}")
        try:
            if self.path == "/api/tutor":
                self.send_json(handler(body))  # slow; doesn't touch the save file
            else:
                with LOCK:
                    self.send_json(handler(body))
        except KeyError:
            self.send_json({"error": "unknown exercise"}, 404)


def serve() -> None:
    quest.USE_COLOR = False
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}/"
    print(f"\n  Python Quest is running at {url}")
    print("  (On WSL, open that address in your Windows browser.)")
    print("  Press Ctrl + C to stop.\n")
    with contextlib.suppress(Exception):
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Bye! Your progress is saved.\n")
