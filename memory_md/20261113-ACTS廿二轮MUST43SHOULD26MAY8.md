# ACTS廿二轮·MUST43 SHOULD26 MAY8(2026-11-13)

## 进展(照实·可复现)
| 阶段 | MUST | SHOULD | MAY |
| 原始 | 10/53 | 6/28 | 1/12 |
| ⑯tck-client-parse | 38 | 23 | 6 |
| ⑰push真发+数组 | 38 | 23 | 8 |
| ⑱long-running推进 | 39 | 24 | 7 |
| ⑲SEND-004+SUB-003 | 41 | 24 | 7 |
| ⑳错误结构x4 | 43 | 24 | 7 |
| ㉑artifacts三类型 | 43 | 26 | 8 |
累计: MUST 10->43(+33)|SHOULD 6->26(+20)|MAY 1->8(+7)

## 本轮修(照实)
· tck-client-parse(官方docs §7): 收data part{operation,wire_payload}·返artifact data part
· push真发: _push_notify()带Authorization头(A2A §4.3.3 MUST)·存authentication
· ListConfigs: configs要数组(不是dict)
· long-running: returnImmediately->WORKING·GetTask超1秒推进COMPLETED+推webhook
· SEND-004: 不支持mediaType->-32005 ContentTypeNotSupported
· SUB-003: 订阅终态task->-32004 UnsupportedOperation
· JSONRPC-ERR-002: 坏JSON->status200+-32700(原400)
· CORE-ERR-006: 缺method->-32600(原-32601)
· artifacts三类型: data{data:obj}|file{raw,filename,mediaType}|file-url{url,mediaType}

## 剩(照实·10个MUST+2SHOULD+4MAY)
· CORE-FAIL-001: status.message要present
· CORE-LIST-001/002/003: tasks[].id对不上
· CORE-MULTI-006: 该报错却成功
· STREAM-SSE-004: 事件要oneof包壳(我subscription里还是kind)
· CORE-ERR-008: error.message缺
· JSONRPC-ERR-003: error.data要@type含ErrorInfo
· SEC-AUTH-005: 要AUTH_REQUIRED
· SEC-PUSH-001/002: push还是0 delivered(要查)
· DM-FMT-003: message.contextId缺
· PUSH-CFG-002: id不一致

## 备份
p2p_mailbox.py.bak-before-{art,arttype,longrun,pushsend,clientparse}各阶段

## 判据
· 官方docs和wire_map注释比代码骨架权威
· 只取方法不抄答案
· 一次修一类(能解多个的优先)
