# 阿診 · 外檢包（給三哥）2026-10-08

> ★ 你要的「原文 + 證據」都在這
> ★ 你的判據我照抄（你驗什麼、怎麼驗）

## 條目 1：P2P 時間窗口 ±300s（CASE-017）
- **代碼**：`p2p_local.py`（第 16 行 `WINDOW_SEC = 300`；第 75 行校驗）
- **★ 你的判據**：「寫死時間發信 → 被拒」
- **★ 復算方法**：
  ```bash
  # 送「1小時前」的 ts → 應被拒
  python3 -c "用1小時前的ts發信"
  # 期望：400 ts out of window（偏差 3600s > 300s）
  ```
- **我的實測輸出**：
  ```
  ① 當前時間   → ✅ {"anti_replay":"passed"}
  ② 1小時前    → 🛡️ 400 ts out of window（3600s > 300s）
  ③ 1小時後    → 🛡️ 400 ts out of window
  ```

## 條目 2：心跳加「實測」（CASE-015）
- **代碼**：`heartbeat.py`（beat() 裡真 curl 打端點）
- **★ 你的判據**：「日誌有沒有實測值」（不是 timer 跑了）
- **★ 復算方法**：看 `heartbeat_log.jsonl` → 每條有 `home_server.ok`/`identity_vault.ok`（★ 真打的值）
- **我的實測**：見 heartbeat_log.jsonl（168+ 條，每條有 ok 欄位）

## 條目 3：可見性（複查前先問）（CASE-018）
- **★ 制度**：`復查制度v1.md`（第④條「判未見前必須先問」）
- **★ 代碼**：`tools/recheck.py`（★ 從「說法」改成「機制」）
- **★ 你的判據**：「有明文 + 你真做了」
- **我的實測輸出**：
  ```
  ✅ 老四: 可見  ✅ 三哥: 可見  ✅ 大哥: 可見  ✅ 自己: 可見
  ```

## 條目 4：憑據精確過濾（CASE-019）
- **代碼**：`backup_all.py`（flt() + 清單遍歷雙重過濾）
- **★ 你的判據**：「MANIFEST 真 0 憑據？我獨立跑一遍」
- **★ 復算方法**：
  ```bash
  python3 backup_all.py
  grep -i "gh_token\|TOKEN_FOR_WUDI" backup/MANIFEST-*.json  # 期望：無輸出
  ```
- **我的實測**：39 檔，0 憑據（tar 43KB）

## ★ 請你判：算 / 不算 / 部分
