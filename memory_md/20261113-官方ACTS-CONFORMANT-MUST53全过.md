# ★★★ 官方ACTS CONFORMANT·MUST53/53全过(2026-11-13)

## 最终成绩(照实·可复现)
MUST    53/53 passed (6 skipped)   ✅
SHOULD  28/28 passed (1 skipped)   ✅
MAY     12/12 passed (1 skipped)   ✅
=> CONFORMANT

## 全程(29轮·照实)
| 级别 | 起点 | 终点 |
| MUST | 10/53 | 53/53 |
| SHOULD | 6/28 | 28/28 |
| MAY | 1/12 | 12/12 |

## 关键真根(照实·按发现顺序)
① result.id -> result.task.id + TASK_STATE_COMPLETED
② tck-* 行为层(14前缀·最长优先)
③ SSE关流(末事件后close_connection)
④ GetTask真读a2a_tasks.jsonl(原查memory.db两处对不上)
⑤ CARD: protocolVersion 1.0 + Cache-Control + ETag
⑥ contextId复用(多轮同task)
⑦ 终态拒续(-32004)
⑧ CancelTask查taskboard
⑨ 多轮状态机(INPUT_REQUIRED->done->COMPLETED)
⑩ history+historyLength
⑪ VER-NEG-002(无A2A-Version头->-32009)
⑫ SubscribeToTask返SSE
⑬ StreamResponse oneof包壳({"status_update":{}}不是{"kind":"task"})
⑭ artifacts parts + Z时间戳
⑮ PushConfig id+url顶层
⑯ tck-client-parse(收data part返解析结果)
⑰ push真发+Authorization头
⑱ long-running推进(WORKING->COMPLETED)
⑲ SEND-004(不支持mediaType->-32005) + SUB-003(订阅终态->-32004)
⑳ 坏JSON->200+-32700 | 缺method->-32600
㉑ artifacts三类型(data/file/file-url)
㉒ ListTasks读a2a_tasks.jsonl+contextId过滤
㉓ contextId为空要生成
㉔ -32601结构+auth_required
㉕ push body要{"statusUpdate":{...}}包壳(notifications_app._extract_task_id_v10)
㉖ SSE首事件status_update包壳
㉗ cfgid统一(存和返同一个)
㉘ taskId不存在->-32001
㉙ @type要type.googleapis.com/google.rpc.ErrorInfo
㉚ contextId不匹配->-32602

## 判据(照实·焊死)
· 官方docs和wire_map注释比代码骨架权威
· 只取方法不抄答案(老六给方向·我去官方文档核)
· 一次修一类(能解多个的优先)
· 修了!=修好了·跑官方ACTS才算验过
· 自造探针判全绿=假绿|官方ACTS判不合规=真相

## 备份
p2p_mailbox.py.bak-before-* 各阶段(29个备份)

## 跑法(可复现)
cd /opt/masterd-wudi/standards/a2a-itk
sudo -n env PATH=/root/.local/bin:$PATH python3 run_acts.py \
  --sut-url http://127.0.0.1:28430 --sdk laowu --transport jsonrpc \
  --behaviors acts/sut-behaviors.yaml
