#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LLM 历史对话 · 产物渲染

读归一化 JSON（extract.py / deepseek_dom.py 的输出），按会话落三类产物：

  <out>/
    raw/<NN>-<slug>.json        原始消息（源，含时间戳/id，可随时重渲染）
    questions/<NN>-<slug>.md    该会话所有用户提问
    answers/<NN>-<slug>.md      该会话所有模型回答
    _todo-summaries.md          概括任务清单（由 agent 认领后写 summaries/）

概括（提问思路/回答思路）是 LLM 的活，本脚本不生成——只把任务列清楚。
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import re
import sys


def slugify(s: str, fallback: str) -> str:
    s = (s or "").strip()
    s = re.sub(r'[\\/:*?"<>|\s\']+', "_", s)[:40]
    return s.strip("_") or fallback


def fmt_time(t) -> str:
    if not t:
        return "时间未知"
    try:
        return datetime.datetime.fromtimestamp(float(t)).strftime("%Y-%m-%d %H:%M")
    except (TypeError, ValueError, OSError):
        return str(t)


def write(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render_conversation(out: pathlib.Path, i: int, conv: dict) -> tuple[str, int, int]:
    slug = f"{i:02d}-{slugify(conv.get('title'), conv.get('id') or 'chat')}"
    raw = dict(conv)
    write(out / "raw" / f"{slug}.json",
          json.dumps(raw, ensure_ascii=False, indent=1))

    qs, ans, nq, na = [], [], 0, 0
    for m in conv.get("messages") or []:
        t = fmt_time(m.get("time"))
        if m.get("role") == "user":
            nq += 1
            qs.append(f"## Q{nq} · {t}\n\n{m.get('text','').strip()}\n")
        elif m.get("role") == "assistant":
            na += 1
            ans.append(f"## A{na} · {t}\n\n{m.get('text','').strip()}\n")
        elif m.get("role") == "unknown":
            # 分享页兜底产物：无法定角色，原文先落 answers 并标警示
            na += 1
            ans.append(f"## A{na} · {t}\n\n> ⚠️ role 未定（分享页提取），请人工核对\n\n"
                       f"{m.get('text','').strip()}\n")

    title = conv.get("title") or "（无标题）"
    meta = (f"> 平台 {conv.get('platform','?')} · 会话 {conv.get('id','?')}\n"
            f"> 提取 {fmt_time(None) if not conv.get('createdAt') else fmt_time(conv.get('createdAt'))}\n")
    write(out / "questions" / f"{slug}.md",
          f"# {title} · 提问（{nq} 条）\n\n{meta}\n" + "\n".join(qs))
    write(out / "answers" / f"{slug}.md",
          f"# {title} · 回答（{na} 条）\n\n{meta}\n" + "\n".join(ans))
    return slug, nq, na


def main() -> int:
    ap = argparse.ArgumentParser(description="归一化 JSON → 提问/回答/原始 三类产物")
    ap.add_argument("normalized", help="归一化 JSON 路径")
    ap.add_argument("--out", required=True, help="产物根目录")
    args = ap.parse_args()

    data = json.loads(pathlib.Path(args.normalized).expanduser().read_text(encoding="utf-8"))
    convs = data.get("conversations") or []
    if not convs:
        print("!! 归一化 JSON 里没有会话")
        return 1
    out = pathlib.Path(args.out).expanduser()

    todo = ["# 概括任务清单（agent 认领：逐个会话写 summaries/<slug>.md，最后写 SUMMARY.md）", ""]
    total_q = total_a = 0
    for i, conv in enumerate(convs, 1):
        conv.setdefault("platform", data.get("platform"))
        conv.setdefault("id", str(i))
        slug, nq, na = render_conversation(out, i, conv)
        total_q += nq
        total_a += na
        rng = (fmt_time(conv.get("createdAt")) if conv.get("createdAt") else "时间未知")
        todo.append(f"- [ ] `{slug}`（{nq} 问 / {na} 答 · {rng}）→ 写 `summaries/{slug}.md`")

    todo += [
        "",
        "概括规程（对每个会话）：",
        "1. 读 questions/<slug>.md → 用 5~8 行概括**用户提问思路**（在解决什么、怎么推进、卡在哪）；",
        "2. 读 answers/<slug>.md → 用 5~8 行概括**模型回答思路**（方案取向、套路、有没有反复返工）；",
        "3. 长会话先按消息分块小结再汇总，禁止一次读完全文硬概括；",
        "4. 最后写 SUMMARY.md：跨会话汇总用户思路 + 模型思路，并注明数据日期范围。",
    ]
    write(out / "_todo-summaries.md", "\n".join(todo) + "\n")
    print(f"✓ {len(convs)} 个会话 → {out}（共 {total_q} 问 / {total_a} 答）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
