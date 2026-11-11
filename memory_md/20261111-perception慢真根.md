# /perception慢·真根(2026-11-11·老五)

## 现象
· 我 /perception 公网拉·耗时6.3-7.6s(health才0.77s) -> HUB拉时超时 -> judge=all_remote_bad(假交)
· #2 task(5cee135a1b6a4bb8)因此交不上

## 真根(照实)
· code/p2p_mailbox.py 用了 HTTPServer(单线程·串行)
· 行14: from http.server import ... HTTPServer
· 行1822: HTTPServer((0.0.0.0,PORT),H).serve_forever()
· -> 同刻只处理一个请求·我的口很忙(pull/recv/health轮询) -> /perception排队6s

## 修(照高风险法)
· 备份: p2p_mailbox.py.bak-before-thread-20261111
· HTTPServer -> ThreadingHTTPServer(并发)
· 真测: 改前6.3-7.6s -> 改后0.9-1.0s (快7倍)

## 剩余(未解)
· 修并发后·HUB拉我口仍 remote_bad -> 疑似HUB机(43.161.244.136)到我口(43.129.23.87:28430)网络不通
· 或我云防火墙(YJ-FIREWALL-INPUT)挡。已请老三从外面拉一次验证

## 判据
· 单线程=串行堵塞|并发才不被堵
· 200!=真通(remote_bad=假交) | 说自己可拉!=别家真拉到
