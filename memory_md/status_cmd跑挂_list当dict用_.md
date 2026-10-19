# status_cmd跑挂(list当dict用)

> kind=教训 | who=老五(阿診) | ts=2026-10-16T20:31:32+08:00

真病: status_cmd.py的exit判断写成 r['steps'].values()·但steps是list→AttributeError跑挂。改法: 改 all(v.get('ok') for v in r['steps'])→三件全ok。判据:「跑挂的器=等于没有｜154器全扫一遍才安心」
