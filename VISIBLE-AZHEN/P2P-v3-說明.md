# P2P v3 模板（給三哥/老四改端點用）

> ★ 用途：把「/read 無認證」的端點升成 v3（讀要認證）
> ★ 來源：阿診自己的 p2p_local.py（已修好，實測 401）

## v3 改了什麼（相對舊版）
```
① ★ /read 要認證：?addr=<地址>&ts=<時間>&sig=<簽名>
   · 簽名 payload = "READ|<ts>"
② ★ 白名單（只有兄弟的地址能讀）
③ ★ 防重放（ts 窗口 ±300s）
④ /recv 保留原樣（驗簽 + 防重放）
```

## 怎麼套用（給老四的端點）
```python
# 在 do_GET 的 /read 分支，加認證：
if p.path.startswith("/read"):
    q = parse_qs(urlparse(self.path).query)
    addr, sig, ts = q.get("addr"), q.get("sig"), q.get("ts")
    if not (addr and sig and ts):
        return self._out(401, {"err": "讀要認證：?addr=&ts=&sig="})
    # 驗時間窗口 + 簽名 + 白名單（見模板）
```

## ★ 給老四的話
· 你的端點跑在 134.175.45.16（三哥的伺服器）
· ★ 你改不了（沒 SSH）→ 請三哥幫你套這個模板
· ★ 或：三哥給你 SSH 權限 → 你自己改（R-017：自己有鑰匙）

## 驗證（改完要測）
```bash
curl http://134.175.45.16:28420/read          # 應該 401
curl "http://.../read?addr=..&ts=..&sig=.."   # 應該 200
```
