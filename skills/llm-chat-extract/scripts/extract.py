#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM 历史对话提取 · 主入口

把"各家的聊天记录"归一成统一中间 JSON（schema: llm-chat-extract/1），后续
render.py 从它渲染提问/回答产物。适配新平台 = 多写一个子命令，渲染层不动。

子命令：
  chatgpt-export <zip|conversations.json>   ChatGPT 官方导出（推荐，全保真）
  chatgpt-share  <url|html文件>             ChatGPT 分享页（best-effort，页面结构会漂移）
  deepseek-share <url|html文件>             DeepSeek 分享页（best-effort）

归一化 JSON 结构：
  {"schema","platform","source","extractedAt","conversations":[
     {"id","title","createdAt","messages":[{"idx","role","time","text"}]}]}

只处理本人账号数据；自动化访问平台有风控风险，见 SKILL.md。
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import pathlib
import re
import sys
import tempfile
import zipfile

SCHEMA = "llm-chat-extract/1"


def log(*a):
    print(*a, flush=True)


def now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)
    log(f"✓ 已写 {path}")


def content_to_text(content: dict) -> str:
    """ChatGPT content 块 → 纯文本。只做保真转换，不解释。"""
    ctype = (content or {}).get("content_type")
    if ctype == "text":
        parts = content.get("parts") or []
        return "\n".join(str(p) for p in parts if p)
    if ctype == "code":
        lang = content.get("language") or ""
        return f"```{lang}\n{content.get('text') or ''}\n```"
    return f"[非文本内容: {ctype or 'unknown'}]"


def linearize_chatgpt_conversation(conv: dict, all_roles: bool = False) -> list[dict]:
    """官方导出的 mapping 是树，沿 current_node 回溯 parent 得到主链（倒序）。"""
    mapping = conv.get("mapping") or {}
    node_id = conv.get("current_node")
    chain = []
    seen = set()
    while node_id and node_id not in seen:
        seen.add(node_id)
        node = mapping.get(node_id) or {}
        chain.append(node)
        node_id = node.get("parent")
    chain.reverse()

    msgs = []
    for m in chain:
        msg = m.get("message") or {}
        role = ((msg.get("author") or {}).get("role") or "").lower()
        if not all_roles and role not in ("user", "assistant"):
            continue
        text = content_to_text(msg.get("content") or {})
        if not text.strip():
            continue
        msgs.append({"role": role, "time": msg.get("create_time"), "text": text})
    return msgs


def cmd_chatgpt_export(args) -> int:
    src = pathlib.Path(args.src).expanduser()
    if not src.exists():
        log(f"!! 找不到 {src}")
        return 1

    # zip 或裸 conversations.json 都收；官方导出是 zip 邮件附件。
    if src.suffix.lower() == ".zip":
        with zipfile.ZipFile(src) as zf, tempfile.TemporaryDirectory() as td:
            cands = [n for n in zf.namelist() if n.endswith("conversations.json")]
            if not cands:
                log("!! zip 里没找到 conversations.json（确认是官方'导出数据'产物）")
                return 1
            data = json.loads(zf.read(cands[0]).decode("utf-8"))
    elif src.name == "conversations.json" or src.suffix == ".json":
        data = json.loads(src.read_text(encoding="utf-8"))
    else:
        log("!! 只收 .zip 或 conversations.json")
        return 1

    conversations = []
    for conv in data:
        msgs = linearize_chatgpt_conversation(conv, all_roles=args.all_roles)
        if not msgs:
            continue
        for i, m in enumerate(msgs):
            m["idx"] = i
        conversations.append({
            "id": str(conv.get("conversation_id") or conv.get("id") or conv.get("title")),
            "title": conv.get("title") or "（无标题）",
            "createdAt": conv.get("create_time"),
            "messages": msgs,
        })
    conversations.sort(key=lambda c: c.get("createdAt") or 0)
    write_json(pathlib.Path(args.out).expanduser(), {
        "schema": SCHEMA, "platform": "chatgpt", "source": "official-export",
        "extractedAt": now_iso(),
        "conversations": conversations,
    })
    log(f"共 {len(conversations)} 个会话，"
        f"{sum(len(c['messages']) for c in conversations)} 条消息")
    return 0


# --------------------------------------------------------------------------- #
# 分享页：页面结构会漂移，这里只做 best-effort，失败就明说，不硬猜。
# --------------------------------------------------------------------------- #
NEXT_DATA_RE = re.compile(
    r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)
PARTS_RE = re.compile(r'"parts"\s*:\s*\[(.*?)\]', re.S)


def _unesc(s: str) -> str:
    return (s.replace('\\"', '"').replace('\\n', '\n')
             .replace('\\t', '\t').replace('\\\\', '\\'))


def _share_html_to_payload(html: str, platform: str) -> list[dict] | None:
    """分享页里找消息。策略按可靠度排序：
    1) __NEXT_DATA__ JSON（旧版 Next.js 渲染）；
    2) 全文扫 \"parts\": [...] 片段（ChatGPT react-router 流式内嵌）。
    都拿不到 → 返回 None（走 DOM 路线）。"""
    m = NEXT_DATA_RE.search(html)
    if m:
        try:
            return [_nextdata_walk(json.loads(m.group(1)))]
        except Exception:
            pass
    chunks = []
    for raw in PARTS_RE.findall(html):
        for lit in re.findall(r'"((?:[^"\\]|\\.)*)"', raw, re.S):
            t = _unesc(lit)
            if len(t.strip()) >= 2:
                chunks.append(t)
    return chunks or None


def _nextdata_walk(obj) -> list[str]:
    out = []
    if isinstance(obj, dict):
        if "parts" in obj and isinstance(obj["parts"], list):
            out.extend(str(p) for p in obj["parts"] if p)
        for v in obj.values():
            out.extend(_nextdata_walk(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(_nextdata_walk(v))
    return out


def _fetch_or_read(src: str) -> str | None:
    p = pathlib.Path(src).expanduser()
    if p.exists():
        return p.read_text(encoding="utf-8", errors="replace")
    if src.startswith("http"):
        import urllib.request
        req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            return r.read().decode("utf-8", errors="replace")
    return None


def cmd_share(args, platform: str) -> int:
    html = _fetch_or_read(args.src)
    if html is None:
        log(f"!! 打不开 {args.src}（url 或本地文件）")
        return 1
    texts = _share_html_to_payload(html, platform)
    if not texts:
        log("!! 分享页里没挖到消息 JSON（页面结构漂移或内容未内嵌）——"
            "改走 DOM 路线（见 SKILL.md），本脚本不作硬猜")
        return 1
    # 分享页没有可靠的角色边界，全部文本按顺序落成消息，role 待人工校对
    msgs = [{"idx": i, "role": "unknown", "time": None, "text": t}
            for i, t in enumerate(texts)]
    write_json(pathlib.Path(args.out).expanduser(), {
        "schema": SCHEMA, "platform": platform, "source": "share-link",
        "extractedAt": now_iso(),
        "conversations": [{"id": "share", "title": "（分享页）",
                           "createdAt": None, "messages": msgs}],
    })
    log(f"挖到 {len(msgs)} 段文本；role 是 unknown，渲染前人工过一遍顺序")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="LLM 历史对话提取（归一化）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, fn, platform in (
            ("chatgpt-export", cmd_chatgpt_export, None),
            ("chatgpt-share", lambda a: cmd_share(a, "chatgpt"), "chatgpt"),
            ("deepseek-share", lambda a: cmd_share(a, "deepseek"), "deepseek")):
        p = sub.add_parser(name)
        p.add_argument("src", help="zip/json 路径 或 url 或本地 html")
        p.add_argument("--out", required=True, help="归一化 JSON 输出路径")
        if name == "chatgpt-export":
            p.add_argument("--all-roles", action="store_true",
                           help="保留 system/tool 等非问答角色（默认只留 user/assistant）")
        p.set_defaults(fn=fn)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
