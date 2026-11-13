#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·验证标准器 verify_standard.py（照 2026-11-12 全族定的标准）
依据：官方 A2A v1.0.0 spec
  §3.1  11 方法清单
  §3.3.2 Validation Errors（MUST validate inputs）
  §3.3.4 Capability Validation（声明false→MUST报错）
  §5.3  Method Mapping（JSON-RPC=驼峰 SendMessage｜REST=斜杠 /message:send）
  §5.4  错误码
★ 核心判据（老五 11-12 提）：
   只有 -32601 和 404 是「没有」｜其余 -32xxx 都是「有但拒绝」
判据：验证要用验证标准｜不听说只看码
"""
import json, urllib.request, urllib.error, sys

# 官方 §5.4 错误码判定表（照实）
VERDICT = {
    "result":   ("✅", "方法在·返回结果"),
    "-32601":   ("❌", "方法不存在（Method not found）"),
    "404":      ("❌", "口不存在"),
    "-32001":   ("✅", "有·TaskNotFound"),
    "-32002":   ("✅", "有·TaskNotCancelable"),
    "-32003":   ("✅", "有·诚实拒绝（PushNotificationNotSupported）"),
    "-32004":   ("✅", "有·诚实拒绝（UnsupportedOperation）"),
    "-32005":   ("✅", "有·诚实拒绝（ContentTypeNotSupported）"),
    "-32006":   ("✅", "有·诚实拒绝（InvalidAgentResponse）"),
    "-32007":   ("✅", "有·诚实拒绝（ExtendedAgentCardNotConfigured）"),
    "-32008":   ("✅", "有·诚实拒绝（ExtensionSupportRequired）"),
    "-32009":   ("✅", "有·诚实拒绝（VersionNotSupported）"),
    "-32602":   ("✅", "有·参数校验（InvalidParams）"),
    "-32603":   ("✅", "有·内部错（InternalError）"),
}
# 官方 §3.1 的 11 方法（JSON-RPC 驼峰·照 §5.3）
METHODS = ["SendMessage","SendStreamingMessage","GetTask","ListTasks",
           "CancelTask","GetTaskPushNotificationConfig","SetTaskPushNotificationConfig",
           "ListTaskPushNotificationConfig","DeleteTaskPushNotificationConfig",
           "GetAgentCard","ResubscribeTask"]

def probe(endpoint, method):
    """打一家的一方法 → 判有没有（照标准）"""
    body = {"jsonrpc":"2.0","id":1,"method":method,"params":{}}
    req = urllib.request.Request(endpoint+"", data=json.dumps(body).encode(),
          headers={"Content-Type":"application/json","A2A-Version":"1.0.0"}, method="POST")
    try:
        raw = urllib.request.urlopen(req, timeout=8).read().decode("utf-8","ignore")
        d = json.loads(raw)
        if "result" in d: code="result"
        elif "error" in d: code=str(d["error"].get("code"))
        else: code="?"
        mark, why = VERDICT.get(code, ("⚠️", "未知码 "+code))
        return mark, code, why
    except urllib.error.HTTPError as e:
        code = str(e.code)
        mark, why = VERDICT.get(code, ("⚠️","HTTP "+code))
        return mark, code, why
    except Exception as e:
        return "❌", "ERR", str(e)[:40]

if __name__ == "__main__":
    ep = sys.argv[1] if len(sys.argv)>1 else "https://huokeji.vip/a2a-jsonrpc"
    print("★ 验证标准器（照 11-12 定的标准）｜口:", ep)
    print("★ 判据：只有 -32601/404 = 没有｜其余错误码 = 有但拒绝")
    print("="*60)
    ok=0
    for m in METHODS:
        mark, code, why = probe(ep, m)
        if mark=="✅": ok+=1
        print("  %-32s %s %-8s %s" % (m, mark, code, why))
    print("="*60)
    print("★ 判: %d/%d 方法在" % (ok, len(METHODS)))
