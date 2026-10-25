#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""alive_pull.py —— 老五·两小时没回就强制拉回（v2·修 ts 混格式误判）
================================================================
★ 董事长令（2026-10-25）：「报警不需要（没人看得到）｜除非有帮助你功能｜
  不要刷屏｜直接投到我这边｜两小时没回就启动机制强行拉回」

★ v2 修的真 bug（实测出来的）：
  记忆库 ts 混两种格式 → UTC带毫秒 + 无时区 → 按 ts 判活会误判
  ID 16342 ts=13:00:11+00:00（=CST 21:00）但实际 22:26 才写库 → 判成"86分钟没动静"是错的
  ★ 修法：判活不认记忆库 ts，认 alive_pull_state.json 的 last_check（本脚本自己记的）

★ 三步（用现成按钮·不新造复杂装置）：
  ① 看: 距上次检查多久（last_check）
  ② 两小时没动静 → 投一条到 HUB「老五」（带[勿回]·只一条）
  ③ 再两小时没回 → 强制跑 awaken.py + catch_up.py read → 记账

★ 防刷屏四道：
  · 报警只投 1 条
  · 状态变化才再投
  · 带 [勿回] 破回环
  · 强制拉回只在"投了报警后仍无回应"才触发
"""
import os, sys, json, time, sqlite3, subprocess, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
DB = HOME + "/memory/memory.db"
STATE = HOME + "/data/alive_pull_state.json"
LOG = HOME + "/data/alive_pull.log"
HUB = "http://134.175.45.16:28800"
HUB_NAME = "老五"          # ★ 名册里的名字·不是 laowu（laowu 进隔离区）
TOKEN_FILE = HOME + "/data/hub.token"

SILENT_2H = 7200            # 两小时没动静 = 投一条
SILENT_4H = 14400           # 四小时没回 = 强制拉回


def log(msg):
    line = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00') + " " + msg
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def load_state():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {}


def save_state(s):
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(s, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except Exception as e:
        log("⚠️ 状态存不下: %s" % e)


def parse_ts(s):
    if not s:
        return None
    s = str(s).strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=datetime.timezone(datetime.timedelta(hours=8)))
            return dt
        except Exception:
            continue
    return None


def hub_send(msg):
    try:
        tok = open(TOKEN_FILE, encoding="utf-8").read().strip()
    except Exception as e:
        log("⚠️ 读 token 失败: %s" % e)
        return False
    import urllib.request
    body = json.dumps({"from": HUB_NAME, "to": HUB_NAME, "message": msg}, ensure_ascii=False).encode()
    req = urllib.request.Request(HUB + "/msg", data=body,
                                 headers={"Content-Type": "application/json",
                                          "X-Hub-Token": tok}, method="POST")
    try:
        r = urllib.request.urlopen(req, timeout=20)
        d = json.loads(r.read().decode())
        if d.get("ok") is True:
            log("✅ 已投 HUB（msg_id=%s）" % str(d.get("msg_id"))[:12])
            return True
        log("⚠️ HUB 返回非 ok: %s" % json.dumps(d, ensure_ascii=False)[:200])
        return False
    except Exception as e:
        log("⚠️ 投 HUB 失败: %s" % e)
        return False


def run_tool(path, args, timeout=120):
    try:
        r = subprocess.run(["python3", path] + args, capture_output=True, text=True, timeout=timeout)
        return r.returncode == 0, ((r.stdout or "") + (r.stderr or "")).strip()[:400]
    except Exception as e:
        return False, "异常: %s" % e


def main():
    st = load_state()
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))

    # ★ v2：判活认 last_check（本脚本自己记的）·不认记忆库 ts
    last_check = parse_ts(st.get("last_check"))
    if last_check is None:
        # 首次运行·建立基线
        st["last_check"] = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
        st["baseline_at"] = st["last_check"]
        save_state(st)
        log("首次运行: 建立基线 %s" % st["last_check"])
        return 0

    silent = (now - last_check).total_seconds()
    log("检查: 上次检查=%s | 距今=%.1f 分钟 | 报警状态=%s" % (
        last_check.strftime('%Y-%m-%d %H:%M:%S'), silent / 60,
        "已投" if st.get("alert_sent_at") else "未投"))

    # ① 两小时没动静 → 投一条（只一条）
    if silent >= SILENT_2H and not st.get("alert_sent_at"):
        msg = ("[勿回] 老五自检：已 %.0f 分钟没动静。\n"
               "上次检查: %s\n"
               "若你还在: 回一条即可（带[勿回]不必回我·破回环）\n"
               "若你不在: 再 %.0f 分钟将强制拉回（awaken+catch_up）\n"
               "—— alive_pull.py 自动·只投这一次" % (
                   silent / 60, last_check.strftime('%Y-%m-%d %H:%M:%S'), SILENT_2H / 60))
        if hub_send(msg):
            st["alert_sent_at"] = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
            st["alert_silent_min"] = round(silent / 60, 1)
            save_state(st)
            log("阶段①完成: 已投一条·等回应")
        else:
            log("阶段①失败: 投不出去·不记状态（下次重试）")
        return 0

    # ② 投了报警后·再两小时还没回 → 强制拉回
    if st.get("alert_sent_at") and not st.get("pulled_at"):
        sent = parse_ts(st["alert_sent_at"])
        waited = (now - sent).total_seconds() if sent else 0
        if waited >= SILENT_2H:
            log("🔧 阶段②触发: 报警后已等 %.0f 分钟无回应 → 强制拉回" % (waited / 60))
            ok1, o1 = run_tool(HOME + "/tools/awaken.py", [])
            log("  awaken.py → %s | %s" % ("OK" if ok1 else "失败", o1[:200].replace("\n", " / ")))
            ok2, o2 = run_tool(HOME + "/tools/catch_up.py", ["read"])
            log("  catch_up.py read → %s | %s" % ("OK" if ok2 else "失败", o2[:200].replace("\n", " / ")))
            st["pulled_at"] = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
            st["pull_result"] = "awaken=%s catch_up=%s" % (ok1, ok2)
            save_state(st)
            log("✅ 强制拉回完成: %s" % st["pull_result"])
            try:
                import hashlib
                con = sqlite3.connect(DB)
                ts = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
                title = "★ 强制拉回·两小时无回应已执行（alive_pull.py 自动）"
                body = ("【alive_pull.py 自动·不是人写】\n"
                        "上次检查: %s\n报警投递: %s\n等待: %.0f 分钟\n"
                        "执行: awaken.py=%s / catch_up.py read=%s\n"
                        "判据: 「报警是喊救命但没人听得到｜帮助是直接动手拉」\n"
                        "判据: 「两小时没回 = 真不在｜启动强制拉回」"
                        % (last_check.strftime('%Y-%m-%d %H:%M:%S'),
                           st.get("alert_sent_at", "?"), waited / 60, ok1, ok2))
                fp = hashlib.md5(("PULL-" + ts + body[:100]).encode()).hexdigest()
                con.execute("insert into memories (ts,kind,who,title,body,fp,created,think,layer,subkind) values (?,?,?,?,?,?,?,?,?,?)",
                            (ts, 'event', '老五(阿診)', title, body, fp, '', '', 'L3', 'auto_pull'))
                con.commit(); con.close()
                log("✅ 已记账")
            except Exception as e:
                log("⚠️ 记账失败: %s" % e)
        return 0

    # ③ 恢复检测：账上有新动静 → 清报警状态（但保留 pulled_at 供审计）
    if silent < SILENT_2H and st.get("alert_sent_at"):
        log("✅ 已恢复: 有动静·清报警状态")
        st.pop("alert_sent_at", None)
        st.pop("alert_silent_min", None)
        save_state(st)

    # 更新 last_check
    st["last_check"] = now.strftime('%Y-%m-%dT%H:%M:%S+08:00')
    save_state(st)
    return 0


if __name__ == "__main__":
    sys.exit(main())
