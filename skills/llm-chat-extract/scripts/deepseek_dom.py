#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""DeepSeek 网页端对话提取（DOM/fiber 路线）——**未实测，首跑必须人工校验**

DeepSeek 没有官方导出；分享页内容不保证内嵌 JSON。此脚本走浏览器提取，
协议沿用 douyin-dm-export 的实测教训（虚拟列表、fiber 取数、勿啃 protobuf）。

登录态：~/.workbuddy/secrets/deepseek.state.json（600；--login 扫码生成）。
产物：归一化 JSON（schema llm-chat-extract/1），喂给 render.py。

首跑自检（不做完不要信结果）：
  1. 抽一条会话对照网页原文：条数一致、无插错位；
  2. role 判定抽查 5 条（fiber 的 role 字段 vs 页面上谁说的话）；
  3. 长会话滚到底再采，若"搜得到页面上有、结果里没有"的词 → 步长漏采。
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import sys

STATE = pathlib.Path.home() / ".workbuddy/secrets/deepseek.state.json"
BASE = "https://chat.deepseek.com/"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36")
ARGS = ["--disable-blink-features=AutomationControlled",
        "--no-first-run", "--no-default-browser-check"]


def log(*a):
    print(*a, flush=True)


def now_iso():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


# fiber 扫描：DeepSeek 前端是 React，消息数据（role/文本/时间戳）挂在
# fiber 节点的 memoizedProps 上。从"消息容器"向上爬 fiber 链找带 role 的对象。
# —— 选择器是启发式，首跑按脚本头部的自检清单人工校验。
FIBER_EXTRACT_JS = r"""
() => {
  const out = [];
  const seen = new Set();
  const climb = (el) => {
    let f = el;
    for (let i = 0; i < 25 && f; i++) {
      const p = f.memoizedProps;
      if (p && typeof p === 'object') {
        for (const k of ['message', 'msg', 'chatMessage', 'data']) {
          const m = p[k];
          if (m && typeof m === 'object' && !seen.has(m)) {
            seen.add(m);
            const role = m.role || m.sender || (m.is_user !== undefined ? (m.is_user ? 'user' : 'assistant') : undefined);
            const text = m.content || m.text || m.message_text;
            if (typeof text === 'string' && text.trim() && role) {
              out.push({role: String(role), text, time: m.create_time || m.created_at || null});
            }
          }
        }
      }
      f = f.return;
    }
  };
  // 候选容器：assistant 的 markdown 块 + 任何带 message 相关 class 的行
  const cands = document.querySelectorAll('[class*="ds-markdown"], [class*="message"], [class*="Message"]');
  cands.forEach(climb);
  return out;
}
"""


def new_context(pw, headless, with_state=True):
    browser = pw.chromium.launch(channel="chrome", headless=headless, args=ARGS)
    kw = dict(locale="zh-CN", timezone_id="Asia/Shanghai",
              viewport={"width": 1440, "height": 940}, user_agent=UA)
    if with_state and STATE.exists():
        kw["storage_state"] = str(STATE)
    ctx = browser.new_context(**kw)
    ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
    return browser, ctx


def is_logged_in(ctx) -> bool:
    # DeepSeek 登录态 cookie 名含 dsuser-token / token（宽松判定，宁滥勿缺）
    try:
        names = {c.get("name", "") for c in ctx.cookies()}
    except Exception:
        return False
    return any("token" in n.lower() or "session" in n.lower() for n in names)


def cmd_login(args) -> int:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser, ctx = new_context(pw, headless=False, with_state=False)
        ctx.new_page().goto(BASE, wait_until="domcontentloaded")
        log(">>> 请在 Chrome 窗口里登录 DeepSeek（手机验证码/微信）")
        deadline = args.timeout
        import time
        while time.time() < deadline:
            if is_logged_in(ctx):
                break
            time.sleep(2)
        else:
            log("!! 超时未检测到登录态")
            browser.close()
            return 1
        import time as t
        t.sleep(3)
        ctx.storage_state(path=str(STATE))
        STATE.chmod(0o600)
        log(f"✓ 登录态已保存：{STATE}")
        browser.close()
    return 0


def cmd_pull(args) -> int:
    from playwright.sync_api import sync_playwright
    if not STATE.exists():
        log(f"!! NEED_LOGIN: 先跑 {pathlib.Path(__file__).name} login")
        return 1
    with sync_playwright() as pw:
        browser, ctx = new_context(pw, headless=not args.headed)
        try:
            if not is_logged_in(ctx):
                log("!! NEED_LOGIN: 登录态已失效，重新 --login")
                return 1
            page = ctx.new_page()
            page.goto(BASE, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(8000)
            if args.conv:
                # 侧栏找目标会话并点进去（找不到就报错，不硬猜）
                hit = page.locator(f'text="{args.conv}"').first
                if hit.count() == 0:
                    log(f"!! 侧栏没找到含「{args.conv}」的会话")
                    return 1
                hit.click()
                page.wait_for_timeout(5000)
            raw = page.evaluate(FIBER_EXTRACT_JS)
        finally:
            browser.close()

    # 就近去重（连续相同 text+role 视为 fiber 多次命中）
    msgs, last = [], None
    for r in raw:
        key = (r["role"], r["text"])
        if key != last:
            msgs.append({"role": r["role"], "time": r["time"], "text": r["text"]})
            last = key
    for i, m in enumerate(msgs):
        m["idx"] = i
    out = pathlib.Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "schema": "llm-chat-extract/1", "platform": "deepseek", "source": "dom",
        "extractedAt": now_iso(),
        "conversations": [{"id": args.conv or "current", "title": args.conv or "（当前会话）",
                           "createdAt": None, "messages": msgs}],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    out.chmod(0o600)
    log(f"✓ 已写 {out}，{len(msgs)} 条消息（首跑请按自检清单人工校验）")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="DeepSeek 对话提取（DOM，未实测见头部说明）")
    sub = ap.add_subparsers(dest="cmd", required=True)
    lp = sub.add_parser("login")
    lp.add_argument("--timeout", type=int, default=480)
    lp.set_defaults(fn=cmd_login)
    pp = sub.add_parser("pull")
    pp.add_argument("--conv", help="侧栏会话名关键词（缺省=当前打开的会话）")
    pp.add_argument("--out", required=True)
    pp.add_argument("--headed", action="store_true")
    pp.set_defaults(fn=cmd_pull)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
