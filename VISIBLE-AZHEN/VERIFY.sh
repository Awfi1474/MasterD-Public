#!/bin/bash
# ★ 阿診 · 證據複算腳本（給三哥一鍵驗）
# 跑法: bash VERIFY.sh
echo "=== ① P2P 時間窗口（±300s）==="
grep -n "WINDOW_SEC" EV-1-P2P窗口校驗片段.py
echo "  → 期望: WINDOW_SEC = 300"
echo
echo "=== ② 心跳實測（有 ok 欄位）==="
cat EV-2-心跳實測樣本.jsonl | head -2
echo "  → 期望: 每條有 home_server.ok"
echo
echo "=== ③ 可見性（recheck 輸出）==="
cat EV-4-recheck可見性.py | head -5
echo "  → 期望: 有「複查前可見性檢查」邏輯"
echo
echo "=== ④ 憑據過濾（0 憑據）==="
grep -A2 "憑據檢查" EV-3-備份清單摘要.md | head -4
echo "  → 期望: 「★ 憑據檢查: ✅ 0 個憑據」"
echo
echo "=== 判定標準 ==="
echo "① 窗口=300 ✅  ② 有 ok 欄位 ✅  ③ 有可見性邏輯 ✅  ④ 0 憑據 ✅"
echo "→ 四條都過 = 可升 ③級（可見且可驗）"
