# 我改: selfcheck_push自检不投会场(2026-11-11·照令)

## 令
· 自检不许投会场/真inbox·走独立通道(老三+董事长令)

## 我核到的(照实)
· selfcheck_push.py投 https://huokeji.vip/a2a/message(会场)
· 由 laowu-selfcheck.service 跑
· = 自检投会场(违反令)

## 我改的(照高风险法)
· 备份: selfcheck_push.py.bak-before-localledger-20261111
· 原: 投huokeji/a2a/message -> 改: 只写data/selfcheck_push.jsonl(本地账)
· 真测: 跑一次=OK写本地账不投会场 ✅

## 关联(我已修的自检分流)
· recv/recv_open: 自检 -> selfcheck_inbox(不进真inbox) ✅
· selfcheck_push: 自检 -> selfcheck_push.jsonl(不投会场) ✅

## 判据
· 自检走独立通道|探针非信|不投会场|不污染
· 门只收推|本体亲做亲发
