#!/usr/bin/env bash
# One-time setup for Linux or WSL (Windows Subsystem for Linux).
set -e
echo "== Python Quest setup =="
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is missing. On Ubuntu/WSL run:  sudo apt update && sudo apt install -y python3"
  exit 1
fi
echo "✓ $(python3 --version)"
if command -v claude >/dev/null 2>&1; then
  echo "✓ Claude Code found: Pip will use your Claude account."
else
  echo "• Claude Code not found. Pip (the tutor) needs it. To install:"
  echo "    1. Install Node.js 18+:   sudo apt install -y nodejs npm   (or use nvm)"
  echo "    2. npm install -g @anthropic-ai/claude-code"
  echo "    3. Run 'claude' once and sign in with your Claude account."
fi
echo
echo "Next:"
echo "  python3 quest.py setup   # your name, language and hero color"
echo "  python3 quest.py web     # play in your browser"
echo "  python3 quest.py         # or play in the terminal"
