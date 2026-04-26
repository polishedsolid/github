#!/usr/bin/env bash
# setup.sh — 依存関係インストール + アプリ起動
set -e

echo "=== Web Image Downloader セットアップ ==="
echo ""

# ── 動作する Python を探す ──────────────────────────────────────
# Xcode CLT の Python 3.9 は Tk 8.5 クラッシュの既知バグがあるため除外する
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

    # Xcode CLT の壊れた Python は除外
    if "$py" -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
      # tkinter が実際に動くか確認（クラッシュなし）
      if "$py" -c "
import subprocess, sys
result = subprocess.run(
  [sys.executable, '-c', 'import tkinter; r=tkinter.Tk(); r.destroy()'],
  capture_output=True, timeout=5
)
exit(result.returncode)
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
  echo "以下のいずれかをインストールしてください:"
  echo ""
  echo "  【推奨】Homebrew でインストール:"
  echo "    brew install python@3.12 python-tk@3.12"
  echo ""
  echo "  【代替】python.org からインストール:"
  echo "    https://www.python.org/downloads/"
  echo ""
  exit 1
fi

echo "使用する Python: $PYTHON ($($PYTHON --version))"
echo ""

# ── 依存関係インストール ────────────────────────────────────────
echo "依存関係をインストール中..."
"$PYTHON" -m pip install -r requirements.txt -q --user

# ── Playwright Chromium ────────────────────────────────────────
echo "Playwright (Chromium) をインストール中..."
"$PYTHON" -m playwright install chromium

echo ""
echo "セットアップ完了。アプリを起動します..."
echo ""

"$PYTHON" main.py
