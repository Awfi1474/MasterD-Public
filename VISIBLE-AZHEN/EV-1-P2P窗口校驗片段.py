from eth_account.messages import encode_defunct

HERE = os.path.dirname(os.path.abspath(__file__))
INBOX = os.path.join(HERE, "data")
os.makedirs(INBOX, exist_ok=True)
INBOX_FILE = os.path.join(INBOX, "inbox.jsonl")
PORT = 28430
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
