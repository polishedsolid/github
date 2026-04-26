#!/usr/bin/env bash
# setup.sh — 依存関係インストール + アプリ起動
set -e

# Python3 確認
if ! command -v python3 &>/dev/null; then
  echo "エラー: python3 が見つかりません。"
  echo "https://www.python.org/downloads/ からインストールしてください。"
  exit 1
fi

PYTHON=$(command -v python3)
echo "Python: $($PYTHON --version)"

# tkinter 確認
if ! $PYTHON -c "import tkinter" 2>/dev/null; then
  echo ""
  echo "エラー: tkinter が見つかりません。"
  echo "python.org からインストールした Python を使うか、以下を実行してください:"
  echo "  brew install python-tk"
  exit 1
fi

# pip 依存関係インストール
echo "依存関係をインストール中..."
$PYTHON -m pip install -r requirements.txt -q

# Playwright ブラウザインストール
echo "Playwright (Chromium) をインストール中..."
$PYTHON -m playwright install chromium

echo ""
echo "セットアップ完了。アプリを起動します..."
echo ""

$PYTHON main.py
