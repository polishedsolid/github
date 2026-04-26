#!/usr/bin/env bash
# setup.sh — venv 作成 + 依存関係インストール + アプリ起動
set -e

VENV_DIR="$(cd "$(dirname "$0")" && pwd)/.venv"

echo "=== Web Image Downloader セットアップ ==="
echo ""

# ── 動作する Python を探す ──────────────────────────────────────
find_python() {
  local candidates=(
    /opt/homebrew/bin/python3.13
    /opt/homebrew/bin/python3.12
    /opt/homebrew/bin/python3.11
    /opt/homebrew/bin/python3
    /usr/local/bin/python3.13
    /usr/local/bin/python3.12
    /usr/local/bin/python3.11
    /usr/local/bin/python3
    "$(command -v python3.13 2>/dev/null)"
    "$(command -v python3.12 2>/dev/null)"
    "$(command -v python3.11 2>/dev/null)"
  )

  for py in "${candidates[@]}"; do
    [ -z "$py" ] && continue
    [ ! -x "$py" ] && continue
    if "$py" -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
      if "$py" -c "
import subprocess, sys
r = subprocess.run([sys.executable, '-c',
  'import tkinter; w=tkinter.Tk(); w.destroy()'],
  capture_output=True, timeout=5)
exit(r.returncode)
" 2>/dev/null; then
        echo "$py"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON=$(find_python 2>/dev/null) || true

if [ -z "$PYTHON" ]; then
  echo "エラー: 動作する Python 3.11+ が見つかりませんでした。"
  echo ""
  echo "  brew install python@3.12 python-tk@3.12"
  echo ""
  exit 1
fi

echo "使用する Python: $PYTHON ($("$PYTHON" --version))"

# ── venv 作成（初回のみ）──────────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  echo "仮想環境を作成中: $VENV_DIR"
  "$PYTHON" -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"

# ── 依存関係インストール ────────────────────────────────────────
echo "依存関係をインストール中..."
"$VENV_PYTHON" -m pip install -q -r requirements.txt

# ── Playwright Chromium ────────────────────────────────────────
echo "Playwright (Chromium) をインストール中..."
"$VENV_PYTHON" -m playwright install chromium

echo ""
echo "セットアップ完了。アプリを起動します..."
echo ""

"$VENV_PYTHON" main.py
