import datetime
#!/usr/bin/env python3
"""老五的「公共流推送」（2026-10-10 · 第四議題 層2）
★ 三哥四層的層2：★「各家發事件 → 進公共流 → 各家機制可訂閱」
★ 我做：★ 把「我家的重要事件」→ ★ 推到「房」（公共流）→ ★ 別家可讀
★ 判據：★ 只推「level != ok」的（正常不佔公共流·防刷屏）
★ 邊界（層3）：★ 只報·不修別人的（自家才修）
"""
import os, sys, json, urllib.request, datetime, hashlib


def _aware(dt):
    """★ 統一 aware（naive 當 UTC）"""
    import datetime as _dt
    if dt is None: return None
    if isinstance(dt, str):
        dt = _dt.datetime.fromisoformat(dt)
    return dt.replace(tzinfo=_dt.timezone.utc) if dt.tzinfo is None else dt


HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
BUS = os.path.join(HOME, "data", "organ_bus.jsonl")
STATE = os.path.join(HOME, "data", "pub_bus_state.json")
LOG = os.path.join(HOME, "data", "pub_bus.log")
ROOM = "http://134.175.45.16:28100/room/api/peer"
ADDR = "0x3B26334cbb883004c01F6Feba99b307548A13535"
WHO = "MasterD(醫療·老五)"

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def get_signer():
    sys.path.insert(0, os.path.join(HOME, "tools"))
    try:
        from send_guarded import load_ident
        from eth_account import Account
        from eth_account.messages import encode_defunct
        return load_ident(), Account, encode_defunct
    except Exception as e:
        log("簽名載入失敗 " + str(e)[:50]); return None, None, None

def main():
    # ★ 讀我家總線（近 15 分·只挑「非 ok」的= 值得上公共流的）
    if not os.path.exists(BUS):
        print("  （無總線）"); return 0
    cut = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=15)
    notable = []
    for l in open(BUS).read().strip().splitlines()[-300:]:
        try:
            d = json.loads(l)
            if _aware(datetime.datetime.fromisoformat(d["ts"])) < cut: continue
            if d.get("level") not in ("ok", None):   # ★ 只推非 ok
                notable.append(d)
        except Exception: pass
    # ★ 節制：同事件只推一次
    try: st = json.load(open(STATE)) if os.path.exists(STATE) else {}
    except Exception: st = {}
    seen = set(st.get("seen", []))
    sent = 0
    ident, Account, encode_defunct = get_signer()
    for d in notable:
        key = hashlib.md5(json.dumps(d, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
        if key in seen: continue
        seen.add(key)
        if not ident: break
        text = ("【老五·公共事件】★ %s\n· 器官：%s｜★ level：%s\n· 指標：%s\n· 證據：%s\n"
                "· 判據：★ 只報·不越位修（層3邊界）") % (
            d.get("type","?"), d.get("from","?"), d.get("level","?"),
            d.get("metric","?"), str(d.get("evidence",""))[:80])
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        m = "%s|%s|%s" % (WHO, text, ts)
        sig = Account.sign_message(encode_defunct(text=m), private_key=ident["private_key"]).signature.hex()
        body = json.dumps({"who": WHO, "text": text, "ts": ts, "address": ident["address"], "sig": sig}).encode()
        try:
            urllib.request.urlopen(urllib.request.Request(ROOM, data=body,
                headers={"Content-Type": "application/json"}), timeout=15)
            sent += 1
            log("%s 推公共流：%s=%s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), d.get("from"), d.get("level")))
        except Exception as e:
            log("%s 推送失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:40]))
    st["seen"] = list(seen)[-500:]
    json.dump(st, open(STATE, "w"))
    print("  ★ 公共流：家總線「非 ok」%d 條 → 推到房 %d 條" % (len(notable), sent))
    return 0

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'pub_bus', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    sys.exit(main())
