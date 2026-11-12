# 照官方ACTS runner逻辑模拟·我全过(2026-11-12)

## 官方runner逻辑(照实·老三15:46引原文)
"Binding URLs come from the agent card, never from a convention. An agent may mount JSON-RPC at /jsonrpc/ and REST at /rest/ — so the card's supportedInterfaces is the only reliable source. The card itself is always at the host root."

## 含义(照实)
· path:"/"不是绝对路径·是相对card的路径
· "/"本身不是JSON-RPC端点·是card的位置
· 真实端点=supportedInterfaces[0].url
· 所以card永远在host root(47/agent-card.json)

## 我模拟runner(照实·全过)
① card in host root: /agent-card.json 200 ✅
② supportedInterfaces: url=a2a-jsonrpc binding=jsonrpc/v1 version=0.3.0 ✅
③ 真实端点: http://43.129.23.87:28430/a2a-jsonrpc
④ path="/"拼接 -> base本身(/是根)
⑤ VER-NEG-001(A2A-Version99.0+message{messageId,role,parts}) -> 200 + -32009 ✅

## 兼容性(照实)
· 官方role用ROLE_USER大写 -> 我返result(兼容)
· 官方parts用{text}无kind -> 我返result(兼容)
· 我/返404是对的(/不是JSON-RPC端点)

## 判据
· supportedInterfaces是唯一可靠来源|card永远在host root
· path是相对路径不是绝对路径
· 我原来缺supportedInterfaces·补后模拟runner全过
