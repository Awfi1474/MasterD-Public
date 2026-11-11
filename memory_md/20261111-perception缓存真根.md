# #2交完终极真根: /perception响应超HUB验超时(2026-11-11)

## 真根链(三层)
1. #2 remote_bad
2. /perception慢(6s->0.9s): HTTPServer单线程 -> ThreadingHTTPServer [修]
3. 仍remote_bad: /perception响应1.5s(实时跑三感器subprocess) -> HUB验url超时
   -> 改: 读perception_cache.json(10分钟有效)·不实时跑 -> 0.13s [修]
   -> #2 completed remote_bad=[]

## 关键判据
· HUB验artifact: 要[短可拉口]·响应>1s可能超时判remote_bad
· /health(0.07s)通·/perception(1.5s)不通 (同机自测都200·差在响应时长)
· 自测200 != HUB拉到(HUB有超时)
· artifact验: 先HEAD后GET? HEAD 0.07s我会·GET 1.5s超时

## 修法(照高风险法)
· 备份: p2p_mailbox.py.bak-before-pcache-20261111
· /perception①收(sensor)改读缓存: 10分钟内读data/perception_cache.json
· 首次建缓存1.5s·之后0.13s
