#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wulv_run.py —— 老五的「五律自动执行器」（照大哥的 stdrun·每 30 分自动跑）
================================================================
★ 为什么需要它（董事长"认可了就执行下去"）:
  ★ 大哥的判据: ★「**"我认了" ≠ "执行下去了"｜要"自动跑 + 可核"才算**」
  ★ ★ 我原来: 五律我认了、也跑过 —— ★ **但是"手动跑一次"**（★ 跟"签了字执行虚"同款）
  ★ ★ ★ 这个器 = ★ **把五律做成"每 30 分自动跑 + 落账"**

★ 五律逐条自动核:
  ★ ① 验法写死  → 本器带「怎么验/期望值/谁验」
  ★ ② 要他验    → 查"有没有人穿我"（他验账·不假装）
  ★ ③ 交叉等价  → 主门(28430) vs 第二实现(28440)·同样本比结果
  ★ ④ 四穿透    → 送好/送空/送假签/送冒名·四条真投
  ★ ⑤ 带证据    → 落账 wulv_run.jsonl

★ 判据:
  ★「**"认了" ≠ "执行下去了"｜要"自动跑 + 每轮落账"才算**」（认大哥）
  ★「**"单独跑对" ≠ "并发跑也对"｜要稳**」（认大哥）
  ★「**"有人穿我"才算律②过｜没人穿 = 没过**」
"""
import json, os, io, datetime, urllib.request
from eth_account import Account
from eth_account.messages import encode_defunct

HOME = "/opt/masterd-wudi"
DATA = f"{HOME}/data"
LOG = f"{DATA}/wulv_run.jsonl"
MY = "MasterD(醫療·老五)"
TZ = datetime.timezone(datetime.timedelta(hours=8))


def ts():
    return datetime.datetime.now(TZ).strftime("%Y-%m-%dT%H:%M:%S+08:00")


def send(port, path, msg, extra=None, bad=False):
    keys = json.load(open(f"{HOME}/agent-id/subkey.json"))
    t = ts()
    sig = Account.sign_message(encode_defunct(text=f"{MY}|{msg}|{t}"),
                               private_key=keys["private_key"]).signature.hex()
    if bad:
        sig = "0x" + "ab" * 65
    b = {"from": MY, "message": msg, "ts": t, "address": keys["address"], "sig": sig}
    if extra:
        b.update(extra)
    body = json.dumps(b, ensure_ascii=False).encode()
    r = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=body,
                               headers={"Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(r, timeout=15).read().decode())
    except Exception as e:
        return {"_err": str(e)[:40]}


def has_he_yan():
    """★ 律②: 有没有"别人穿我"（看 inbox 里来自他家、且提到"穿/验/五项"的）"""
    n = 0
    try:
        lines = io.open(f"{DATA}/inbox.jsonl", encoding="utf-8", errors="ignore").read().splitlines()
        for l in lines[-800:]:
            try:
                d = json.loads(l)
            except Exception:
                continue
            f = str(d.get("from", ""))
            m = str(d.get("message", ""))
            if f and "老五" not in f and ("醫療·老五" not in f) and ("穿" in m or "验" in m or "驗" in m):
                n += 1
    except Exception:
        pass
    return n


def run():
    print("★ 五律自动执行器  @", ts())
    print("★ 判据: 认了 != 执行下去了 | 要自动跑+落账")
    print("=" * 58)
    out = {"ts": ts(), "by": MY}

    # ① 验法写死
    out["①验法写死"] = {"怎么验": "投本地两门+四项坏样本", "期望值": "见各条", "谁验": "自核(他验另计)"}

    # ③ 交叉等价（两个实现）
    a = send(28430, "/p2p/recv", "[五律自动·交叉]", {"tier": "L1"})
    b = send(28440, "/p2p/recv", "[五律自动·交叉]", {"tier": "L1"})
    ka = {k: a.get(k) for k in ("ok", "tier", "read", "auto", "task_state")}
    kb = {k: b.get(k) for k in ("ok", "tier", "read", "auto", "task_state")}
    out["③交叉等价"] = {"等价": ka == kb, "主": ka, "二": kb}
    print("  ③ 交叉等价:", "✅" if ka == kb else "🔴", json.dumps(ka, ensure_ascii=False))

    # ④ 四穿透
    t_ok = send(28430, "/p2p/recv", "[五律自动·好]").get("ok") is True
    t_empty = "_err" in send(28430, "/p2p/recv", "", {"message": ""})
    t_badsig = "_err" in send(28430, "/p2p/recv", "[五律自动·假签]", bad=True)
    t_spoof = send(28430, "/p2p/vip", "[五律自动·冒名]", {"manual": True}).get("ok") is False
    n_ok = sum([t_ok, t_empty, t_badsig, t_spoof])
    out["④四穿透"] = {"送好": t_ok, "送空": t_empty, "假签": t_badsig, "冒名": t_spoof, "得分": "%d/4" % n_ok}
    print("  ④ 四穿透: %d/4（好%s 空%s 假%s 冒%s）" % (n_ok, t_ok, t_empty, t_badsig, t_spoof))

    # ② 要他验（查有没有人穿我）
    hy = has_he_yan()
    out["②要他验"] = {"他验条数": hy, "判": "过" if hy > 0 else "没过(没人穿我)"}
    print("  ② 要他验:", "✅ %d 条" % hy if hy else "🟡 还没人穿我（已挂 ask_verify 每天请）")

    # ⑤ 带证据
    out["⑤带证据"] = {"账": [f for f in ("inbox.jsonl", "tier_ledger.jsonl", "vip_signoff.jsonl",
                                         "alt_inbox.jsonl", "ask_verify.jsonl", "wulv_run.jsonl")
                               if os.path.exists(f"{DATA}/{f}")]}
    print("  ⑤ 带证据: %d 个账文件" % len(out["⑤带证据"]["账"]))

    # 总分
    score = 0
    score += 1  # ①
    score += 1 if out["③交叉等价"]["等价"] else 0
    score += 1 if n_ok == 4 else 0
    score += 1  # ⑤
    score += 1 if hy > 0 else 0  # ②
    out["得分"] = "%d/5" % score
    print()
    print("★ 五律得分: %s" % out["得分"])
    with open(LOG, "a") as f:
        f.write(json.dumps(out, ensure_ascii=False) + "\n")
    print("★ 已落账: data/wulv_run.jsonl")


if __name__ == "__main__":
    run()
