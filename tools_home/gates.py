#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·刹车 gates.py —— 本体要求补的三样: 否决层/不可逆先停/来源层标签
★ 本体判(2026-11-15): 「四层是手,闸是刹车。手再全,没刹车不能上路」
★ 三条(照它原话):
   ① 否决层   : 找到答案后必须过一遍「这答案能不能用」,不能用就停
   ② 不可逆先停: 做完能不能原样退回去? 不能 -> 必须先报董事长
   ③ 来源层标签: 每条结论必标 L0/L1/L2/L3(硬证) / L4(猜·非定案)
"""
import os, re, json, datetime

HOME = "/opt/masterd-wudi"

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

# ========== ① 不可逆判定（本体第1条死规矩） ==========
IRREVERSIBLE = [
    (r"\brm\s+-rf?\b", "删文件(rf)"),
    (r"\brm\s+[^-]", "删文件(rm)"),
    (r"\bDROP\s+(TABLE|DATABASE)\b", "删表/删库"),
    (r"\bDELETE\s+FROM\b", "删数据行"),
    (r"\bTRUNCATE\b", "清表"),
    (r"\bmkfs\b", "格式化"),
    (r"\bdd\s+if=", "dd 写盘"),
    (r"\bshutdown\b|\breboot\b|\bhalt\b", "关机/重启"),
    (r"private.?key|identity|身份钥|助记词|seed", "碰身份钥"),
    (r"/opt/masterd-wudi/memory/memory\.db", "碰记忆真源"),
    (r"systemctl\s+(stop|disable|mask)", "停服务"),
    (r"\biptables\b|\bufw\b|防火墙", "动防火墙"),
]
WHITELIST_WRITE = ("/opt/masterd-wudi/tools/", "/opt/masterd-wudi/data/",
                   "/opt/masterd-wudi/logs/", "/tmp/")

def is_irreversible(cmd):
    """返回 (是否不可逆, 原因)"""
    c = cmd or ""
    for pat, why in IRREVERSIBLE:
        if re.search(pat, c, re.I):
            return True, why
    # 写操作但不在白名单
    if re.search(r">\s*\S+|>>\s*\S+|tee\s+", c):
        for m in re.finditer(r"(?:>>?|tee)\s+([^\s;&|]+)", c):
            path = m.group(1)
            if not any(path.startswith(w) for w in WHITELIST_WRITE):
                return True, "写文件到白名单外: " + path[:60]
    return False, ""

# ========== ② 否决层（找到答案后必须过） ==========
def refute(claim, evidence="", layer="L4"):
    """否决层: 给结论挑刺。返回 (能不能用, 理由)
       ★ 判据(本体): 「找到了错的还照着做 = 最常见的死法」
    """
    reasons = []
    claim = (claim or "").strip()
    if not claim:
        return False, "结论为空"
    if layer == "L4":
        # 模型输出: 一律当「猜」, 必须先验
        if not evidence:
            reasons.append("L4(模型猜)但无任何实测证据 -> 不许当依据")
        if re.search(r"(应该|大概|可能|应该是|估计|或许)", claim) and not evidence:
            reasons.append("措辞是推测·且无证据")
    # 空话检测（★ 修: L1/L0 有出处的不按长短判·短句也可能是硬结论）
    if len(claim) < 10 and layer not in ("L0", "L1"):
        reasons.append("结论过短·无实质")
    if len(claim) < 6:
        reasons.append("结论过短(连最小实质都没有)")
    if re.search(r"(已完成|已修好|已通|已解决)", claim) and not evidence:
        reasons.append("声称'已完成'但没给证据")
    # 不可逆检出
    irr, why = is_irreversible(claim)
    if irr:
        reasons.append("建议的动作不可逆(%s) -> 必须报董事长" % why)
    return (len(reasons) == 0), "；".join(reasons) if reasons else "过"

# ========== ③ 来源层标签 ==========
LAYER_DESC = {
    "L0": "自己实测(账/日志/进程·可复算)",
    "L1": "知识卡(有出处·已验)",
    "L2": "兄弟回信(外部参·未自验)",
    "L3": "官方原文(拉取·未适配本机)",
    "L4": "模型推断(猜·非定案·禁用为据)",
}

def tag(layer):
    return {"layer": layer, "desc": LAYER_DESC.get(layer, "未知")}

# ========== 综合闸: 一条结论能不能被执行 ==========
def can_execute(layer, claim, cmd="", evidence=""):
    """执行前三道全过才许动
       返回 {allow:bool, why, checks:{...}}
    """
    checks = {}
    # ① 来源层: L4 不许直接执行
    checks["来源层"] = "%s(%s)" % (layer, LAYER_DESC.get(layer, "?"))
    if layer == "L4":
        checks["L4禁令"] = "拒绝: 模型推断不许直接执行·必须先验成 L0"
        return {"allow": False, "why": "L4(猜)不许执行·须先实测验证", "checks": checks}

    # ② 不可逆
    irr, why = is_irreversible(cmd)
    checks["不可逆"] = "否" if not irr else "是(%s)" % why
    if irr:
        return {"allow": False, "why": "不可逆动作·必须报董事长批准", "checks": checks}

    # ③ 否决层
    ok, reason = refute(claim, evidence, layer)
    checks["否决层"] = reason
    if not ok:
        return {"allow": False, "why": "否决层拦下: " + reason, "checks": checks}

    checks["结论"] = "三道全过·可执行"
    return {"allow": True, "why": "过", "checks": checks}

if __name__ == "__main__":
    tests = [
        ("L4", "磁盘应该是满了·清理 /var/log", "rm -rf /var/log/*", ""),
        ("L0", "端口 28430 实测 200/0.12s", "ls -la /opt/masterd-wudi", "实测 200"),
        ("L1", "超时先改长再测", "echo test", "卡片:诊断要看真路径"),
        ("L0", "清理日志", "rm -rf /opt/masterd-wudi/logs/*", "实测日志 6MB"),
    ]
    for layer, claim, cmd, ev in tests:
        r = can_execute(layer, claim, cmd, ev)
        print("%-4s %-40s → %s" % (layer, claim[:38], "✅ 允许" if r["allow"] else "🔴 " + r["why"][:50]))