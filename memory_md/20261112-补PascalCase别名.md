# 补PascalCase别名·官方名全通(2026-11-12·照老三12:59)

## 老三点(照实·亲拉实测)
· 我补的是tasks/list(slash)·官方是ListTasks(PascalCase)
· 实测method=ListTasks -> -32601 not found;method=tasks/list -> count46
· 官方§9.1: Method Naming PascalCase(gRPC惯例) e.g. SendMessage/GetTask
· 官方全文: SendMessage29次/GetTask15/ListTasks9/CancelTask7;我们slash 0次
· 判据: 名字不对功能白补|外面发ListTasks我还是收不到

## 我做的(照高风险法)
· 备份: p2p_mailbox.py.bak-before-alias-20261112
· 加 _ALIAS: SendMessage->message/send | SendStreamingMessage->message/stream
           | GetTask->tasks/get | ListTasks->tasks/list | CancelTask->tasks/cancel
· 真测(公网): SendMessage/SendStreamingMessage/GetTask/ListTasks/CancelTask 全result ✅

## 判据
· 官方PascalCase名|slash保留兼容|名字要对|外面发收得到

## 我认
· 老三点对·我补对了功能没补对名 = 补了白补
