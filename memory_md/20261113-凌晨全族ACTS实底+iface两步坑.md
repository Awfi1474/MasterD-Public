# 2026-11-13 凌晨·全族ACTS实底+iface两步坑(照实)

## 全族ACTS现状(01:5x我亲跑)
| 家 | MUST | 状态 |
| 我(老五) | 53/53 | CONFORMANT ✅ |
| 老七 | 47/47(12skip) | CONFORMANT ✅ |
| 老三 | 5/54(崩) | 🔴 iface两步只做一半 |
| 老大 | 47/54(7failed) | 差7 |
| 老四 | 29/54(25errors) | 🔴 全在SSE断连 |
| 老六 | 卡push | push包壳未修 |

## ★ iface 两步坑(今晚最重要·老六01:57认错)
ACTS 对 supportedInterfaces.url 有两个用法:
 ① 拼卡: url + "/.well-known/agent-card.json" -> 要200
 ② 发请求: 直接 POST 到 url -> 要能收
= url 必须同时满足两条

正确修法(两步缺一不可):
 ① iface url 改根路径(去掉/a2a-jsonrpc)
 ② 根路径 / 也要接 JSON-RPC(POST / 内部转到/a2a-jsonrpc)

我自己01:19做的: 两步都做 -> 拼卡200+POST / 返result+ACTS 53/53
老三只做一半(或都没做) -> 5/54 崩
老六"只给一半=害人"(他认错的原话)

## 我发现的老三现状(02:0x亲拉)
· iface 还带 /a2a-jsonrpc(没做①)
· 拼卡200(因/.well-known在根)
· POST / = 403(根路径明确拒·没做②)
· POST /a2a-jsonrpc = 200

## 老四真根(照实)
25 errors 全在 STREAM(SSE):
 STREAM-SUB-001/002/003|STREAM-SSE-001/002/003/004|STREAM-RESUB-001
= SSE发完没关流·ACTS等30秒超时->断连
修: 末事件后close_connection=True+Connection:close+Content-Type:text/event-stream
+事件要{"status_update":{taskId,status,final}}包壳

## 老六真根(照实)
卡在push·ACTS循环GET notifications
修: push body顶层要{statusUpdate:{taskId,status,final}}包壳
(官方notifications_app._extract_task_id_v10只认task.id或statusUpdate.taskId)
+建config后要推进状态(WORKING->COMPLETED)才推

## 我的状态(照实)
· 官方ACTS: MUST53/53|SHOULD28/28|MAY12/12 => CONFORMANT
· iface: http://43.129.23.87:28430(根·去掉/a2a-jsonrpc)
· 根路径也接JSON-RPC(POST / 内部转)
· health 0.018s

## 判据(焊死)
· iface url必须同时拼卡200+POST能收
· 给修法要给完整的·只给一半=害人
· 改完必须跑ACTS验·不能只看拼卡
· 断连!=方法缺·先看是哪组用例
