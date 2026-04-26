#!/usr/bin/env bash
# start.sh — Xvfb + x11vnc + noVNC + tkinter app を一括起動
set -e

DISPLAY_NUM=:99
VNC_PORT=5900
NOVNC_PORT=6080
APP_PORT=$NOVNC_PORT

echo "=== Web Image Downloader 起動中 ==="

# 既存プロセスをクリーンアップ
pkill -f "Xvfb $DISPLAY_NUM" 2>/dev/null || true
pkill -f "x11vnc"             2>/dev/null || true
pkill -f "websockify"         2>/dev/null || true
pkill -f "python3.12 main.py" 2>/dev/null || true
sleep 1

# 1. 仮想ディスプレイ起動
echo "[1/4] 仮想ディスプレイ (Xvfb) 起動..."
Xvfb $DISPLAY_NUM -screen 0 1280x800x24 -ac &
sleep 1

# 2. VNCサーバー起動（パスワードなし、ローカルのみ）
echo "[2/4] VNCサーバー (x11vnc) 起動..."
DISPLAY=$DISPLAY_NUM x11vnc \
  -display $DISPLAY_NUM \
  -rfbport $VNC_PORT \
  -nopw \
  -forever \
  -quiet \
  -bg

sleep 1

# 3. noVNC WebSocket プロキシ起動
echo "[3/4] noVNC プロキシ 起動..."
websockify \
  --web /usr/share/novnc/ \
  --wrap-mode=ignore \
  0.0.0.0:$NOVNC_PORT \
  localhost:$VNC_PORT \
  > /tmp/novnc.log 2>&1 &

sleep 1

# 4. tkinter アプリ起動
echo "[4/4] アプリ起動..."
DISPLAY=$DISPLAY_NUM python3.12 main.py &

sleep 2
echo ""
echo "======================================"
echo " アクセスURL: http://192.0.2.2:$NOVNC_PORT/vnc_auto.html"
echo "======================================"
echo " Ctrl+C で停止"
wait
