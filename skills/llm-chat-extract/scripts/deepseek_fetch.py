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

# 分享 ID 不是十六进制（实测 zyt6bfy9p22tuq0cm7 这种字母数字混编），按 base36 级别放宽
SHARE_ID_RE = re.compile(r"chat\.deepseek\.com/(?:a/chat/s|share)/([0-9a-zA-Z_-]{8,})")
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
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    except Exception as e:
        log(f"  · 分享 API 不通（{e.__class__.__name__}），转 DOM 路线")
        return None
    # 2026-11-13 实测：/share/ 链接的 API 返回的是 SPA 的 HTML 壳，不是 JSON——
    # 这条社区路线对 /share/ 已死，只在 /a/chat/s/ 链接上可能还有效。别对着 HTML 硬 json.loads。
    if raw.lstrip().startswith("<"):
        log("  · 分享 API 返回 HTML 壳（此格式分享页无 JSON API），转 DOM 路线")
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        log("  · 分享 API 响应不是 JSON，转 DOM 路线")
        return None
    acc = find_message_lists(data, [])
    if not acc:
        log("  · 分享 API 有响应但没解析出消息数组，转 DOM 路线")
        return None
    best = max(acc, key=len)
    log(f"  ✓ 分享 API 拿到 {len(best)} 条消息")
    return best


# 消息块结构（2026-11-13 真页实测）：
#   统一容器 .ds-message；assistant 内有 .ds-markdown.ds-assistant-message-main-content
#   （思考内容在同容器的 .ds-think-content 里，不算正文）；user 消息没有 ds-markdown。
#   外层是虚拟列表（ds-virtual-list-visible-items），长对话只渲染可见区 → 由
#   Python 侧滚动+重叠合并采全量，这里只负责抽"当前渲染出来的"消息。
DOM_EXTRACT_JS = r"""
() => {
  const UI_NOISE = new Set(['该对话来自分享，由 AI 生成，请仔细甄别。']);
  return [...document.querySelectorAll('.ds-message')].map(el => {
    const main = el.querySelector('.ds-markdown.ds-assistant-message-main-content')
              || el.querySelector('.ds-markdown');
    const text = ((main || el).innerText || '').trim();
    return {role: main ? 'assistant' : 'user', text};
  }).filter(m => m.text && !UI_NOISE.has(m.text));
}
"""

SCROLL_STEP_JS = r"""
(step) => {
  const el = document.querySelector('.ds-message');
  let p = el ? el.parentElement : null;
  while (p) {
    const st = getComputedStyle(p);
    if (/(auto|scroll)/.test(st.overflowY) && p.scrollHeight > p.clientHeight + 5) {
      const before = p.scrollTop;
      p.scrollTop = Math.min(before + step, p.scrollHeight);
      return {advanced: p.scrollTop > before,
              atBottom: p.scrollTop + p.clientHeight >= p.scrollHeight - 5};
    }
    p = p.parentElement;
  }
  window.scrollBy(0, step);
  return {advanced: true,
          atBottom: window.innerHeight + window.scrollY >= document.body.scrollHeight - 5};
}
"""


def try_dom(url: str, headed: bool) -> list[dict] | None:
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
            # 用用户贴来的原始 URL，绝不改写路径——/share/<id> 改写成 /a/chat/s/<id>
            # 是空页（2026-11-13 实测，第一版就是栽在这）
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            try:
                page.wait_for_selector(".ds-message", timeout=20000)
            except Exception:
                log("  · 页面 20s 内没渲染出消息块（可能要登录或链接失效）")
                return None
            page.wait_for_timeout(2000)   # 首屏正文异步注入

            # 虚拟列表：滚动到底，逐屏快照，按"已采集尾部 = 快照头部"的最大重叠合并。
            # 去重不能按内容全局去——两条一模一样的"好的"是合法对话，重叠对齐才不误杀。
            collected = [tuple(m.values()) for m in page.evaluate(DOM_EXTRACT_JS)]
            stuck = 0
            for _ in range(80):   # 80 屏封顶，防失控
                nav = page.evaluate(SCROLL_STEP_JS, 800)
                page.wait_for_timeout(700)
                snap = [tuple(m.values()) for m in page.evaluate(DOM_EXTRACT_JS)]
                best = 0
                for k in range(min(len(collected), len(snap), 60), 0, -1):
                    if collected[-k:] == snap[:k]:
                        best = k
                        break
                collected.extend(snap[best:])
                if not nav["advanced"] or (nav["atBottom"] and best == len(snap)):
                    stuck += 1
                    if stuck >= 2:
                        break
                else:
                    stuck = 0
        finally:
            browser.close()
    out = [{"role": r, "text": t} for r, t in collected if t]
    if not out:
        log("  · DOM 渲染后没抽到消息块")
        return None
    n_user = sum(1 for m in out if m["role"] == "user")
    log(f"  ✓ DOM 抽到 {len(out)} 条（user {n_user} / assistant {len(out) - n_user}）")
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

    # DOM 为主（2026-11-13 实测 /share/ 链接没有 JSON API，页面能渲染全量），
    # API 是 /a/chat/s/ 格式的兜底。
    msgs = try_dom(args.url, args.headed)
    source = "share-dom"
    if not msgs:
        msgs = try_api(sid)
        source = "share-api"
    if not msgs:
        log("!! 提取失败：DOM 和分享 API 都没拿到内容（链接失效或页面改版）")
        return 1

    write_out(pathlib.Path(args.out).expanduser(), norm(msgs, sid, source))
    log(f"✓ 已写 {args.out}（source={source}，{len(msgs)} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
