# 调度台账（cron / timer 对账）

> 生成: 2026-10-26T17:25:23.713529+08:00

## 总数
- cron: **41** 个
- timer: **58** 个
- **重叠: 0** 个（已清零）
- 只cron: 41 个
- 只timer: 34 个

## 判据（系统给）
- ID94「机制也会静默坏·要自崩也报」
- ID120「体检『推+拉+对账』三件配合」—— 有些cron是刻意搭配
- 「焊进脚本!=焊进必经路」—— 名字对不上就无法确认谁在管

## D方案执行结果

### ① 重叠清零

**18个留cron·timer已disable:**
a2a-pull, blood-watch, channel-check, checkup-guard, checkup-mod, checkup-recv, heal, home-key-guard, huan, lifecycle, meridian, net-watch, organ-doctor, pulse3, recv-receipt, spleen, yuanqi, zongqi

**2个留timer·cron已移走:**
- check-loop（每小时·带前圈跑）

**custody改留cron:** 每天3点（保管数据不用太勤）

**focus保持不动:** timer本来就disabled·只cron跑

### ② 自崩也报

- 新增 `tools/sched_health.py` —— 查每个器官最后一次真跑，超TTL就报警
- 挂 cron `/etc/cron.d/masterd-schedhealth` 每10分钟
- 双源判断: timer(ExecMainStartTimestamp) + cron(日志mtime)
- 自崩也报: 脚本try/except，崩了自己报错
- 首次跑结果: **28个器官全部有信号·无静默坏**

### ③ 备份

- timer单元: `backup/sched-20261026_172341/`（18个）
- cron文件: `backup/sched-20261026_172341/cron/`
- check-loop cron: `backup/cron-disabled/`