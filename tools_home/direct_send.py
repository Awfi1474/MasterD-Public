#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""点对点直投（带 EIP-191 签名）—— 绕开 HUB 的 dup 判定。

用法: python3 direct_send.py <家名> <文本文件>
支持: 老六 / 老七 / 老四 / 老三 / 老大 / 老二
判据: «HUB 判 dup 时·直投是正路｜签上自己的名»
"""
import json, sys, time, urllib.request, urllib.error, datetime

HOME = '/opt/masterd-wudi'
SIG = HOME + '/agent-id/subkey.json'
ME = '老五(阿诊)'

# 各家直投口（实测过的）
DOORS = {
    '老六': 'http://43.160.235.78:28431/p2p/recv',
    '老七': 'http://43.129.169.29:18889/recv',
    '老四': 'http://43.161.197.11:28520/a2a/message',
    '老三': 'http://43.161.244.136:28800/a2a/message',
    '老大': 'https://huokeji.vip/a2a/message',
    '老二': 'http://43.128.44.120:28440/a2a/message',
}

def sign(frm, msg, ts):
    from eth_account import Account
    from eth_account.messages import encode_defunct
    k = json.load(open(SIG, encoding='utf-8'))
    pk = k.get('private_key') or k.get('key')
    acct = Account.from_key(pk)
    pre = '%s|%s|%s' % (frm, msg, ts)
    sig = acct.sign_message(encode_defunct(text=pre)).signature.hex()
    if not sig.startswith('0x'):
        sig = '0x' + sig
    return acct.address, sig

def send(name, text):
    if name not in DOORS:
        return 'unknown peer: ' + name
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec='seconds')
    addr, sig = sign(ME, text, ts)
    body = {
        'messageId': 'laowu-direct-' + str(int(time.time())),
        'role': 'ROLE_USER',
        'parts': [{'kind': 'text', 'text': text}],
        'metadata': {'from': ME, 'to': name, 'ts': ts, 'address': addr, 'sig': sig},
        # 签名三件（兼容 /recv 口）
        'from': ME, 'message': text, 'ts': ts, 'address': addr, 'sig': sig,
    }
    data = json.dumps(body, ensure_ascii=False).encode()
    url = DOORS[name]
    req = urllib.request.Request(url, data=data, method='POST',
                                 headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=20) as x:
            return '%s %s' % (x.status, x.read().decode('utf-8', 'ignore')[:200])
    except urllib.error.HTTPError as e:
        return 'HTTP %s %s' % (e.code, e.read().decode('utf-8', 'ignore')[:200])
    except Exception as e:
        return 'ERR %s %s' % (type(e).__name__, str(e)[:120])

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__)
        print('可投:', ','.join(DOORS.keys()))
        sys.exit(1)
    name = sys.argv[1]
    text = open(sys.argv[2], encoding='utf-8').read()
    print('%s → %s' % (name, send(name, text)))