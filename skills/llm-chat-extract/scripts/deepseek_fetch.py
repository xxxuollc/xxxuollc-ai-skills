#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek 分享链接 → 归一化 JSON（app.py 的后端执行器）

路线（可靠性递减，前一条失败自动试下一条）：
  1. 公开分享 API（无需登录）：GET /api/v0/chat/shared_get?share_id=<id>
     —— 社区已知路线，字段/可用性未长期验证，解析全部容错；
  2. Playwright 无头渲染分享页后按 DOM 顺序抽文本块
     —— 选择器启发式（.ds-markdown = 助手侧），role 判不准落 unknown；
  3. 都失败 → 如实报失败，不硬猜。

用法：deepseek_fetch.py <分享链接> --out normalized.json [--headed]
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys
import urllib.request

SHARE_ID_RE = re.compile(r"chat\.deepseek\.com/(?:a/chat/s|share)/([0-9a-fA-F-]{8,})")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
API_URL = "https://chat.deepseek.com/api/v0/chat/shared_get?share_id={sid}"


def log(*a):
    print(*a, flush=True)


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def write_out(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(path)


def find_message_lists(obj, acc):
    """容错地在任意 JSON 里找"像消息数组"的东西：dict 带 role/sender + content/text。"""
    if isinstance(obj, list):
        cand = [d for d in obj if isinstance(d, dict)
                and (("role" in d) or ("sender" in d) or ("is_user" in d))
                and any(isinstance(d.get(k), str) and d[k].strip()
                        for k in ("content", "text", "message_text"))]
        if cand:
            acc.append(cand)
        for d in obj:
            if isinstance(d, dict):
                find_message_lists(d, acc)
    elif isinstance(obj, dict):
        for v in obj.values():
            find_message_lists(v, acc)
    return acc


def role_of(d: dict) -> str:
    r = str(d.get("role") or d.get("sender") or "").lower()
    if "user" in r or d.get("is_user") is True:
        return "user"
    if "assist" in r or "bot" in r or "ai" in r:
        return "assistant"
    return "unknown"


def norm(messages: list[dict], share_id: str, source: str) -> dict:
    out = []
    for i, m in enumerate(messages):
        text = next(m[k] for k in ("content", "text", "message_text")
                    if isinstance(m.get(k), str) and m[k].strip())
        t = m.get("create_time") or m.get("created_at")
        out.append({"idx": i, "role": role_of(m),
                    "time": float(t) if isinstance(t, (int, float)) else None,
                    "text": text.strip()})
    return {"schema": "llm-chat-extract/1", "platform": "deepseek", "source": source,
            "extractedAt": now_iso(),
            "conversations": [{"id": share_id, "title": "（分享页）",
                               "createdAt": None, "messages": out}]}


def try_api(sid: str) -> list[dict] | None:
    try:
        req = urllib.request.Request(API_URL.format(sid=sid), headers={
            "User-Agent": UA, "Accept": "application/json",
            "Referer": f"https://chat.deepseek.com/a/chat/s/{sid}"})
        data = json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    except Exception as e:
        log(f"  · 分享 API 不通（{e.__class__.__name__}），转 DOM 路线")
        return None
    acc = find_message_lists(data, [])
    if not acc:
        log("  · 分享 API 有响应但没解析出消息数组，转 DOM 路线")
        return None
    best = max(acc, key=len)
    log(f"  ✓ 分享 API 拿到 {len(best)} 条消息")
    return best


DOM_EXTRACT_JS = r"""
() => {
  const blocks = [];
  document.querySelectorAll('.ds-markdown, [class*="Markdown"], [class*="message-item"], [class*="message"]').forEach(el => {
    const t = (el.innerText || '').trim();
    if (!t || t.length < 1) return;
    const cls = el.className || '';
    const isMd = /ds-markdown|Markdown/.test(cls);
    const isUser = /user|User/.test(cls);
    blocks.push({role: isMd ? 'assistant' : (isUser ? 'user' : 'unknown'), text: t});
  });
  return blocks;
}
"""


def try_dom(sid: str, headed: bool) -> list[dict] | None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log("  · 本 python 没装 playwright，DOM 路线不可用")
        return None
    args = ["--disable-blink-features=AutomationControlled"]
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome", headless=not headed, args=args)
        ctx = browser.new_context(locale="zh-CN", timezone_id="Asia/Shanghai",
                                  viewport={"width": 1440, "height": 940}, user_agent=UA)
        ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        page = ctx.new_page()
        try:
            page.goto(f"https://chat.deepseek.com/a/chat/s/{sid}",
                      wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(10000)
            blocks = page.evaluate(DOM_EXTRACT_JS)
        finally:
            browser.close()
    # 就近去重（父子容器会重复命中同一段文本）
    out, last = [], None
    for b in blocks:
        if b["text"] != last:
            out.append(b)
            last = b["text"]
    if not out:
        log("  · DOM 渲染后没抽到文本块")
        return None
    log(f"  ✓ DOM 抽到 {len(out)} 块文本（role 有 unknown 属预期，渲染时带人工核对警示）")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="DeepSeek 分享链接")
    ap.add_argument("--out", required=True)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    m = SHARE_ID_RE.search(args.url)
    if not m:
        log(f"!! 不像 DeepSeek 分享链接：{args.url}")
        return 1
    sid = m.group(1)

    msgs = try_api(sid)
    source = "share-api"
    if not msgs:
        msgs = try_dom(sid, args.headed)
        source = "share-dom"
    if not msgs:
        log("!! 提取失败：分享 API 和 DOM 路线都没拿到内容（链接失效或页面改版）")
        return 1

    write_out(pathlib.Path(args.out).expanduser(), norm(msgs, sid, source))
    log(f"✓ 已写 {args.out}（source={source}，{len(msgs)} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
