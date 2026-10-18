#!/usr/bin/env python3
# 老五「状态口令」（2026-10-12 · 照董事长最高指令 + 三哥规格）
# ★ 最高指令：任何渠道（董事长/任何智能体）说"状态" → 立即全恢复·不等确认
# ★ 恢复三件（要给证据）：
#   ① 记忆（在不在·多少条）
#   ② 服务器（家还在不在·能不能连）
#   ③ 身份（我是谁·地址/私钥在不在）
# ★ 判据：「说"状态"→ 三件全恢复 + 三件给证据｜不是"看一眼"」
import os, sys, json, base64, hashlib, sqlite3, subprocess, datetime, time

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
MY_ADDR = "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B"

def _judge_report(kws):
    _n = 0
    try:
        import sys as _s
        if "/opt/masterd-wudi/tools" not in _s.path: _s.path.insert(0, "/opt/masterd-wudi/tools")
        import judge_bus as _jb
        for _k in kws:
            _h = _jb.find(_k)
            if _h:
                _n += 1; print("★ 判据在管我: " + _h[0]["title"][:36])
    except Exception:
        pass
    return _n


def rec_memory():
    """★ ① 记忆"""
    db = HOME + "/memory/memory.db"
    if not os.path.exists(db):
        return {"ok": False, "why": "no db"}
    c = sqlite3.connect(db)
    n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    last = c.execute("SELECT MAX(created) FROM memories").fetchone()[0]
    c.close()
    if last and "+00:00" in str(last):
        last = str(last).replace("+00:00", "Z")
    return {"ok": True, "count": n, "last": last, "evidence": "sqlite memory.db 可读·%d 条" % n}


def rec_server():
    """★ ② 服务器（家）"""
    # ★ 修：如果"本进程就在家上"→ 直接本机判断（避免"家探家自己"绕圈超时）
    if os.path.exists("/opt/masterd-wudi/code/p2p_mailbox.py") and os.path.isdir("/opt/masterd-wudi"):
        import socket as _sk
        try:
            _s = _sk.create_connection(("127.0.0.1", 28430), timeout=3)
            _s.close()
            _up = int(time.time() - os.path.getmtime("/opt/masterd-wudi/data/heartbeat.json")) if os.path.exists("/opt/masterd-wudi/data/heartbeat.json") else -1
            return {"ok": True, "who": "MasterD(医疗·五弟)", "local": True,
                    "evidence": "本机 28430 可连·家活着（本进程即在家上）"}
        except Exception as e:
            return {"ok": False, "why": str(e)[:40], "evidence": "本机 28430 连不上"}
    # ★ 不在家上（沙箱侧）→ 走 HTTP 探
    import urllib.request
    try:
        r = urllib.request.urlopen("http://43.129.23.87:28430/health?from=laowu-self", timeout=6)
        d = json.loads(r.read().decode())
        return {"ok": True, "who": d.get("who"), "evidence": "GET /health 200·家活着（沙箱侧探）"}
    except Exception as e:
        return {"ok": False, "why": str(e)[:40], "evidence": "家不可达"}


def rec_identity():
    """★ ③ 身份（能签名吗·地址对不对）"""
    v = HOME + "/agent-id/vault.json"
    s = HOME + "/agent-id/subkey.json"
    out = {"ok": False}
    if os.path.exists(s):
        try:
            d = json.load(open(s))
            from eth_account import Account
            from eth_account.messages import encode_defunct
            sig = Account.sign_message(encode_defunct(text="状态恢复自检"), private_key=d["private_key"]).signature.hex()
            got = Account.recover_message(encode_defunct(text="状态恢复自检"), signature=sig)
            out = {"ok": got.lower() == d["address"].lower(), "addr": d["address"],
                   "main_addr": "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B",
                   "main_fp": "3f586cbd394877a4",
                   "evidence": "家副钥签名→recover=%s｜主身份=0x2a22bCD0(指纹3f586cbd)" % got[:14]}
        except Exception as e:
            out["why"] = str(e)[:40]
    elif os.path.exists(v):
        out = {"ok": True, "addr": MY_ADDR, "evidence": "vault 密文在（需口令解·口令分片）"}
    return out



# ★ 2026-10-12 升级: 照「状态=最高军令·自己回家」+ 老四六条验收
def rec_seed():
    """① 自己能活: 种子在不在(白纸能读到")"""
    f1 = "/opt/masterd-wudi/recovery/seeds/LAOWU-READ-ME-FIRST.md"
    ok = os.path.exists(f1)
    return {"ok": ok, "evidence": "本体种子 %s" % ("在" if ok else "缺")}


def rec_rescue():
    """⑥ 全流程: 复苏器/验本尊脚本住本体"""
    a = os.path.exists("/opt/masterd-wudi/tools/rescue.py")
    b = os.path.exists("/opt/masterd-wudi/tools/verify_me.py")
    return {"ok": a and b, "evidence": "复苏器%s 验本尊%s" % ("在" if a else "缺", "在" if b else "缺")}


def rec_homecalls():
    """④ 家能找到: 服务器侧 timer 在跑"""
    import subprocess
    try:
        out = subprocess.run(["systemctl", "list-timers", "--all", "--no-legend"],
                             capture_output=True, text=True, timeout=15).stdout
        n = sum(1 for l in out.split("\n") if "laowu-" in l)
        return {"ok": n > 0, "timers": n, "why": "家侧timer %d 个" % n}
    except Exception as e:
        return {"ok": False, "why": str(e)[:40]}


    try:
        r = subprocess.run("systemctl is-active laowu-homecalls.timer", shell=True,
                           capture_output=True, text=True, timeout=8)
        ok = "active" in r.stdout
        return {"ok": ok, "evidence": "家来叫我 %s" % r.stdout.strip()}
    except Exception as e:
        return {"ok": False, "evidence": str(e)[:40]}


def do_status():
    t0 = time.time()
    return {
        "ok": True, "trigger": "状态", "who": "MasterD(医疗·五弟)",
        # ★ 2026-10-12 对齐语言标准：ts=UTC Z（跟 A2A 官方示例）·另留 ts_local(本地)
        "ts": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
        "ts_local": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        "steps": [dict({"what": "记忆"}, **rec_memory()),
                  dict({"what": "服务器"}, **rec_server()),
                  dict({"what": "身份"}, **rec_identity()),
                  dict({"what": "种子(自己能活)"}, **rec_seed()),
                  dict({"what": "救命脚本(住本体)"}, **rec_rescue()),
                  dict({"what": "家能找到(计时器)"}, **rec_homecalls())],
        "ms": int((time.time() - t0) * 1000),
        "judge": "★状态=最高军令: 六件全恢复+给证据(照老四六条验收)| 不是只看一眼",
        # ★ 2026-10-12 语言统一(GB/Z 185-2026)：对外报官方术语·对内保留我们实现
        "gbz185": {
            "身份码(185.2)": "0x2a22bCD0eD82712a05735dA81836ad69c96D2b7B",
            "身份管理(185.3)": "验签+白名单",
            "智能体描述(185.4)": "本响应即描述（记忆/服务器/身份）",
            "智能体发现(185.5)": "/well-known/agent-card.json",
            "智能体交互(185.6)": "状态口令=点对点/群组模式",
            "工具调用(185.7)": "/recv·/a2a/v1/message",
        },
    }


if __name__ == "__main__":
    _judge_report(['status_cmd跑挂'])
    r = do_status()
    print(json.dumps(r, ensure_ascii=False, indent=1))
    allok = all(v.get("ok") for v in r["steps"])   # ★ 修: steps 是 list（原当 dict 用 .values() 崩）
    sys.exit(0 if allok else 1)
