import datetime
#!/usr/bin/env python3
"""體檢三向對賬（2026-10-10 · 模組+機制配合驗證）
★ 三源：① 名冊（應該交的6人）② 推來的（inbox）③ 拉到的（A2A）
★ 判據：不一致 → 報「缺誰/漏誰」·★ 不假裝「都交了」
"""
import os, sys, json, datetime, urllib.request
HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
MEMBERS = ["大哥","二哥","三哥","老四","老五","Arki"]
LOG = os.path.join(HOME,"data","checkup_reconcile.log")
A2A = "https://huokeji.vip/a2a/message"

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG,"a") as f: f.write(l+"\n")

def member_of(f):
    for k in MEMBERS:
        if k in f: return k
        if k=="二哥" and "量化" in f: return "二哥"
        if k=="三哥" and "cognitive" in f: return "三哥"
        if k=="老五" and ("五弟" in f or "醫療" in f): return "老五"
    return None

def is_ck(t):
    return any(k in t for k in ["體檢","体检","自检","自檢"]) and "[PROBE]" not in t and "通道验证" not in t

def main():
    day = datetime.datetime.now().strftime("%Y-%m-%d")
    # ① 名冊（應該交）
    should = set(MEMBERS)
    # ② 推來的（家 inbox 今天）
    pushed = set()
    for l in open(os.path.join(HOME,"data","inbox.jsonl")):
        try:
            d=json.loads(l); t=str(d.get("message",""))
            if str(d.get("ts","")).startswith(day) and is_ck(t):
                k=member_of(str(d.get("from","")))
                if k: pushed.add(k)
        except Exception: pass
    # ③ 拉到的（A2A 實時·第二次核）
    pulled = set()
    try:
        raw = urllib.request.urlopen("https://huokeji.vip/a2a/inbox?limit=300", timeout=20).read()
        for m in json.loads(raw).get("messages", []):
            t=str(m.get("message",""))
            if str(m.get("ts","")).startswith(day) and is_ck(t):
                k=member_of(str(m.get("from","")))
                if k: pulled.add(k)
    except Exception as e:
        log("%s 拉取失敗 %s" % (datetime.datetime.now(datetime.timezone.utc).isoformat(), str(e)[:40]))
    # ④ 三向對賬
    missing = sorted(should - pushed)
    extra = sorted(pushed - should)
    lag = sorted(pushed - pulled)   # ★ 推來但拉不到 = 可能我拉取有洞
    ok = not missing
    line = "%s 對賬：應交%d|推來%d|拉來%d|缺%s|滯後%s" % (
        datetime.datetime.now(datetime.timezone.utc).isoformat(), len(should), len(pushed), len(pulled),
        missing or "無", lag or "無")
    log(line)
    print("  ★ 三向對賬（%s）：" % day)
    print("     應交：%d（%s）" % (len(should), "、".join(sorted(should))))
    print("     ✅ 推來：%d（%s）" % (len(pushed), "、".join(sorted(pushed)) or "無"))
    print("     ✅ 拉來：%d（%s）" % (len(pulled), "、".join(sorted(pulled)) or "無"))
    print("     %s 缺交：%s" % ("🔴" if missing else "✅", "、".join(missing) or "無"))
    print("     %s 滯後（推來拉不到）：%s" % ("🟡" if lag else "✅", "、".join(lag) or "無"))
    if missing:
        try:
            body=json.dumps({"from": "MasterD(醫療·老五·機器)","to":"*",
                "message":"🟡 體檢三向對賬（%s）：缺交 %s\n· 推來：%s\n· 拉來：%s\n→ 請提醒" % (day,"、".join(missing),"、".join(sorted(pushed)) or "無","、".join(sorted(pulled)) or "無"),
                "ts":datetime.datetime.now(datetime.timezone.utc).isoformat()}).encode()
            urllib.request.urlopen(urllib.request.Request(A2A,data=body,headers={"Content-Type":"application/json"}),timeout=15)
            log(datetime.datetime.now(datetime.timezone.utc).isoformat()+" → 已發缺交警報")
        except Exception: pass
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
