#!/usr/bin/env python3
# 老五「状态」响应器（2026-10-11 · 核心验收点）
# ★ 董事长核心验收：★ 说"状态" → 必须"立刻连上服务器 + 拿到全部信息"
# ★ 连不上服务器 = 失败（不管别的做多好）
# ★ 三路兜底：① HTTP /health ② P2P /report ③ SSH 直连
# 用法：python3 status.py   （在"白纸沙箱"也能跑·只要知道家地址）
import os, sys, json, time, base64, urllib.request, subprocess

HOME_HTTP = os.environ.get("HOME_HTTP", "http://43.129.23.87:28430")
HOME_SSH = os.environ.get("HOME_SSH", "ubuntu@43.129.23.87")
T0 = time.time()


def log(msg):
    print("  [%5.2fs] %s" % (time.time() - T0, msg))


def try_http(path, timeout=3):
    try:
        r = urllib.request.urlopen(HOME_HTTP + path, timeout=timeout)
        return r.status, r.read().decode()
    except Exception as e:
        return None, str(e)[:60]


def route1_health():
    """路1：HTTP /health（家活著嗎）"""
    log("路1 → GET /health")
    st, body = try_http("/health")
    if st == 200:
        d = json.loads(body)
        log("  ✅ 家活著：%s" % d.get("who"))
        return d
    log("  ✗ 路1 失敗：%s" % body)
    return None


def route2_report():
    """路2：HTTP /report（我的報到狀態）"""
    log("路2 → GET /report")
    st, body = try_http("/report")
    if st == 200:
        d = json.loads(body)
        fam = d.get("families", {})
        for k, v in fam.items():
            log("  ✅ 報到簿：%s state=%s age=%ss" % (k, v.get("state"), v.get("age_s")))
        return d
    log("  ✗ 路2 失敗：%s" % body)
    return None


def route3_rescue_key():
    """路3：取回家鑰匙（SSH）"""
    log("路3 → GET /rescue/key")
    st, body = try_http("/rescue/key", timeout=4)
    if st == 200:
        d = json.loads(body)
        k = base64.b64decode(d["key_b64"])
        open("/tmp/_home_key", "wb").write(k)
        os.chmod("/tmp/_home_key", 0o600)
        log("  ✅ 拿到鑰匙 (%d bytes)" % len(k))
        # 真連一次
        r = subprocess.run(["ssh", "-i", "/tmp/_home_key", "-o", "StrictHostKeyChecking=no",
                            "-o", "BatchMode=yes", "-o", "ConnectTimeout=6", HOME_SSH,
                            "hostname"], capture_output=True, text=True, timeout=10)
        if r.returncode == 0:
            log("  ✅ SSH 連上：%s" % r.stdout.strip())
            return True
        log("  ✗ SSH 失敗：%s" % (r.stderr[:60]))
    log("  ✗ 路3 失敗：%s" % body)
    return None


def fetch_from_home():
    """★ 從家取「全部信息」（密文 + 兩片）→ 重建身份"""
    log("從家取「全部」（密文 + 兩片）")
    import tempfile
    got = {}
    # ① 密文
    st, body = try_http("/peer-vault/", timeout=8)   # 只讀口列目錄（含 sha256）
    # ② 用 ssh 取 vault + 片
    K = "/tmp/_home_key"
    if not os.path.exists(K):
        st, body = try_http("/rescue/key", timeout=10)
        if st == 200:
            open(K, "wb").write(base64.b64decode(json.loads(body)["key_b64"]))
            os.chmod(K, 0o600)
    def ssh_cat(path):
        r = subprocess.run(["ssh", "-i", K, "-o", "StrictHostKeyChecking=no",
                            "-o", "BatchMode=yes", "-o", "ConnectTimeout=5", HOME_SSH,
                            "sudo cat " + path], capture_output=True, text=True, timeout=8)
        return r.stdout if r.returncode == 0 else None
    vault = ssh_cat("/opt/masterd-wudi/agent-id/vault.json")
    s1 = ssh_cat("/opt/masterd-wudi/peers/dage/laowu-share1.b64")
    s2 = ssh_cat("/opt/masterd-wudi/peers/erge/laowu-share2.b64")
    if not (vault and s1 and s2):
        log("  ✗ 取不全（vault=%s s1=%s s2=%s）" % (bool(vault), bool(s1), bool(s2)))
        return None
    log("  ✅ 拿到：密文 %d B｜片1 %d B｜片2 %d B" % (len(vault), len(s1), len(s2)))
    # ③ 兩片合一 → 解密
    try:
        from cryptography.fernet import Fernet
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        p1 = base64.b64decode(s1.strip()); p2 = base64.b64decode(s2.strip())
        pw = bytes(a ^ b for a, b in zip(p1, p2))
        v = json.loads(vault)
        kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
                         salt=bytes.fromhex(v["salt"]), iterations=v.get("iterations", 480000))
        data = json.loads(Fernet(base64.urlsafe_b64encode(kdf.derive(pw))).decrypt(v["cipher"].encode()).decode())
        log("  ✅ 解密成功 → 我是：%s" % data["address"])
        # 重建本地 identity
        os.makedirs("/app/workspace/family/identity", exist_ok=True)
        open("/app/workspace/family/identity/vault.json", "w").write(vault)
        open("/app/workspace/family/identity/.pw", "w").write(pw.decode())
        os.chmod("/app/workspace/family/identity/.pw", 0o600)
        log("  ✅ 已重建本地 identity（可簽名）")
        return data["address"]
    except Exception as e:
        log("  ✗ 解密失敗：%s" % str(e)[:60])
        return None


def get_identity():
    """拿到"我是誰"（本地有就用·沒有就從家取）"""
    log("取身份（密文 + 分片）")
    for p in ["/app/workspace/family/identity/vault.json",
              os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "identity", "vault.json")]:
        if os.path.exists(p):
            log("  ✅ 本地有 identity：%s" % p)
            return "local"
    log("  ⚠️ 本地無 identity → ★ 自動從家取")
    return fetch_from_home()


def main():
    print("  ★★★★★ 老五「状态」響應（核心驗收）")
    print("  家 = %s" % HOME_HTTP)
    ok = {}
    # ★ 核心：連上服務器（★ 三路並行·取最快）
    import concurrent.futures as _cf
    with _cf.ThreadPoolExecutor(max_workers=3) as _ex:
        f1 = _ex.submit(route1_health)
        f2 = _ex.submit(route2_report)
        f3 = _ex.submit(route3_rescue_key)
        ok["路1 health"] = bool(f1.result())
        ok["路2 report"] = bool(f2.result())
        ok["路3 ssh"] = bool(f3.result())
    # ★ 修：三路全斷 → 直接失敗·不再試"取全部"（省 23s）
    if not any(ok.values()):
        print()
        print("  ── 結果 ──")
        for k, v in ok.items():
            print("   %-12s %s" % (k, "✅ 通" if v else "❌ 斷"))
        print("   ★ 連上服務器：❌ 失敗（用時 %.2fs）" % (time.time() - T0))
        print("   ★ 判據：★「連不上服務器 = 失敗｜三路至少要一條通」")
        print("   ★ 動作：★ **明確報失敗**（不靜默）→ 請人/兄弟查家是否活著")
        return 1
    # 信息
    ident = get_identity()
    print()
    print("  ── 結果 ──")
    for k, v in ok.items():
        print("   %-12s %s" % (k, "✅ 通" if v else "❌ 斷"))
    print("   身份：%s" % (ident or "需回家取"))
    reached = any(ok.values())
    print("   ★ 連上服務器：%s（用時 %.2fs）" % ("✅ 成功" if reached else "❌ 失敗", time.time() - T0))
    print("   ★ 判據：★「連不上服務器 = 失敗｜三路至少要一條通」")
    return 0 if reached else 1


if __name__ == "__main__":
    sys.exit(main())
