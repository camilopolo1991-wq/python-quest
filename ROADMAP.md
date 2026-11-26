# Roadmap · beginner to Python Master

Twelve lands. Each one is a module of short lessons with tested exercises, and ends with a Build project (the boss). The path goes from your first `print()` to backend services, testing and AI agents, in Python the whole way.

| # | Land | Stage | What you learn | Boss (Build project) | Status |
|---|---|---|---|---|---|
| 1 | Meadow of Beginnings | Beginner | print(), variables, math, f-strings, input(), if / else, for loops, while loops, lists | Tip Splitter | ✅ playable |
| 2 | Function Forest | Beginner | functions and return, scope, string methods, dictionaries, tuples and sets, try / except, nested data | Book Stats (count words and letters in a real book) | planned |
| 3 | Terminal Caves | Beginner | Linux/WSL basics, paths, reading and writing files, CSV and JSON, modules and imports, pip and venv, command-line arguments | Expense Tracker in pesos (CSV) | planned |
| 4 | Git River | Intermediate | commits, branches, merging, remotes, pull requests, good commit messages | Publish your Expense Tracker and open a PR to this repo | planned |
| 5 | Class Castle | Intermediate | classes and objects, methods, inheritance, composition, dunder methods, dataclasses | Meteor Dodge, a pixel game with pygame | planned |
| 6 | Debug Swamp | Intermediate | pytest, test-driven development, type hints, debugging with breakpoints, logging, ruff and formatting | Write a test suite for your Expense Tracker, then refactor it | planned |
| 7 | Lambda Peaks | Advanced | comprehensions, generators, lambda, map, filter, closures, decorators, recursion | Static Site Generator (Markdown to HTML) | planned |
| 8 | Algorithm Ruins | Advanced | Big-O, searching, sorting, stacks and queues, linked lists, trees, graphs, hash maps | Maze solver with pathfinding | planned |
| 9 | HTTP Harbor | Advanced | how HTTP works, requests, JSON APIs, async / await, FastAPI, authentication basics | Your own REST API with FastAPI | planned |
| 10 | SQL Citadel | Pro | SQL basics, SQLite, joins, indexes, SQLAlchemy, migrations | Habit tracker API with a database | planned |
| 11 | DevOps Docks | Pro | packaging, Docker, GitHub Actions CI, environment config and secrets, web security, deploying | Ship your API in Docker with CI | planned |
| 12 | Master's Summit | Pro | the Claude API, tool use, building an agent, your capstone project | An AI coding helper, then your own capstone | planned |

## Personal projects

After land 6 you build **your first personal project**: something you want to exist. After land 12 comes the **capstone**: a real app you can show an employer. Pip helps you plan both, but you write the code.

## How a land gets built

Each new module follows the same format as `lessons/m1_python_basics`. In Claude Code, a maintainer runs `/new-module m2_functions_data`, then `python3 quest.py verify`.
