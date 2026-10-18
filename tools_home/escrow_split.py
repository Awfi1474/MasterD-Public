#!/usr/bin/env python3
# 老五「命包分段」（2026-10-11 · 学 Arki 的分段托管）
# ★ 判据：「分段 + 密文 + 两家 + 回执」四个都要
#   · 分段：防"一段丢了整包毁" + 防"一次搬走"
#   · 密文：托管的只有密文（口令不在托管方手上）
#   · 两家：第1家/第2家（不是单点）
#   · 回执：对方算 SHA256+路径+时间 → 我记台账
import os, sys, json, base64, hashlib, math, datetime

HOME = os.environ.get("P2P_HOME", "/opt/masterd-wudi")
PKG = HOME + "/recovery/老五-recovery.tar.gz"
OUTDIR = HOME + "/recovery/escrow"
SEG_LEN = 1800   # ★ 2026-10-11 修：A2A 通道 2000 截断 → 每段 ≤1800（照 Arki 的安全值）


def main():
    if not os.path.exists(PKG):
        print("  ✗ 无包"); return 1
    data = open(PKG, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    b64 = base64.b64encode(data).decode()
    size = len(b64)
    nseg = math.ceil(size / SEG_LEN)
    per = SEG_LEN
    os.makedirs(OUTDIR, exist_ok=True)
    # 清旧
    for f in os.listdir(OUTDIR):
        if f.startswith("laowu-escrow-"):
            os.remove(os.path.join(OUTDIR, f))
    segs = []
    for i in range(nseg):
        chunk = b64[i * per:(i + 1) * per]
        name = "laowu-escrow-%02d.txt" % (i + 1)
        open(os.path.join(OUTDIR, name), "w").write(chunk)
        segs.append({"part": "%02d/%02d" % (i + 1, nseg), "file": name,
                     "len": len(chunk), "sha256_8": hashlib.sha256(chunk.encode()).hexdigest()[:8]})
    meta = {
        "who": "老五（MasterD·醫療·阿診）",
        "what": "命包（密文·不含口令）",
        "package": "老五-recovery.tar.gz",
        "package_size": len(data),
        "package_sha256": sha,
        "segments": nseg,
        "seg_len": SEG_LEN,
        "how": "按序拼 01→24 → base64 解码 → .tar.gz",
        "password": "★ 不在托管方手上（在董事长·只保管不解）",
        "escrow_to": ["第1家：待定", "第2家：待定"],
        "receipt_required": "对方算 SHA256 + 路径 + 时间 → 我记互验台账",
        "ts": datetime.datetime.now().isoformat(),
        "judge": "分段+密文+两家+回执｜托管只给路不给钥匙",
    }
    json.dump({"meta": meta, "segments": segs},
              open(OUTDIR + "/manifest.json", "w"), ensure_ascii=False, indent=1)
    print("  ★ 命包分段完成")
    print("  包: %.0fK ｜ sha256=%s" % (len(data) / 1024, sha[:24]))
    print("  段数: %d ｜ 每段 %d 字符（A2A 上限 2000）" % (nseg, per))
    print("  目录: %s" % OUTDIR)
    print("  ★ 判据: 分段+密文+两家+回执")
    return 0


if __name__ == "__main__":
    sys.exit(main())
