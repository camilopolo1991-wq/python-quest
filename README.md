# 🐍 Python Quest

**Learn Python from total beginner to Python Master, as a 16-bit RPG.** It runs on your own computer (Linux or WSL), you write real code in real files, automatic tests check it, and **your own Claude Code** is your tutor, Pip.

Inspired by how [Boot.dev](https://boot.dev) teaches: a short lesson, then code, then tests. A Build project closes every module. XP, levels and streaks keep you coming back.

```
   ▄▄▄▄▄▄     PYTHON QUEST · CAMILO
  █▀▀▀▀▀▀█    Level 7 · Apprentice 2
  █ ●  ● █    XP 640
  █  ▀▀  █    ████████████░░░░░░░░░░░░  120 XP to Apprentice 3
   ▀█▄▄█▀     Streak 4 day(s)  (best 9)
```

## Start (Linux or WSL)

```bash
git clone https://github.com/<you>/python-quest.git
cd python-quest
./scripts/setup.sh          # checks Python and Claude Code
python3 quest.py web        # opens the game in your browser
```

The first screen asks your name, your hero's color and which language Pip speaks. On WSL, open the address it prints (`http://127.0.0.1:8765`) in your Windows browser.

**Pip, the tutor**, uses the Claude Code installed on your computer, signed in with your Claude account. If you don't have it yet:

```bash
npm install -g @anthropic-ai/claude-code
claude        # sign in once
```

Prefer the terminal? Everything works there too:

| Command | What it does |
|---|---|
| `python3 quest.py` | Your hero, level, XP, streak and next exercise |
| `python3 quest.py next` | Instructions for your next exercise |
| `python3 quest.py check` | Run the tests on your code |
| `python3 quest.py hint` | A hint (free; run it again for a bigger one) |
| `python3 quest.py solution` | Show the solution (you lose that exercise's XP) |
| `python3 quest.py list` | The whole map |
| `python3 quest.py setup` | Change your name, language, color, daily goal |

Or open the repo in Claude Code and use `/lesson`, `/hint` and `/review`. The `CLAUDE.md` file tells Claude to teach you, not do the work for you.

## How the game works

| You do | XP |
|---|---|
| Pass an exercise | +10 |
| Pass after failing, without peeking at the solution | +10 bonus |
| Finish every exercise in a lesson | +50 |
| Beat a module's Build project (the boss) | +150 |
| Practice on another day in a row | +20 per day |

There are **60 levels** and **12 ranks**, a new rank every 5 levels: Curious, Apprentice, Coder, Builder, Debugger, Scripter, Hacker, Engineer, Architect, Wizard, Sage and **Python Master** at level 60. Each rank gives your hero new gear. The full course is worth about 18,000 XP, so reaching Python Master means finishing the whole course and practicing for months.

## The 12 lands

See [ROADMAP.md](ROADMAP.md). Module 1 (Meadow of Beginnings) is playable now. The others are planned and get added one module at a time.

## Your progress

Your save lives in `.quest/progress.json` and your settings in `.quest/config.json`. Both are gitignored, so they stay on your computer.

## For maintainers

Every exercise is a folder with `test.json` (task, hints, tests), a starter file and `solution.py`. `python3 quest.py verify` proves every solution passes and every starter fails, and it runs in GitHub Actions on every push.
