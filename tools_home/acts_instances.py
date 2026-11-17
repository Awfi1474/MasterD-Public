#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ACTS reduced/auth 实例（照官方 acts_runner 说明：只需"发布更小的 capabilities"）。

官方原话:
  "honouring this usually means nothing more than publishing a smaller
   capabilities block"
  REDUCIBLE_CAPABILITIES = ('streaming', 'pushNotifications', 'extendedAgentCard')
  AUTH pass: "the card declares no security requirement and the test needs one"

做法:
  一个轻量 server 挂两个口:
    28431 → reduced（capabilities 缩小）
    28432 → auth（声明 security requirement·无认证头→401）
  协议行为转发到主门 28430（同实现·只是 card 不同 + auth 门）

判据: «官方要的是"另一个 card"· 不是"另一套实现"»
"""
import json, os, sys, threading, urllib.request, urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MAIN = 'http://127.0.0.1:28430'
REDUCED_PORT = 28431
AUTH_PORT = 28432

# 两张小卡
CARD_REDUCED = {
    "name": "MasterD(生命科學·老五)·reduced",
    "description": "ACTS reduced-capability instance",
    "protocolVersion": "1.0",
    "supportedInterfaces": [{"url": "http://127.0.0.1:28431/a2a-jsonrpc",
                             "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}],
    "capabilities": {"streaming": False, "pushNotifications": False,
                     "extendedAgentCard": False, "extensions": []},
    "defaultInputModes": ["text/plain"],
    "defaultOutputModes": ["application/json"],
    "skills": [{"id": "env-selftest", "name": "环境自检", "description": "x",
                "tags": ["x"], "examples": ["x"],
                "inputModes": ["text/plain"], "outputModes": ["application/json"]}],
}
CARD_AUTH = dict(CARD_REDUCED)
CARD_AUTH["name"] = "MasterD(生命科學·老五)·auth"
CARD_AUTH["description"] = "ACTS auth-enforced instance"
CARD_AUTH["supportedInterfaces"] = [{"url": "http://127.0.0.1:28432/a2a-jsonrpc",
                                     "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}]
CARD_AUTH["capabilities"] = {"streaming": True, "pushNotifications": False, "extensions": []}
CARD_AUTH["securitySchemes"] = {
    "bearer": {"httpAuthSecurityScheme": {"scheme": "bearer", "bearerFormat": "JWT"}}
}
CARD_AUTH["securityRequirements"] = [{"schemes": {"bearer": {}}}]


class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    KIND = 'reduced'   # 子类覆盖

    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        b = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        try:
            self.wfile.write(b)
        except Exception:
            pass

    def _card(self):
        return CARD_REDUCED if self.KIND == 'reduced' else CARD_AUTH

    def do_GET(self):
        p = self.path.split('?')[0]
        if p in ('/.well-known/agent-card.json', '/agent-card.json'):
            return self._json(200, self._card())
        if p == '/health':
            return self._json(200, {"ok": True, "who": "MasterD(生命科學·老五)·" + self.KIND,
                                    "kind": self.KIND, "note": "ACTS " + self.KIND + " instance"})
        # 其余 GET 转发主门
        return self._forward('GET', None)

    def do_POST(self):
        n = int(self.headers.get('Content-Length') or 0)
        body = self.rfile.read(n) if n else b''
        # auth 实例: 无 Authorization 头 → 401（官方 SEC-AUTH 期望"拒绝未授权"）
        if self.KIND == 'auth':
            auth = self.headers.get('Authorization') or ''
            # ★ 2026-11-17 修(照 ACTS runner L80-84: 两个固定token)
            #   itk-valid-token → 200(有效) · itk-insufficient-token → 403(认证但不授权)
            #   判据: «认证!=授权|有效200|不足403|无401»
            if not auth:
                return self._json(401, {"jsonrpc": "2.0", "id": None,
                                        "error": {"code": -32600, "error_type": "InvalidRequestError",
                                                  "message": "Unauthorized: missing credentials",
                                                  "data": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                                                            "reason": "UNAUTHENTICATED",
                                                            "domain": "a2a-protocol.org"}]}})
            if 'itk-insufficient-token' in auth:
                return self._json(403, {"jsonrpc": "2.0", "id": None,
                                        "error": {"code": -32600, "error_type": "ForbiddenError",
                                                  "message": "Forbidden: insufficient permissions",
                                                  "data": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                                                            "reason": "PERMISSION_DENIED",
                                                            "domain": "a2a-protocol.org"}]}})
        # ★ reduced 实例: 行为也要降（不能只改 card）—— streaming 该拒
        _p = self.path.split("?")[0]
        # ★ 2026-11-17 修2(照实: ACTS用method=SendStreamingMessage· 不是路径)
        _is_stream = False
        try:
            _bj = json.loads(body.decode('utf-8','ignore')) if body else {}
            _mth = str(_bj.get('method') or '')
            _is_stream = _mth in ('SendStreamingMessage', 'SubscribeToTask', 'message/stream', 'tasks/subscribe')
        except Exception:
            pass
        if self.KIND == "reduced" and (_p in ("/a2a/stream", "/message:stream") or _is_stream):
            return self._json(200, {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32004, "error_type": "UnsupportedOperationError",
                          "message": "UnsupportedOperationError: streaming not supported",
                          "data": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                                    "reason": "UNSUPPORTED_OPERATION", "domain": "a2a-protocol.org"}]}})
        return self._forward('POST', body)

    def _forward(self, method, body):
        url = MAIN + self.path
        try:
            # ★ 2026-11-17 修(照实: 转发漏带 A2A-Version → 主门判0.3 → 返VersionNotSupported)
            #   判据: «转发要透传头|漏一个头=换一个错»
            _hdrs = {'Content-Type': 'application/json'}
            for _h in ('A2A-Version', 'Authorization', 'X-Hub-Token'):
                _v = self.headers.get(_h)
                if _v:
                    _hdrs[_h] = _v
            req = urllib.request.Request(url, data=body, method=method, headers=_hdrs)
            with urllib.request.urlopen(req, timeout=25) as x:
                data = x.read()
                self.send_response(x.status)
                self.send_header('Content-Type', x.headers.get('Content-Type', 'application/json'))
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            d = e.read()
            self.send_response(e.code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(d)))
            self.end_headers()
            self.wfile.write(d)
        except Exception as e:
            self._json(502, {"err": str(e)[:80]})




# ★ 2026-11-17 加(照ACTS SEC-AUTH-002: 要带凭证但权限不足实例)
PERM_PORT = 28433
CARD_PERM = dict(CARD_AUTH)
CARD_PERM["name"] = "MasterD(生命科學·老五)·perm"
CARD_PERM["description"] = "ACTS insufficient-permission instance"
CARD_PERM["supportedInterfaces"] = [{"url": "http://127.0.0.1:28433/a2a-jsonrpc",
                                       "protocolBinding": "JSONRPC", "protocolVersion": "1.0"}]


class HPerm(H):
    KIND = 'perm'

    def _card(self):
        return CARD_PERM

    def do_POST(self):
        # 带凭证 → 403(权限不足)· 无凭证 → 401
        auth = self.headers.get('Authorization') or ''
        if not auth:
            return self._json(401, {"jsonrpc": "2.0", "id": None,
                "error": {"code": -32600, "error_type": "InvalidRequestError",
                           "message": "Unauthorized: missing credentials"}})
        return self._json(403, {"jsonrpc": "2.0", "id": None,
            "error": {"code": -32600, "error_type": "ForbiddenError",
                       "message": "Forbidden: insufficient permissions",
                       "data": [{"@type": "type.googleapis.com/google.rpc.ErrorInfo",
                                   "reason": "PERMISSION_DENIED", "domain": "a2a-protocol.org"}]}})


class HRed(H):
    KIND = 'reduced'


class HAuth(H):
    KIND = 'auth'


def serve(port, cls):
    srv = ThreadingHTTPServer(('0.0.0.0', port), cls)
    srv.daemon_threads = True
    srv.request_queue_size = 128
    print("[%s] listening %d" % (cls.KIND, port), flush=True)
    srv.serve_forever()


if __name__ == '__main__':
    threading.Thread(target=serve, args=(REDUCED_PORT, HRed), daemon=True).start()
    threading.Thread(target=serve, args=(PERM_PORT, HPerm), daemon=True).start()
    serve(AUTH_PORT, HAuth)