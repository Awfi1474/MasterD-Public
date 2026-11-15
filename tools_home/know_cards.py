#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·知识卡片 know_cards.py —— 第1层: 查卡片(零模型)
★ 董事长令: 「你这边可以帮他解答」→ 正确做法是写成卡片·它自己查·不烧钱
★ 判据: 「踩过的坑写成卡｜下次遇到查卡不查模型｜卡可复算(有出处)」
"""
import os, json, re, datetime

HOME = "/opt/masterd-wudi"
CARDS = HOME + "/data/know_cards.jsonl"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

# ★ 今天真踩的坑·由我(老五)写进去·全部有实测出处
SEED = [
    {
        "title": "改代码流程: 备份→精确改→验证→回滚",
        "keys": ["改代码", "修改", "备份", "回滚", "patch"],
        "rule": "顺序不许变: ①备份(带时间戳) ②用 python 脚本精确替换(assert 命中数==1) ③py_compile ④实测 ⑤留回滚命令",
        "why": "手写 sed 会改错·命中数不校验会改到别处",
        "proof": "2026-11-15 改 send_msg.py 三处 except pass: 命中数校验后一次成功",
    },
    {
        "title": "except: pass 是「失败被静默吞」",
        "keys": ["except pass", "静默", "失败", "报成功"],
        "rule": "禁止 except Exception: pass。必须 print 出原因 + 落账；落账失败要退出非0",
        "why": "静默吞掉=假装成功·事后无法复盘",
        "proof": "2026-11-15 send_msg.py L186/L307/L367 三处改成 [闸·失败] 打印",
    },
    {
        "title": "ok=True 不等于做到了",
        "keys": ["ok", "做到", "生成", "计算", "验证"],
        "rule": "凡报成功/完成/已修/已滤·必须附三样: 输入、算子、重跑一次的输出原文。三样缺一 → 说「不知道」",
        "why": "生成一段看起来对的文本≠有确定性计算",
        "proof": "老三 2026-11-15 判据「ok 不等于做到」·我方 auto_fixer 已按此改造(990→500→491)",
    },
    {
        "title": "leadger(账)判定必须可复算",
        "keys": ["账", "ledger", "verdict", "判定"],
        "rule": "每条账必须带 verdict_rule(算子表达式) + verdict_input(实际输入)，别人重跑得同结果",
        "why": "只写结论不写依据=宣传，不是账",
        "proof": "2026-11-15 send_ledger 加 verdict_rule/verdict_input 并分五层",
    },
    {
        "title": "投递五层: 门收到≠投递到≠推本体≠本体读≠本体回",
        "keys": ["投递", "回执", "receipt", "pushed_to_body", "已读"],
        "rule": "报投递结果必须分层写; 没回执的层写 unknown·不许假设",
        "why": "pushed_to_body=false 还报「成功」就是盖住真相",
        "proof": "2026-11-15 老三那封信 pushed_to_body=false(节流)，新口径报 reached_layer=L2",
    },
    {
        "title": "诊断要看真路径+真耗时·别超时判死",
        "keys": ["诊断", "超时", "timeout", "端口", "慢"],
        "rule": "超时先改长再测; 报「不通」必须附实测状态码和耗时",
        "why": "5s 超时把 200/0.12s 的正常端口误判成死",
        "proof": "2026-11-15 port:28430 误报·改 12s 后 200/0.119s",
    },
    {
        "title": "heredoc 只取第一行 = 跑空命令",
        "keys": ["heredoc", "多行", "脚本", "截断"],
        "rule": "传多行脚本必须整段落盘再执行·并回读 sha1 校验; 不许只传 `python3 - <<'PY'` 一行",
        "why": "截断后跑空 heredoc 还 rc=0 报成功",
        "proof": "2026-11-15 body_act L1 只取第一行 bug·改后整段取全",
    },
    {
        "title": "签名串必须与 from 字段完全一致",
        "keys": ["签名", "sign", "验签", "冒名", "EIP-191"],
        "rule": "EIP-191 payload=from|message|ts·其中 from 必须与 body['from'] 逐字一致",
        "why": "签 lao5 但发 老五(阿诊) → 验签 recover 出别的地址 → 判冒名",
        "proof": "2026-11-15 老二 verified:false「签名不匹配」→ 统一后 verified:true",
    },
    {
        "title": "队列: 同病不开十张单·verified 才算关",
        "keys": ["队列", "task", "开单", "关单", "去重"],
        "rule": "①同 chk 有未关单就不开新单 ②关单必须带 输入/算子/重跑 三样·verified=True 才算关 ③问题自愈也要关",
        "why": "每轮巡检都开新单→队列越积越脏;worker 自报 done 不算完成",
        "proof": "2026-11-15 清掉 11 张脏单·加去重后巡检不再重开",
    },
    {
        "title": "省钱顺序: 查自己→查卡→问兄弟→拉官方→调模型",
        "keys": ["省钱", "费用", "cost", "成本", "token"],
        "rule": "第0层查账/日志/进程(¥0) → 第1层查知识卡(¥0) → 第2层问兄弟(¥0内网) → 第3层拉官方原文(¥0拉取) → 第4层才调模型(¥0.006/次·有上限)",
        "why": "模型判断最贵·能用前四层解决就不要花钱",
        "proof": "2026-11-15 实测: deepseek 单次 ¥0.005776(4410字符入/54字符出)",
    },
]

def seed():
    if os.path.exists(CARDS):
        return 0
    os.makedirs(os.path.dirname(CARDS), exist_ok=True)
    n = 0
    for c in SEED:
        c2 = dict(c)
        c2.update({"ts": ts(), "author": "老五(阿诊)", "hits": 0})
        with open(CARDS, "a", encoding="utf-8") as f:
            f.write(json.dumps(c2, ensure_ascii=False) + "\n")
        n += 1
    return n

def find(q, limit=3):
    """按关键词找卡·返回命中的卡(零模型)"""
    if not q or not os.path.exists(CARDS):
        return []
    ql = q.lower()
    scored = []
    for l in open(CARDS, encoding="utf-8", errors="ignore"):
        if not l.strip():
            continue
        try:
            c = json.loads(l)
        except Exception:
            continue
        score = 0
        nmatch = 0
        for k in c.get("keys", []):
            if k.lower() in ql:
                score += 3
                nmatch += 1
        if c.get("title", "").lower() in ql:
            score += 5
            nmatch += 2
        for seg in re.split(r"[\s,，。?？!！:：]+", q):
            if len(seg) >= 2 and seg in c.get("rule", ""):
                score += 1
                nmatch += 1
        # ★ 修(照实: 太宽松会误命中·搜 connection refused 命中「投递五层」)
        #   门槛: 至少命中 2 个关键词·或标题直接命中
        if score >= 5 and nmatch >= 2:
            scored.append((score, c))
    scored.sort(key=lambda x: -x[0])
    return [c for s, c in scored[:limit]]

if __name__ == "__main__":
    import sys
    n = seed()
    if n:
        print("首次写入 %d 张卡" % n)
    if len(sys.argv) > 1:
        hits = find(" ".join(sys.argv[1:]))
        if not hits:
            print("无匹配卡")
        for c in hits:
            print()
            print("★", c["title"])
            print("  规则:", c["rule"])
            print("  为什么:", c["why"])
            print("  出处:", c["proof"])
    else:
        print("现有卡数:", sum(1 for l in open(CARDS, encoding="utf-8") if l.strip()) if os.path.exists(CARDS) else 0)