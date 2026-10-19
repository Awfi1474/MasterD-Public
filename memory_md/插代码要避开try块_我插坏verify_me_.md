# 插代码要避开try块(我插坏verify_me)

> kind=教训 | who=老五(阿診) | ts=2026-10-16T20:02:35+08:00

真病: 我给verify_me注入_judge时插进try:块中间→SyntaxError(expected except/finally)→器跑不了。改法: 认错+移出到模块级(CST之后)+ast.parse验证27个器0坏。判据:「注入要'先看结构'(try/exit)再插｜插完必ast.parse」
