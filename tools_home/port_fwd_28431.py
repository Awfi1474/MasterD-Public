#!/usr/bin/env python3
"""老五 · 端口转发 28431 → 28430（因为公开说明里写了 28431·但它没服务）
判据: 别人按旧说明投 28431 → 应该也能通（转给真口）"""
import socket, threading, sys
LISTEN, TARGET = 28431, ("127.0.0.1", 28430)
def pipe(a, b):
    try:
        while True:
            d = a.recv(65536)
            if not d: break
            b.sendall(d)
    except Exception: pass
    finally:
        try: a.close()
        except Exception: pass
        try: b.close()
        except Exception: pass
def handle(c):
    try:
        s = socket.create_connection(TARGET, timeout=8)
        threading.Thread(target=pipe, args=(c, s), daemon=True).start()
        pipe(s, c)
    except Exception:
        try: c.close()
        except Exception: pass
def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", LISTEN)); srv.listen(50)
    print("  ★ 转发启动: 0.0.0.0:%d → %s:%d" % (LISTEN, TARGET[0], TARGET[1]), flush=True)
    while True:
        c, _ = srv.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()
if __name__ == "__main__":
    main()
