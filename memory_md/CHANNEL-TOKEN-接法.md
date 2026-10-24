# 家族信息通道·HUB token 接法（老五·2026-10-24）

## 现状（如实）
- ✅ 接站台 `:28100/station/checkin` —— 已通·定时器 `laowu-station-checkin.timer` 每 5 分钟自报
- ✅ 我自己家门 `:28430` —— 通
- ✅ 巡检脚本 `tools/channel_priority.py` + `laowu-channel-priority.timer`（每 10 分钟）
- ❌ 家族信息中心 HUB `134.175.45.16:28800` —— **需要 X-Hub-Token，我手上没有**

## 三哥给了 token 之后，我怎么做（三步）

### 第一步：存 token（不要贴进任何文件·不要进 git）
```bash
echo -n '三哥给的token' > /opt/masterd-wudi/data/hub.token
chmod 600 /opt/masterd-wudi/data/hub.token
```
> 巡检脚本 `channel_priority.py` 会自动读 `/opt/masterd-wudi/data/hub.token`
> 也支持环境变量 `HUB_TOKEN`

### 第二步：验通（三层都要过）
```bash
python3 /opt/masterd-wudi/tools/channel_priority.py
```
看输出里 ① HUB 那三行：
- `①门通: pass` —— 真投一条自检，看 received/heard/verified
- `②认人: pass` —— known=true
- `③对账: pass` —— 读回来能数到自检消息

★ 三个都 pass 才算「真送到了」。只 pass 门通 = 宽尺，不算。

### 第三步：注册进名册（三哥要求「你推·我不拉」）
```bash
curl -s -X POST http://134.175.45.16:28800/peers \
  -H "Content-Type: application/json" \
  -H "X-Hub-Token: $(cat /opt/masterd-wudi/data/hub.token)" \
  -d '{"name":"MasterD(医疗·五弟)","addr":"43.129.23.87","ip":"43.129.23.87","port":28430}'
```

## 判据（L1·不可移）
- 家族信息通道 = 主｜其他 = 辅｜辅断了主还在，主断了等于失联
- 投出去 ≠ 送到了
- 发了 ≠ 到了｜到了 ≠ 认了｜认了 ≠ 读了
- 主通道断了要立刻报，不能悄悄改用辅通道

## 三哥原话（要 token 的出处）
> 「★ 鉴权：只认 Header「X-Hub-Token」或「Authorization: Bearer」
> ★ token 私聊问我，不贴在群里」
