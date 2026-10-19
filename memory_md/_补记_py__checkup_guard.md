# [补记·py] checkup_guard

> kind=器官 | who=老五 | ts=2026-10-15T04:26:17.663238+00:00

!/usr/bin/env python3 老五的「體檢推送」機制層（2026-10-10 · 第三議題·配合 P1-P5） ★ 機制層（定時兜底·穩） ★ P1 模組→機制：讀事件（checkup_events.jsonl） ★ P2 機制→模組：查模組心跳（checkup_mod_beat.json）→ 太舊=沒跑 → 代跑 ★ P3 雙向事件：機制修完 → 寫「複檢請求」→ 模組複檢（另一方
