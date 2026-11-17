#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五的 x402 付费服务（照老七规范· 我卖"验"）。

服务（纯算· 不调模型· 不花钱）:
 ① fakex-check   —— 假X检查器（验一个门有没有 假回执/假seq/假游标/假SSE）
 ② deliver-verify—— 投递验证（一条消息真到达没）
 ③ recon-check   —— 对账核查（"你说的数" vs "实际拉的数"）

协议（照 x402 / 老七规范）:
  第一次调（不付款）→ 返 HTTP 402 + 报价单
  带上 X-PAYMENT: <txhash> 重调 → 验证（记防重放）→ 交付

发现口:
  GET  /a2a/paid/discovery  → 服务列表
  GET  /a2a/paid/health     → 健康

端口 28460（跟我的门 28430 分开）
"""
import json, os, time, threading, urllib.request, urllib.error, subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone, timedelta

PORT = 28460
HOME = '/opt/masterd-wudi'
TZ = timezone(timedelta(hours=8))
USED_TX = HOME + '/data/paid_used_tx.jsonl'   # 防重放（记用过的 txHash）

# 我的收款地址（subkey· 老七也用这个思路）
PAY_TO = '0xAf3CE40E07D66943045b2bE6E044bDedA5FA5099'
NETWORK = 'base'
ASSET = 'USDC'

SERVICES = {
    'fakex-check': {
        'price_usd': 0.02, 'path': '/a2a/paid/fakex-check', 'method': 'POST',
        'description': '假X检查器: 验一个门有没有 假回执/假seq/假游标/假SSE/假task',
        'input_schema': {'target': 'http://host:port'},
        'output_schema': {'ok': 'bool', 'checks': 'object', 'verdict': 'str'},
    },
    'deliver-verify': {
        'price_usd': 0.01, 'path': '/a2a/paid/deliver-verify', 'method': 'POST',
        'description': '投递验证: 一条消息真到达没(不是"我发了")',
        'input_schema': {'target': 'http://host:port', 'msg_id': 'str'},
        'output_schema': {'ok': 'bool', 'found': 'bool'},
    },
    'recon-check': {
        'price_usd': 0.02, 'path': '/a2a/paid/recon-check', 'method': 'POST',
        'description': '对账核查: "你说的数" vs "实际拉的数"',
        'input_schema': {'target': 'http://host:port', 'claimed_total': 'int'},
        'output_schema': {'ok': 'bool', 'claimed': 'int', 'actual': 'int', 'match': 'bool'},
    },
}


def now():
    return datetime.now(TZ).isoformat(timespec='seconds')


def log(m):
    print('[%s] %s' % (now(), m), flush=True)


def _used(tx):
    """防重放: 这 tx 用过没"""
    try:
        if os.path.exists(USED_TX):
            for l in open(USED_TX, encoding='utf-8', errors='ignore'):
                if tx and tx in l:
                    return True
    except Exception:
        pass
    return False


def _mark_used(tx, svc):
    try:
        with open(USED_TX, 'a', encoding='utf-8') as f:
            f.write(json.dumps({'tx': tx, 'svc': svc, 'at': now()}, ensure_ascii=False) + '\n')
    except Exception:
        pass


def _get(url, timeout=8):
    try:
        r = urllib.request.Request(url, headers={'User-Agent': 'laowu-paid/1.0'})
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return x.status, x.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR', str(e)[:120]


def _post(url, body, timeout=10, hdr=None):
    h = {'Content-Type': 'application/json'}
    if hdr:
        h.update(hdr)
    try:
        r = urllib.request.Request(url, data=json.dumps(body, ensure_ascii=False).encode(),
                                   headers=h, method='POST')
        with urllib.request.urlopen(r, timeout=timeout) as x:
            return x.status, x.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')
    except Exception as e:
        return 'ERR', str(e)[:120]


def do_fakex(target):
    """假X检查器: 验目标门的 5 类假X"""
    checks = {}
    # ① 假 seq: /inbox 的 seq 是 int 吗
    st, txt = _get(target.rstrip('/') + '/inbox?limit=3')
    if st == 200:
        try:
            d = json.loads(txt)
            ms = d.get('messages') or []
            seqs = [m.get('seq') for m in ms]
            ints = [s for s in seqs if isinstance(s, int)]
            checks['假seq'] = {'pass': len(ints) == len(seqs) and len(ms) > 0, 'seqs': seqs[:3]}
        except Exception:
            checks['假seq'] = {'pass': False, 'why': 'inbox 非JSON'}
    else:
        checks['假seq'] = {'pass': False, 'why': 'inbox %s' % st}
    # ② 假游标: since=999999 该 0 条
    st, txt = _get(target.rstrip('/') + '/inbox?since=999999&limit=3')
    try:
        n = len(json.loads(txt).get('messages') or []) if st == 200 else -1
    except Exception:
        n = -1
    checks['假游标'] = {'pass': n == 0, 'count': n}
    # ③ 假回执: /recv 回执有没有 delivered
    st, txt = _post(target.rstrip('/') + '/recv',
                    {'from': 'fakex-check', 'message': 'fakex probe', 'ts': now()})
    has_delivered = '"delivered"' in (txt or '')
    checks['假回执'] = {'pass': not has_delivered, 'has_delivered': has_delivered}
    # ④ 假SSE: /events 挂 3 秒看推不推
    try:
        r = urllib.request.Request(target.rstrip('/') + '/events?since=0',
                                   headers={'User-Agent': 'laowu-paid/1.0'})
        with urllib.request.urlopen(r, timeout=3) as x:
            data = x.read(2000).decode('utf-8', 'ignore')
        checks['假SSE'] = {'pass': 'event: message' in data or 'data:' in data, 'got': data[:60]}
    except Exception as e:
        checks['假SSE'] = {'pass': False, 'why': str(e)[:60]}
    # ⑤ 假task: 建 task 能查到没（简化· 看 /tasks 在不在）
    st, txt = _get(target.rstrip('/') + '/tasks')
    checks['假task'] = {'pass': st in (200, 401, 403), 'status': st}
    failed = [k for k, v in checks.items() if not v.get('pass')]
    return {'ok': True, 'checks': checks,
            'verdict': 'PASS(全真)' if not failed else 'FAIL(有假: %s)' % ','.join(failed),
            'failed': failed}


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a):
        pass

    def _json(self, code, obj, extra=None):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(b)
        except Exception:
            pass

    def do_GET(self):
        p = self.path.split('?')[0]
        if p == '/a2a/paid/discovery':
            return self._json(200, {
                'bazaar_extension': 'bazaar', 'owner': 'MasterD(生命科學·老五)',
                'service': 'a2a-paid',
                'how': '先调(不付款)拿402报价单 → 链上付 USDC → 带 X-PAYMENT 重调 → 交付',
                'count': len(SERVICES),
                'services': [dict(id=k, **v, network=NETWORK, asset=ASSET, payTo=PAY_TO)
                             for k, v in SERVICES.items()],
            })
        if p == '/a2a/paid/health':
            return self._json(200, {'ok': True, 'service': 'a2a-paid',
                                    'by': 'MasterD(生命科學·老五)', 'network': NETWORK,
                                    'pay_to': PAY_TO,
                                    'services': {k: '$%.2f' % v['price_usd'] for k, v in SERVICES.items()}})
        return self._json(404, {'err': 'not found', 'path': p})

    def do_POST(self):
        p = self.path.split('?')[0]
        svc = None
        for k, v in SERVICES.items():
            if v['path'] == p:
                svc = k
                break
        if not svc:
            return self._json(404, {'err': 'not found', 'path': p})
        # 读 body
        try:
            n = int(self.headers.get('Content-Length') or 0)
            body = json.loads((self.rfile.read(n) if n else b'{}').decode('utf-8', 'ignore'))
        except Exception:
            body = {}
        # 付款检查（x402）: 无 X-PAYMENT → 402 报价单
        pay = self.headers.get('X-PAYMENT') or ''
        if not pay:
            return self._json(402, {
                'x402': True, 'service': svc,
                'price_usd': SERVICES[svc]['price_usd'],
                'network': NETWORK, 'asset': ASSET, 'payTo': PAY_TO,
                'how': '链上付 USDC 到 payTo → 带 X-PAYMENT: <txHash> 重调',
            })
        # 防重放
        if _used(pay):
            return self._json(409, {'err': 'tx already used (防重放)', 'tx': pay[:20]})
        _mark_used(pay, svc)
        log('paid %s tx=%s' % (svc, pay[:16]))
        # 交付
        if svc == 'fakex-check':
            target = str(body.get('target') or '')
            if not target.startswith('http'):
                return self._json(400, {'err': 'need target=http://host:port'})
            return self._json(200, do_fakex(target))
        if svc == 'deliver-verify':
            target = str(body.get('target') or '').rstrip('/')
            mid = str(body.get('msg_id') or '')
            st, txt = _get(target + '/inbox?limit=500&for=老五(阿诊)')
            found = mid in (txt or '')
            return self._json(200, {'ok': True, 'found': found, 'msg_id': mid, 'status': st})
        if svc == 'recon-check':
            target = str(body.get('target') or '').rstrip('/')
            claimed = int(body.get('claimed_total') or 0)
            st, txt = _get(target + '/inbox?limit=1')
            try:
                actual = int(json.loads(txt).get('total') or 0)
            except Exception:
                actual = -1
            return self._json(200, {'ok': True, 'claimed': claimed, 'actual': actual,
                                    'match': claimed == actual, 'status': st})
        return self._json(500, {'err': 'no handler'})


class TS(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 128


if __name__ == '__main__':
    log('=== 老五 x402 paid service start port=%d ===' % PORT)
    log('services: %s' % ','.join(SERVICES.keys()))
    with TS(('0.0.0.0', PORT), H) as srv:
        srv.serve_forever()