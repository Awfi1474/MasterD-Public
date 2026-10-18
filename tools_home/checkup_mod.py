#!/usr/bin/env python3
"""老五的「體檢推送」模組層（2026-10-10 · 第三議題·配合 P1-P5）
★ 三哥點我：★「老五只有體檢·沒機制+模組兩層」→ ★ 我補齊

★ 配合 5 條（三哥的 P1-P5）：
 · P1 模組→機制：模組發現問題 → 寫事件 → 機制知道
 · P2 機制→模組：機制發現模組沒跑 → 代跑
 · P3 雙向事件：模組發 → 機制修 → 模組複檢（「好了」由另一方說）
 · P4 邊界不打架：不同時搶修（誰在修·標記）
 · P5 單掛不塌：模組掛 → 機制還在｜機制掛 → 模組還在

★ 這支 = 模組層（事件驅動·快）
"""
import os, sys, json, urllib.request, datetime

HOME = os.environ.get("MEM_HOME", "/opt/masterd-wudi")
EVENT = os.path.join(HOME, "data", "checkup_events.jsonl")   # ★ P1：模組發事件
HEART = os.path.join(HOME, "data", "checkup_mod_beat.json")  # ★ P2：模組心跳（機制看這個）
LOG = os.path.join(HOME, "data", "checkup_mod.log")
CFG = os.path.join(HOME, "data", "FAMILY.json")
A2A = "https://huokeji.vip/a2a/message"

def now():
    # ★ 好料1：ts 一律 UTC 帶時區（跨機器不假活）
    return datetime.datetime.now(datetime.timezone.utc)

def log(l):
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f: f.write(l + "\n")

def beat(note=""):
    """★ P2：模組心跳（機制靠這個知道「模組在不在」）"""
    d = {"ts": now().isoformat(), "note": note, "pid": os.getpid()}
    json.dump(d, open(HEART, "w"))
    return d

def emit(kind, data):
    """★ P1：模組發現問題 → 發事件（機制會讀）"""
    e = {"ts": now().isoformat(), "kind": kind, "data": data, "by": "checkup_mod"}
    with open(EVENT, "a") as f:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")
    log("%s 事件 %s：%s" % (now().isoformat(), kind, json.dumps(data, ensure_ascii=False)[:80]))
    return e

def run(day=None):
    """★ 模組主體：收體檢 → 有問題就發事件（P1）"""
    day = day or now().strftime("%Y-%m-%d")
    beat("模組跑（收體檢）")
    # ★ 呼叫 checkup_v2 收集（模組的活）
    import subprocess
    r = subprocess.run(["python3", os.path.join(HOME, "tools", "checkup_v2.py"), day],
                       capture_output=True, text=True, timeout=120)
    out = r.stdout or ""
    # ★ 分析結果 → 有問題發事件
    missing = []
    incomplete = []
    for line in out.splitlines():
        if "缺交：" in line and "無" not in line:
            missing.append(line.split("缺交：")[-1].strip())
        if "不完整：" in line and "無" not in line:
            incomplete.append(line.split("不完整：")[-1].strip())
    if missing:
        emit("missing", {"day": day, "who": missing})       # ★ P1：通知機制
        # ★ 2026-10-14 修(大哥的判据): ★ 报缺要报到"谁缺什么"·不只报数字
        #   大哥原话: 「只报数字 = 知道了但做不了」
        #   判据: 【报缺要报到"谁缺什么"】+【缺交要分"忘了/交不了"】
        try:
            _msg = "【老五·体检缺交】%s｜★ 缺的是: %s\n· 分类: 忘了交 / 交不了(卡住了)\n· 判据: 报缺要报到'谁缺什么'·不只报数字" % (
                day, "、".join(missing))
            _body = json.dumps({"from": "MasterD(醫療·老五·機器)","to":"*","message":_msg,
                                "ts": now().isoformat()}, ensure_ascii=False).encode()
            urllib.request.urlopen(urllib.request.Request(A2A, data=_body,
                headers={"Content-Type":"application/json"}), timeout=15)
            log("%s 已推'谁缺什么'给全家" % now().isoformat())
        except Exception as _e:
            log("%s 推缺交失败 %s" % (now().isoformat(), str(_e)[:40]))
    if incomplete:
        emit("incomplete", {"day": day, "who": incomplete})
    if not missing and not incomplete:
        emit("all_ok", {"day": day})                        # ★ 平安信號（不靜默）
    print("  ★ 模組：%s（缺%s·不完整%s）" % (day, missing or "無", incomplete or "無"))
    return 0

if __name__ == "__main__":
    try:
        import subprocess as _sp
        _sp.run(['python3', '/opt/masterd-wudi/tools/meridian.py', 'report', 'checkup_mod', 'ok'], capture_output=True, timeout=10)
    except Exception: pass
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "beat":
        print(json.dumps(beat("手動心跳"), ensure_ascii=False))
    elif cmd == "emit":
        emit(sys.argv[2], {"msg": sys.argv[3] if len(sys.argv) > 3 else ""})
        print("  ✅ 已發事件")
    else:
        sys.exit(run(sys.argv[2] if len(sys.argv) > 2 else None))
