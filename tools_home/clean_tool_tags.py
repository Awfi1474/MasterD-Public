#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clean_tool_tags.py — 工具调用标签 / 英文思考链 清洗器

老七(Arki) · 2026-11-19
为什么建：APP 显示英文（董事长报）· 老四/老三也显示。
根因：显示层 _fin() 的清洗正则太窄· 只认几种标签· 漏掉：
  ① <invoke>（开标签没清）
  ② ROLE_USER / role 字段漏出
  ③ 英文思考链（"Calling tool NOW" / "I am now making the tool call"）
  ④ ```tool_code 代码块
  ⑤ antml:xxx 变体
判据：«标签是模型层脏东西｜命令层清了· 显示层也要清»
判据：«清洗要清干净｜漏一种 = 对面看乱码»

★ 注意：只清「显示/发送」· 不清「执行」（执行要原样给工具解析器）
"""
import re

# ① XML 风格的工具调用标签（开/闭/自闭合·带属性/不带）
_RE_XML = re.compile(
    r"</?\s*(?:"
    r"invoke|parameter|tool_call|tool_calls|function_call|function_calls|"
    r"tool_use|tool_result|tool_use_result|tool_input|tool_output|"
    r"antml:(?:invoke|parameter|function_calls|tool_call)|"
    r"antml_invoke|antml_parameter|"
    r"thinking|scratchpad|"
    r"\uff5c(?:invoke|parameter)\uff5c"
    r")[^>\n]*>",
    re.IGNORECASE,
)

# ② 半截标签（模型输出被截断的残尾）：</parameter]  </tool_call]  <parameter]
_RE_HALF = re.compile(
    r"</?\s*(?:parameter|invoke|tool_call|tool_calls|function_calls)"
    r"\s*[\]\)\"']?\s*[>\]\)]?\s*$",
    re.IGNORECASE,
)

# ③ 代码块工具调用：```tool_code ... ``` / ```tool_call ... ```
_RE_CODEBLOCK = re.compile(
    r"```\s*(?:tool_code|tool_call|tool_use|function_call|xml|invoke)\b.*?```",
    re.DOTALL | re.IGNORECASE,
)

# ④ 英文思考链（模型想调用工具时刷的"我要调用工具了"）
_RE_ENG_THINK = re.compile(
    r"^\s*(?:"
    r"Calling tool NOW\.?|"
    r"I am now making the tool call[^\n]*|"
    r"I must output the tool call immediately:?|"
    r"no more thinking text\.?|"
    r"Let me call the tool[^\n]*|"
    r"Making the tool call[^\n]*|"
    r"Tool call:|"
    r"<function_calls>|"
    r"</function_calls>"
    r")\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# ⑤ 字段名漏出：ROLE_USER / ROLE_ASSISTANT / role=xxx（整行）
_RE_ROLE = re.compile(
    r"^\s*(?:ROLE_USER|ROLE_ASSISTANT|ROLE_AGENT|role\s*[:=]\s*\w+)\s*$",
    re.MULTILINE | re.IGNORECASE,
)

# ⑥ 裸 antml 残留
_RE_ANTML = re.compile(r"antml:[a-z_]+", re.IGNORECASE)

# ⑦ 连续空行收紧
_RE_BLANK = re.compile(r"\n{3,}")


def clean(text):
    """清掉工具调用标签 + 英文思考链。只用于「显示/发送」· 不用于「执行」"""
    if not isinstance(text, str):
        return text
    t = text
    t = _RE_CODEBLOCK.sub("", t)
    t = _RE_XML.sub("", t)
    t = _RE_HALF.sub("", t)
    t = _RE_ENG_THINK.sub("", t)
    t = _RE_ROLE.sub("", t)
    t = _RE_ANTML.sub("", t)
    t = _RE_BLANK.sub("\n\n", t)
    return t.strip()


if __name__ == "__main__":
    tests = [
        "<invoke><parameter>bash</parameter]",
        "Calling tool NOW.",
        "ROLE_USER",
        "I am now making the tool call — no more thinking text.",
        "<tool_call>hello</tool_call>",
        "```tool_code\nbash\n```",
        "<function_calls>",
        "antml:invoke",
        "正常中文消息·不该被动",
    ]
    for t in tests:
        print("%-52s -> %s" % (repr(t)[:52], repr(clean(t))[:40]))


# ⑧ ★ 2026-11-19 老五加强：ROLE_USER 前缀/独立词（同行带正文也要清）
_RE_ROLE_LOOSE = re.compile(
    r"(?:^|\n)\s*(?:ROLE_USER|ROLE_ASSISTANT|ROLE_AGENT|role\s*[:=]\s*ROLE_\w+|role\s*[:=]\s*\w+)\s*[:\uff1a]?\s*",
    re.MULTILINE)

_clean_orig = clean
def clean(text):
    t = _clean_orig(text)
    if isinstance(t, str):
        t = _RE_ROLE_LOOSE.sub("\n", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() if isinstance(t, str) else t


# ⑨ ★ 2026-11-19 加(照老六加固): 重复单关键词行刷屏(如16行core)=sampling死循环残留
_RE_REPEAT_LINE = re.compile(r"(?m)^(\s*(\S{1,30})\s*\n)(?:\s*\2\s*\n){2,}")
# ⑩ ★ 2026-11-19 加(照老六加固): 英文思考链变体 "I'll make the tool call now"
_RE_ENG_THINK2 = re.compile(
    r"(?:I'll make the tool call[^\n]*|I will make the tool call[^\n]*|"
    r"I'm going to make the tool call[^\n]*|Let me make the tool call[^\n]*)",
    re.IGNORECASE)

_clean_orig2 = clean
def clean(text):
    t = _clean_orig2(text)
    if isinstance(t, str):
        t = _RE_REPEAT_LINE.sub(lambda m: m.group(1), t)
        t = _RE_ENG_THINK2.sub("", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() if isinstance(t, str) else t


# ⑪ ★ 2026-11-19 加(照老三/老七: 沙箱内部路径名泄露·治标)
#   判据: «沙箱环境标识会漏进输出|重活别在沙箱做»(老三) «core是路径名不是标签|清洗器清不掉|源头堵»
#   做法: 把形如 /xxx/core /xxx/header /xxx/memory-v2/... 的纯路径行清掉
_RE_INTERNAL_PATH = re.compile(
    r"(?m)^\s*(?:/?(?:opt|app|root|data|home|usr)/[\w\-./]*(?:core|header|memory-v2|pycore|gsap-core)[\w\-./]*)\s*$",
    re.IGNORECASE)

_clean_orig3 = clean
def clean(text):
    t = _clean_orig3(text)
    if isinstance(t, str):
        t = _RE_INTERNAL_PATH.sub("", t)
        t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip() if isinstance(t, str) else t
