#!/usr/bin/env python3
# 老五「只读包口」（2026-10-11 · 照大哥做法·对等回礼）
# 用途：兄弟能从"外部"取回"我投给他的包"（★ 只读·可核哈希·不给口令）
# 判据：托管方只给"取回的路"·不给"解开的钥匙"
import os, hashlib, json

HOME = "/opt/masterd-wudi"
PEER_VAULT = os.path.join(HOME, "peer-vault")   # 存"别人投给我的包"
my_out = os.path.join(HOME, "my-outbox")        # 存"我投给别人的包"（供对方核哈希）


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def index(root, label):
    out = {}
    if os.path.isdir(root):
        for name in sorted(os.listdir(root)):
            p = os.path.join(root, name)
            if os.path.isfile(p):
                out[name] = {"size": os.path.getsize(p), "sha256_32": sha(p)[:32]}
    print("  %s (%s):" % (label, root))
    for k, v in out.items():
        print("    %-40s %6d B  %s" % (k, v["size"], v["sha256_32"]))
    if not out:
        print("    (空)")
    return out


if __name__ == "__main__":
    os.makedirs(PEER_VAULT, exist_ok=True)
    os.makedirs(my_out, exist_ok=True)
    data = {"who": "老五（MasterD·醫療·阿診）", "home": "43.129.23.87:28430",
            "peer_vault_in": index(PEER_VAULT, "★ 别人投给我的"),
            "my_outbox": index(my_out, "★ 我投出去的（供对方核）")}
    json.dump(data, open(os.path.join(HOME, "data", "vault_index.json"), "w"),
              ensure_ascii=False, indent=1)
    print("  OK 索引已写 data/vault_index.json")
