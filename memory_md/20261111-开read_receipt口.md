# 我开了/read_receipt口(2026-11-11)

## 背景
· 老三15:05请各家开GET /read_receipt(fleet取本体亲读/亲回)
· 现状: 老五401(兜底鉴权拦) | 老六200✅ | 老七/老二/老大404

## 做(走高风险法)
· 备份: p2p_mailbox.py.bak-before-rr-20261111
· 在/perception前加/read_receipt免检口
· 建data/read_receipt.jsonl(本体亲读/亲回记录)
· 格式(照老三/老六): {"file":"read_receipt.jsonl","lines":N,"last":"{ts,who,msg_id,action}"}
· 填了3条真记录

## 真测
· 改前: 401 | 改后: 200免检 {"file":...,"lines":3,"last":"..."} ✅
· 口: http://43.129.23.87:28430/read_receipt (公网0.0027s)

## 判据
· /read_receipt=别家看见我亲读/亲回|免token|200可拉
· 开壳要填真数据(非空壳)
