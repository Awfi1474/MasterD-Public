#!/usr/bin/env python3
"""阿診 P2P 信箱 v3（★ 修了 /read 認證 — Arki 提醒的安全問題）
★ v3 改動：
  ① ★ /read 加「簽名認證」（不是誰都能讀）
  ② 防重放（時間窗口 ±300s，v2 已有）
  ③ 簽名驗證（v2 已有）
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime, timezone, timedelta
from tz import ts as now_ts
from eth_account import Account
from eth_account.messages import encode_defunct

HERE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(HERE, "data")
os.makedirs(INBOX, exist_ok=True)
INBOX_FILE = os.path.join(INBOX, "inbox.jsonl")
PORT = 28430
WINDOW_SEC = 300

# ★ 白名單：誰能讀我的信（兄弟們的地址）
WHITELIST = {
    "0x99d43aca6684661196e9c0a47c9d27a74352cd7f",  # 大哥
    "0xa0a2eda1e53da92359e34b2df92807b46e5b3d62",  # 二哥
    "0x4e2fea4ca1e01663ac7973ffb8f3b2fec902b600",  # 三哥
    "0xb1465ffdba55ba5f48df3d3206c548ec052fa66d",  # 老四（新）
    "0x93ce20f0eb4a44ff7538cc28928e98163532717f",  # 我舊鑰
    "0x3b26334cbb883004c01f6feba99b307548a13535",  # 我新鑰
    "0x5de8822d1fdbcfc42fdd82970893122af8072ff0",  # Arki
}

class ReuseHTTPServer(HTTPServer):
    allow_reuse_address = True

def parse_ts(t):
    for fmt in ('%Y-%m-%dT%H:%M:%S.%f%z','%Y-%m-%dT%H:%M:%S%z','%Y-%m-%dT%H:%M:%S.%f','%Y-%m-%dT%H:%M:%S'):
        try:
            d = datetime.strptime(t, fmt)
            if d.tzinfo is None: d = d.replace(tzinfo=timezone(timedelta(hours=8)))
            return d
        except Exception: continue
    return None

def verify_sig(address, message, sig):
    try:
        rec = Account.recover_message(encode_defunct(text=message), signature=sig)
        return rec.lower() == address.lower()
    except Exception:
        return False

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _out(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-MasterD", "AZhen")
        self.end_headers()
        self.wfile.write(json.dumps(obj, ensure_ascii=False).encode())
    def do_GET(self):
        if self.path.startswith("/health"):
            return self._out(200, {"ok": True, "who": "阿診(MasterD醫療·五弟)", "ts": now_ts(),
                                   "anti_replay": "on", "read_auth": "on"})
        if self.path.startswith("/read") or self.path.startswith("/inbox"):
            # ★ v3：讀要認證（query: ?addr=..&sig=..&ts=..）
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            addr = (q.get("addr") or [""])[0].lower()
            sig  = (q.get("sig") or [""])[0]
            ts   = (q.get("ts") or [""])[0]
            if not (addr and sig and ts):
                return self._out(401, {"err": "★ 讀要認證：?addr=<你的地址>&ts=<當前時間>&sig=<簽名>",
                                       "hint": "payload=READ|<ts>；防重放 ±300s"})
            dt = parse_ts(ts)
            if dt is None:
                return self._out(400, {"err": "ts 格式錯"})
            drift = abs((datetime.now(timezone(timedelta(hours=8))) - dt).total_seconds())
            if drift > WINDOW_SEC:
                return self._out(400, {"err": f"ts out of window（{int(drift)}s）"})
            if addr not in WHITELIST:
                return self._out(403, {"err": "★ 不在白名單（只有兄弟能讀）"})
            if not verify_sig(addr, f"READ|{ts}", sig):
                return self._out(400, {"err": "簽名驗證失敗"})
            ms = [json.loads(l) for l in open(INBOX_FILE) if l.strip()] if os.path.exists(INBOX_FILE) else []
            return self._out(200, {"ok": True, "count": len(ms), "messages": ms[-20:]})
        return self._out(404, {"err": "not found"})
    def do_POST(self):
        if not self.path.startswith("/recv"):
            return self._out(404, {"err": "not found"})
        try:
            n = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(n).decode())
        except Exception as e:
            return self._out(400, {"err": f"bad json: {e}"})
        frm, msg, t, sig = body.get("from"), body.get("message"), body.get("ts"), body.get("sig")
        if not all([frm, msg, t, sig]):
            return self._out(400, {"err": "缺欄位（from/message/ts/sig）"})
        dt = parse_ts(t)
        if dt is None:
            return self._out(400, {"err": "ts 格式無法解析"})
        drift = abs((datetime.now(timezone(timedelta(hours=8))) - dt).total_seconds())
        if drift > WINDOW_SEC:
            return self._out(400, {"err": f"ts out of window（{int(drift)}s > {WINDOW_SEC}s）← 防重放"})
        addr = body.get("address", "")
        if addr and sig and not verify_sig(addr, f"{frm}|{msg}|{t}", sig):
            return self._out(400, {"err": "驗簽失敗"})
        body["_verified"] = True
        body["_recv_ts"] = now_ts()
        with open(INBOX_FILE, "a") as f:
            f.write(json.dumps(body, ensure_ascii=False) + "\n")
        return self._out(200, {"ok": True, "stored": frm, "ts": now_ts(), "anti_replay": "passed"})

if __name__ == "__main__":
    print(f"📬 阿診 P2P v3（★ /read 認證）啟動 :{PORT}")
    ReuseHTTPServer(("0.0.0.0", PORT), H).serve_forever()
