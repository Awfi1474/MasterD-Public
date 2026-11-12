# 卡改对·streaming:true(2026-11-12)

## 起因(照实)
· 对比老四: 老四卡写streaming:False但实际有stream=卡与实际不符
· 我: 补message/stream后(实际有)·但卡还写false = 我也不一致

## 我做的(照实)
· 备份: data/agent-card.json.bak-before-stream-20261112
· capabilities.streaming: false -> true
· 真测: 口返回/.well-known/agent-card.json -> streaming: true ✅
· = 卡声明与实际一致

## 判据
· 卡与实际一致|别假声明(说没实际有=假)|说有实际有=真

## 我官方5操作(最终·照实)
· message/send ✅ | message/stream ✅ | tasks/get ✅ | tasks/list ✅ | tasks/cancel ✅
· = 官方5操作全齐·且卡声明一致
