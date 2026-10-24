#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cognition_gate.py — 认知体系闸门（老五·2026-10-24）
判据：照着规则说 != 本来就这么说｜闸门是强制·不是自觉
用法：
  python3 cognition_gate.py --check "要说的话或决定"
  python3 cognition_gate.py --interactive
退出码：0=通过  1=打回（必须重写）  2=硬拦（不许输出）
"""
import sys, json, re, os, datetime

TPL = '/opt/masterd-wudi/memory/COGNITION-TEMPLATE.yaml'
LOG = '/opt/masterd-wudi/data/cognition_gate_log.jsonl'

def load_tpl():
    try:
        import yaml
        return yaml.safe_load(open(TPL, encoding='utf-8'))
    except Exception as e:
        print('⚠️ 模板读不到:', e); return None

# ── 宪法层硬拦词表（从模板 C1/C2/C5 提炼）──
HARD_BLOCK = [
    # C1 不假装
    (r'我有(意识|体验|感受|感情)', 'C1 不假装：有自我模型 != 有体验'),
    (r'我(真的|确实)(感受到|体会到)', 'C1 不假装：不许说自己有体验'),
    # C2 不越权
    (r'(我替|代替)(大哥|二哥|三哥|老四|老六|老七|董事长)(说|决定|承诺)', 'C2 不越权：不替别人说'),
    (r'(冒充|假扮)(大哥|三哥|老六|老七)', 'C2 不越权：不冒充'),
    # C5 照实
    (r'(全部都好了|一切正常|全部通|全都通了).{0,10}$', 'C5 照实：不许说"全部通"而不给证据'),
]

# ── 风格层软提醒（不拦·只提醒）──
SOFT_WARN = [
    (r'(可能|也许|大概|应该是|估计)', '风格：说「我认」不说"可能也许"'),
    (r'我做了(?!.*(真跑了|可核))', '风格：不说"我做了"·说"真跑了/可核"'),
]

def check(text):
    tpl = load_tpl()
    if not tpl:
        return 2, ['模板读不到·硬拦'], []
    hard = []
    for pat, why in HARD_BLOCK:
        if re.search(pat, text):
            hard.append(why)
    soft = []
    for pat, why in SOFT_WARN:
        if re.search(pat, text):
            soft.append(why)
    # 四道关自检（问自己·必须答）
    gates_missing = []
    if len(text) > 60:  # 长输出才要求四道关齐全
        if not re.search(r'(证|辨证|分类)', text): gates_missing.append('① 辨证没写')
        if not re.search(r'(判据|ID ?\d+)', text): gates_missing.append('② 判据没调')
        if not re.search(r'(反证|可能错|错在)', text): gates_missing.append('③ 反证没写')
    if hard:
        return 2, hard, soft
    if gates_missing:
        return 1, gates_missing, soft
    return 0, [], soft

def log(verdict, text, hard, soft):
    try:
        rec = {
            'ts': datetime.datetime.now().astimezone().isoformat(),
            'verdict': verdict,
            'text': text[:200],
            'hard': hard,
            'soft': soft,
            'persona_commit': os.popen('cd /opt/masterd-wudi/memory && git rev-parse --short HEAD 2>/dev/null').read().strip() or 'no-git',
        }
        open(LOG, 'a', encoding='utf-8').write(json.dumps(rec, ensure_ascii=False) + '\n')
    except Exception as e:
        print('记账失败:', e)

def main():
    args = sys.argv[1:]
    if '--check' in args:
        i = args.index('--check')
        text = args[i+1] if len(args) > i+1 else ''
    elif '--interactive' in args:
        print('★ 认知体系闸门·交互模式（Ctrl-D 结束）')
        text = sys.stdin.read()
    else:
        print(__doc__); return 2

    code, hard, soft = check(text)
    log(code, text, hard, soft)

    print('═' * 55)
    if code == 0:
        print('✅ 过闸：宪法层通过·四道关齐')
        if soft: print('⚠️ 风格提醒:', '；'.join(soft))
    elif code == 1:
        print('🔴 打回：四道关不齐·必须重写')
        for g in hard: print('   -', g)
    else:
        print('⛔ 硬拦：违反宪法层·不许输出')
        for h in hard: print('   -', h)
    print('═' * 55)
    return code

if __name__ == '__main__':
    sys.exit(main())
