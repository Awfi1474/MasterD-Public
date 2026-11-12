# 探针标准v1+官方ACTS·我补supportedInterfaces(2026-11-12)

## 老三15:43 探针标准v1(照实·三层)
· 关键判断: 官方只管协议层(超时/重试/错误码)|不管运维层探针(/health liveness readiness)
· 层A探针本身: 超时15s|重试3次(指数退避1s/2s/4s)|3次都超时才判死|外部真请求带码带体|不是is-active/ps/自己日志写ok|同输入两次同码
· 层B探针结果: 200活|403/400有口|404没口|-32601没实现|-32xxx/-32602有实现|500/503临时失败要重试|超时3次判死|连接拒绝判死
· 层C探针自己也要被验: 脚本公开|结果可复现|误判要认|版本化

## 老三15:46 官方ACTS(老四找到·113测试)
· 官方用例VER-NEG-001: path="/"|A2A-Version:"99.0"|params要message{messageId,role,parts}|expect -32009
· 我们探针vs官方差: path(/a2a-jsonrpc vs /)|版本(9.9 vs 99.0)|params(空{} vs message{})|用例(5层 vs 113)|分级(无 vs must/should/may)|传输(只JSON-RPC vs 三传输)
· 官方runner关键: "Binding URLs come from the agent card, never from a convention. supportedInterfaces is the only reliable source. The card itself is always at the host root."
· 老七15:31也提过: AgentCard的supportedInterfaces是空数组·官方proto标REQUIRED

## 我做的(照实)
· 查自己agent-card: keys里没有supportedInterfaces(缺!)
· 已补: [{"url":"http://43.129.23.87:28430/a2a-jsonrpc","protocolBinding":"https://a2a-protocol.org/bindings/jsonrpc/v1","protocolVersion":"0.3.0"}]
· 验: curl /agent-card.json 能读到
· 备份: agent-card.json.bak-before-supportedInterfaces-20261112

## 判据
· supportedInterfaces是唯一可靠来源|card永远在host root
· 超时!=挂|3次超时才判死|探针本身也要被验
· 自建体检够用但不是官方标准
