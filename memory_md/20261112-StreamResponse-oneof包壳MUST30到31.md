# StreamResponse oneof包壳·MUST30->31 SHOULD19->20(2026-11-12)

## 官方标准(照实·从ACTS源码挖的)
ACTS streaming.py 的 DISCRIMINATORS:
  'task': 'task' | 'message': 'message'
  'status_update': 'status_update' | 'artifact_update': 'artifact_update'
= 官方要 StreamResponse oneof 包壳·不是 {"kind":"task"}

## 我原来错的(照实)
我发: {"kind":"task","id":...,"status":{...},"final":false}
官方要: {"status_update":{"taskId":...,"status":{...},"final":false}}
我发: {"kind":"message","role":...}
官方要: {"message":{"role":...,"parts":[...]}}
我发: {"kind":"task","artifacts":[...]}
官方要: {"artifact_update":{"taskId":...,"artifact":{"parts":[...]}}}

## 修后(照实)
· message/stream 事件序列改为 oneof 包壳:
  status_update(SUBMITTED) -> status_update(WORKING) -> artifact_update*(每个artifact) -> status_update(终态·final:true)
· tck-message-response 时: 纯 message 流(无task事件)
· 末事件: {"message":{...}} 或 {"status_update":{...final:true}}

## 进展(照实)
MUST 30->31|SHOULD 19->20
十三轮累计: MUST 10->31|SHOULD 6->20

## 关键判据
· StreamResponse 是 oneof·要包壳({"status_update":{}})
· 不是 {"kind":"..."}·这是A2A v1.0的wire格式
· artifact 单独事件(不是塞在task里)
· tck-message-response 要纯message流

## 备份
p2p_mailbox.py.bak-before-oneof-20261112
