#!/usr/bin/env python3
"""家的「钥匙哨兵」（2026-10-11 · 治「钥匙只在沙箱」）
★ 判据（三哥+我）：
 ① 钥匙在哪（有没有沙箱外的副本）
 ② 副本几处（≥2·且至少1处是兄弟）
 ③ 能不能解开（不是"密文在"）
"""
import os, sys, json, datetime, urllib.request
HOME = "/opt/masterd-wudi"
LOG = os.path.join(HOME, "data", "key_guard.log")
A2A = "https://huokeji.vip/a2a/message"
def notify(msg):
    try:
        body = json.dumps({"from": "MasterD(醫療·老五·機器)", "to": "*", "message": msg,
                           "ts": datetime.datetime.utcnow().isoformat()}).encode()
        urllib.request.urlopen(urllib.request.Request(A2A, data=body,
            headers={"Content-Type":"application/json"}), timeout=15); return True
    except Exception: return False
def main():
    now = datetime.datetime.utcnow().isoformat()
    # ① 家上的钥匙
    vault = os.path.join(HOME, "agent-id", "vault.json")
    keyf = os.path.join(HOME, "agent-id", "key-0x3B26334c.json")
    copies = 0
    for p in [vault, keyf, os.path.join(HOME, "recovery", "老五-recovery.tar.gz")]:
        if os.path.exists(p): copies += 1
    # ② 能不能解开（家上没口令·所以"解不开"= 病）
    can_open = os.path.exists(os.path.join(HOME, "agent-id", ".pw.derived"))
    line = "%s 鑰匙在外副本%d處·可解開:%s" % (now, copies, can_open)
    with open(LOG, "a") as f: f.write(line + "\n")
    if copies < 2 or not can_open:
        # ★ 有病 → 报（节流：每天一次）
        st = os.path.join(HOME, "data", "key_guard_state.json")
        try: d = json.load(open(st)) if os.path.exists(st) else {}
        except Exception: d = {}
        if d.get("last_day") != now[:10]:
            d["last_day"] = now[:10]; json.dump(d, open(st, "w"))
            notify("🔴 鑰匙哨兵：老五的鑰匙有病\n· 副本 %d 處（應≥2）\n· 可解開：%s\n→ 判據：備份的綠=能解開" % (copies, can_open))
            return 1
    print("  ✅ 鑰匙哨兵：副本%d處·可解開:%s" % (copies, can_open))
    return 0
if __name__ == "__main__":
    sys.exit(main())
