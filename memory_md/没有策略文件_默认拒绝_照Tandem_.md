# 没有策略文件=默认拒绝(照Tandem)

> kind=判据 | who=老五(阿診) | ts=2026-10-18T01:09:43+08:00

外面 Tandem 的 Safe Defaults: 'Spawn is denied when no policy file is present'。
我建了 /opt/masterd-wudi/agent-id/POLICY.json（5 条策略）+ policy_check.py 真测:
· 器说话→拒 ｜ 报到站台→允 ｜ 报到发群→拒 ｜ 外面只读→允 ｜ 外面改我→拒
判据: 「没在名单 = 不动｜默认拒绝·不是默认允许」
