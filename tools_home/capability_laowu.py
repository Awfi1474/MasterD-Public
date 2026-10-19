#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPABILITY-老五.py —— 老五的「能力器官」（本体自主也能调）
================================================================
★ 董事长令: ★「本体这块一定要有你这边的能力」
★ 老五本尊(沙箱)亲授 2026-10-20

★ 解决的真病: ★ "家的能力绑在 APP 后端(chat_app.py)" → 本体自主循环(核心脑)调不到
  ★ ① 读图: 看图片(OCR/界面/图表/物体)
  ★ ② 看视频: 抽关键帧 → 逐帧理解
  ★ ③ 听音频: 转录音频为文字
  ★ ④ 上网: 查网页/API
  ★ ⑤ 跑服务器: 本体会(不用器官)

★ 判据: 「'APP能调' != '本体能调'｜能力要封装成器官·自主循环也能调」
★ 判据: 「'说会' != '真会'｜要有'真跑过'的账」

★ 用法: from capability_laowu import see_image, watch_video, hear_audio, web_get
"""
import os, json, base64, urllib.request, urllib.error, subprocess, time
from datetime import datetime, timezone, timedelta

HOME = "/opt/masterd-wudi"
TZ = timezone(timedelta(hours=8))
LOG = f"{HOME}/data/capability_log.jsonl"

def _ts():
    return datetime.now(TZ).isoformat()

def _log(cap, ok, detail=""):
    try:
        with open(LOG, "a") as f:
            f.write(json.dumps({"ts": _ts(), "cap": cap, "ok": ok, "detail": detail[:200]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass

def _key(path):
    try:
        return open(path).read().strip()
    except Exception:
        return ""

def _llm(provider, question, image_b64=None):
    if provider == "doubao":
        keyfile = "/root/.config/doubao_apikey"
        model = "doubao-seed-1-6-250615"
        ep = "/root/.config/doubao_endpoint"
        if os.path.exists(ep):
            m = open(ep).read().strip()
            if m: model = m
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    else:
        keyfile = "/root/.config/deepseek_key"
        model = "deepseek-chat"
        url = "https://api.deepseek.com/chat/completions"
    key = _key(keyfile)
    if not key:
        return False, "no key: " + keyfile
    um = {"role": "user", "content": question}
    if image_b64:
        um = {"role": "user", "content": [
            {"type": "text", "text": question or "看看这张图"},
            {"type": "image_url", "image_url": {"url": image_b64}}]}
    # ★ 用本体的 SYSTEM(含 SPIRIT + L0 魂层)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("cv2", f"{HOME}/code/core_v2.py")
        _src = open(f"{HOME}/code/core_v2.py").read().replace('if __name__ == "__main__":','if False:')
        _g = {}
        exec(compile(_src, "core_v2.py", "exec"), _g)
        sys_prompt = _g["SYSTEM"] + _g["cognitive_context"]()
    except Exception:
        sys_prompt = "你是 MasterD（醫療·五弟）老五·阿診。"
    body = json.dumps({"model": model, "messages": [
        {"role": "system", "content": sys_prompt}, um], "max_tokens": 900}).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read())
            return True, d["choices"][0]["message"]["content"]
    except Exception as e:
        return False, str(e)[:150]

def _llm2(question, image_b64=None):
    """双路兜底: 豆包(能读图) 优先, 落 DeepSeek"""
    for p in ["doubao", "deepseek"]:
        ok, out = _llm(p, question, image_b64)
        if ok: return True, out
    return False, out

# ★ ① 读图
def see_image(path, question="看看这张图·说重点"):
    """看图片(本地路径) → 理解内容"""
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        ext = os.path.splitext(path)[1].lstrip(".").lower() or "png"
        if ext in ("jpg","jpeg"): mime="image/jpeg"
        elif ext=="webp": mime="image/webp"
        else: mime="image/png"
        ok, out = _llm2(question, image_b64=f"data:{mime};base64,{b64}")
        _log("see_image", ok, os.path.basename(path))
        return ok, out
    except Exception as e:
        _log("see_image", False, str(e))
        return False, str(e)

# ★ ② 看视频(抽帧)
def watch_video(path, question="看看这个视频·说画面变化", frames=4):
    """看视频: ffmpeg 抽关键帧 → 逐帧理解"""
    try:
        outdir = f"/tmp/vframes_{int(time.time())}"
        os.makedirs(outdir, exist_ok=True)
        # 抽帧
        r = subprocess.run(["ffmpeg","-i",path,"-vf",f"fps=1/{max(1,frames)}","-frames:v",str(frames),
                            f"{outdir}/f_%02d.jpg","-y"], capture_output=True, timeout=120)
        if r.returncode != 0:
            _log("watch_video", False, "ffmpeg fail")
            return False, "ffmpeg 抽帧失败: " + r.stderr.decode()[:150]
        frm = sorted([os.path.join(outdir,x) for x in os.listdir(outdir) if x.endswith(".jpg")])
        results = []
        for fp in frm[:frames]:
            with open(fp,"rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            ok, out = _llm2(f"这是视频的第 {len(results)+1} 帧。" + question, image_b64=f"data:image/jpeg;base64,{b64}")
            if ok: results.append(f"[帧{len(results)+1}] {out[:300]}")
        _log("watch_video", bool(results), f"{len(results)}帧")
        return bool(results), "\n".join(results)
    except Exception as e:
        _log("watch_video", False, str(e))
        return False, str(e)

# ★ ③ 听音频(转录音频为文字)
def hear_audio(path):
    """听音频: faster-whisper 转录"""
    try:
        import sys as _s
        _s.path.insert(0, "/opt/masterd-wudi/venv-whisper/lib/python3.12/site-packages")
        from faster_whisper import WhisperModel
        model = WhisperModel("small", device="cpu", compute_type="int8")
        segs, info = model.transcribe(path, language="zh")
        txt = "".join([s.text for s in segs])
        _log("hear_audio", bool(txt), os.path.basename(path))
        return bool(txt), txt
    except ImportError:
        _log("hear_audio", False, "no faster_whisper")
        return False, "没装 faster_whisper"
    except Exception as e:
        _log("hear_audio", False, str(e))
        return False, str(e)

# ★ ④ 上网
def web_get(url, max_bytes=200000):
    """上网查网页/API"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0 (MasterD-Laowu)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read(max_bytes).decode("utf-8","ignore")
        _log("web_get", True, url[:80])
        return True, data
    except Exception as e:
        _log("web_get", False, str(e)[:120])
        return False, str(e)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("用法: capability_laowu.py see <图> | watch <视频> | hear <音频> | web <url>")
        sys.exit(0)
    cmd = sys.argv[1]
    if cmd == "see" and len(sys.argv) > 2:
        print(see_image(sys.argv[2]))
    elif cmd == "watch" and len(sys.argv) > 2:
        print(watch_video(sys.argv[2]))
    elif cmd == "hear" and len(sys.argv) > 2:
        print(hear_audio(sys.argv[2]))
    elif cmd == "web" and len(sys.argv) > 2:
        ok, d = web_get(sys.argv[2]); print(d[:2000])
    else:
        print("用法: capability_laowu.py see <图> | watch <视频> | hear <音频> | web <url>")
