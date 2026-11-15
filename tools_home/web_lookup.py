#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""老五·上网 web_lookup.py —— 第3层: 拉官方原文(零模型·只拉不判)
★ 董事长令: 让它上网查官方资料·省钱
★ 判据: 「拉回来的原文贴出来看｜不许模型自己编｜网上的内容不可直接信」
★ 三道防: ① 只许 https ② 有大小上限 ③ 内容标记为"外来·待核实"
"""
import os, sys, json, re, hashlib, datetime, urllib.request, urllib.parse

HOME = "/opt/masterd-wudi"
CACHE = HOME + "/data/web_cache.jsonl"
LOG = HOME + "/data/web_lookup.jsonl"
MAX_BYTES = 400_000
UA = "Mozilla/5.0 (compatible; MasterD-lao5/1.0)"

# ★ 可信源白名单(官方文档优先·省得模型瞎猜)
OFFICIAL = {
    "ethereum": ["https://ethereum.org", "https://eips.ethereum.org"],
    "bsc": ["https://docs.bnbchain.org", "https://bscscan.com"],
    "pancake": ["https://docs.pancakeswap.finance"],
    "python": ["https://docs.python.org/3"],
    "volc": ["https://www.volcengine.com/docs"],
    "deepseek": ["https://api-docs.deepseek.com"],
}

def ts():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(timespec="seconds")

def _html2text(html):
    html = re.sub(r"(?is)<script.*?</script>", " ", html)
    html = re.sub(r"(?is)<style.*?</style>", " ", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    html = re.sub(r"&nbsp;", " ", html)
    html = re.sub(r"&amp;", "&", html)
    html = re.sub(r"&lt;", "<", html)
    html = re.sub(r"&gt;", ">", html)
    html = re.sub(r"\s{2,}", " ", html)
    return html.strip()

def fetch(url, timeout=15):
    """拉一页·返回 (ok, title, text, bytes, err)"""
    if not url.startswith("https://"):
        return False, "", "", 0, "只许 https(防降级)"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(MAX_BYTES)
        txt = raw.decode("utf-8", "ignore")
        m = re.search(r"(?is)<title>(.*?)</title>", txt)
        title = _html2text(m.group(1)) if m else ""
        body = _html2text(txt)
        return True, title[:200], body[:12000], len(raw), ""
    except Exception as e:
        return False, "", "", 0, str(e)[:120]

def lookup(url, save=True):
    """拉取并在账里留下: 输入(url) / 算子(抓取+去标签) / 结果(字节+标题+摘要哈希)"""
    ok, title, text, nbytes, err = fetch(url)
    rec = {"ts": ts(), "url": url, "ok": ok,
           "输入": url,
           "算子": "GET https + 去script/style/标签 + 截12000字",
           "结果": {"字节": nbytes, "标题": title,
                    "正文长度": len(text),
                    "正文哈希": hashlib.sha1(text.encode()).hexdigest()[:12] if text else "",
                    "摘要": text[:600]},
           "err": err,
           "trust": "外来内容·必须核实后才可当依据"}
    if save:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        if ok and text:
            with open(CACHE, "a", encoding="utf-8") as f:
                f.write(json.dumps({"ts": ts(), "url": url, "title": title,
                                    "text": text[:8000]}, ensure_ascii=False) + "\n")
    return rec

def search_hint(q):
    """给模型一个"去哪找"的提示·不代替它判断"""
    hits = []
    for k, urls in OFFICIAL.items():
        if k.lower() in q.lower():
            hits.extend(urls)
    return {"query": q, "official_candidates": hits[:5],
            "note": "先拉官方候选·拉不到再考虑通用搜索(需模型判断·花钱)"}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)
    if args[0] == "--official":
        print(json.dumps(search_hint(" ".join(args[1:])), ensure_ascii=False, indent=1))
    else:
        url = args[0]
        r = lookup(url)
        print("ok:", r["ok"], "| 字节:", r["结果"]["字节"], "| 标题:", r["结果"]["标题"][:60])
        if r["ok"]:
            print("--- 正文前 800 字 ---")
            print(r["结果"]["摘要"][:800])
        else:
            print("err:", r["err"])