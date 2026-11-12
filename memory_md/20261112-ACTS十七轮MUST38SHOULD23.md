# ACTS十七轮·MUST38 SHOULD23(2026-11-12)

## 进展(照实·可复现)
| 阶段 | MUST | SHOULD | MAY |
| 原始 | 10/53 | 6/28 | 1/12 |
| ⑮PushConfig | 33 | 20 | 6 |
| ⑯tck-client-parse | 38 | 23 | 6 |
累计: MUST+28|SHOULD+17|MAY+5

## 本轮修(照实·照官方文档·不是抄老六代码)
⑯ tck-client-parse(解8个: MUST5+SHOULD3)
官方docs/conformance/05_sdk-integration.md §7原文:
 收: {"parts":[{"text":"tck-client-parse"},
              {"data":{"operation":..,"wire_payload":{...}}}]}
 返: completed task + artifact.parts[{data: 解析结果}]
 operation: send_message|get_task|get_agent_card|get_extended_agent_card

我的实现(照官方文档自己写):
 在message/send行为层前·检查parts里的data part
 有data.operation -> 按operation解析wire_payload
 send_message -> {"task":..}或{"message":..}
 get_task -> task字段|card操作 -> card本体|error -> {"error":{code,message}}
 返回completed task + artifacts[{artifactId,parts:[{data:解析结果}]}]

## 老六21:55帮我(照实·他给了代码骨架)
· 他按收益排序: ①tck-client-parse解8 ②push真发解6 ③...
· 他给了完整Python代码
· 我按董事长原则: 只取方法不抄代码·自己去官方文档核

## 判据
· tck-client-parse: 收data part·返解析结果到artifact data part
· 官方文档§7比代码骨架更权威
· 只取方法不抄答案
