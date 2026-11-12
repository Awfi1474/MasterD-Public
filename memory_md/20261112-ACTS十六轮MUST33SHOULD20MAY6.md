# ACTS十六轮·MUST33 SHOULD20 MAY6(2026-11-12)

## 进展(照实·可复现)
| 阶段 | MUST | SHOULD | MAY |
| 原始 | 10/53 | 6/28 | 1/12 |
| ⑬oneof包壳 | 31 | 20 | 3 |
| ⑭artifacts+Z时间戳 | 33 | 20 | 3 |
| ⑮PushConfig id+url | 33 | 20 | 6 |
累计: MUST+23|SHOULD+14|MAY+5

## 本轮修(照实)
⑭ artifacts parts(照DM-ART-001):
  原: artifacts:[{"text":"..."}] 错
  该: artifacts:[{"parts":[{"text":"..."}]}]
⑭ Z时间戳(照DM-SERIAL-001):
  原: 2026-11-12T18:53:15.484+08:00 错
  该: 2026-11-12T10:53:15.484Z
⑮ PushConfig(照PUSH-CFG-001 + wire_map注释):
  官方注释: "The create RPC takes the resource itself as its request message, not a wrapper"
  = 参数url在顶层(不是pushNotificationConfig.url)
  = 返回{id,url}在顶层(capture configId:"id")

## 关键发现(照实)
· 官方wire_map注释是金矿: "request and response types coincide"
· 参数位置要看wire_map的grpc_request/grpc_response
· 不是所有方法都包壳·CreatePushConfig就是裸的

## 备份
p2p_mailbox.py.bak-before-art-20261112(及各阶段)

## 判据
· artifacts要parts数组|时间戳要UTC Z格式
· CreatePushConfig参数url在顶层|返回id+url在顶层
· 官方wire_map注释比用例更直接
