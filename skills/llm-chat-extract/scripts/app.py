#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""对话导出统一入口 · 本地网页

浏览器打开 http://localhost:8765 ：
  - DeepSeek：贴分享链接 → 点「获取」→ 生成 raw/questions/answers 三类产物
  - 抖音：点「获取」→ 拉最新私信摘要（登录态在 douyin-dm-export 技能目录）
  - ChatGPT：填官方导出 zip / conversations.json 的本地路径 → 点「获取」

所有平台共用同一套归一化 JSON（schema llm-chat-extract/1）和 render.py；
产物统一落 ~/.workbuddy/exports/llm-chat/<platform>/<日期>/。

只跑本机，无鉴权——不要把端口转发到外网。只处理本人账号数据。
"""
from __future__ import annotations

import datetime
import json
import pathlib
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

SCRIPTS = pathlib.Path(__file__).resolve().parent
EXPORT_ROOT = pathlib.Path.home() / ".workbuddy/exports/llm-chat"
DIGEST = pathlib.Path.home() / ".workbuddy/pets/douyin-digest.json"
ENV_PY = "/Users/xuquanke/.workbuddy/binaries/python/envs/default/bin/python"
PYC = ENV_PY if pathlib.Path(ENV_PY).exists() else sys.executable


def log(*a):
    print(*a, flush=True)


def run_py(script: str, args: list[str], timeout=300):
    r = subprocess.run([PYC, str(SCRIPTS / script), *args],
                       capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout + r.stderr)


def render(normalized: pathlib.Path, platform: str) -> dict:
    out = EXPORT_ROOT / platform / datetime.date.today().isoformat()
    out.mkdir(parents=True, exist_ok=True)
    code, text = run_py("render.py", [str(normalized), "--out", str(out)])
    if code != 0:
        return {"ok": False, "error": f"渲染失败：{text[-400:]}"}
    data = json.loads(normalized.read_text(encoding="utf-8"))
    files = sorted(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file())
    return {"ok": True, "outDir": str(out), "files": files,
            "conversations": len(data.get("conversations") or []),
            "messages": sum(len(c.get("messages") or []) for c in data.get("conversations") or []),
            "log": text.strip().splitlines()}


# --------------------------------------------------------------------------- #
PAGE = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<title>对话导出 · 统一入口</title><style>
body{font-family:-apple-system,sans-serif;background:#f5f5f4;color:#1c1c1a;margin:0;padding:32px;}
.wrap{max-width:720px;margin:0 auto;}
h1{font-size:19px;margin:0 0 6px;} .sub{color:#77756e;font-size:13px;margin-bottom:22px;}
.tabs{display:flex;gap:8px;margin-bottom:14px;}
.tab{padding:7px 16px;border-radius:8px;border:1px solid #d3d1c7;background:#fff;cursor:pointer;font-size:14px;}
.tab.on{background:#1d9e75;color:#fff;border-color:#1d9e75;}
.row{display:flex;gap:8px;}
input{flex:1;padding:9px 12px;border:1px solid #d3d1c7;border-radius:8px;font-size:14px;}
button{padding:9px 22px;border:none;border-radius:8px;background:#1d9e75;color:#fff;font-size:14px;cursor:pointer;}
button:disabled{opacity:.5;}
.hint{color:#77756e;font-size:12px;margin-top:8px;line-height:1.6;}
#res{margin-top:22px;background:#fff;border:1px solid #d3d1c7;border-radius:12px;padding:18px;display:none;}
#res h2{font-size:15px;margin:0 0 10px;}
.bad{color:#a32d2d}.good{color:#0f6e56}.muted{color:#77756e;font-size:13px;}
pre{background:#f1efe8;border-radius:8px;padding:10px;font-size:12px;white-space:pre-wrap;word-break:break-all;}
table{border-collapse:collapse;width:100%;font-size:13px;}
td,th{border-bottom:1px solid #e8e6de;padding:6px 8px;text-align:left;vertical-align:top;}
th{color:#77756e;font-weight:500;}
.unread{color:#ba7517;font-weight:500;}
</style></head><body><div class="wrap">
<h1>对话导出 · 统一入口</h1>
<div class="sub">选平台 → 给输入 → 点「获取」。产物统一落在 <code>~/.workbuddy/exports/llm-chat/</code></div>
<div class="tabs">
 <div class="tab on" data-p="deepseek" onclick="pick(this)">DeepSeek</div>
 <div class="tab" data-p="douyin" onclick="pick(this)">抖音私信</div>
 <div class="tab" data-p="chatgpt" onclick="pick(this)">ChatGPT 导出</div>
</div>
<div class="row"><input id="inp" placeholder="贴 DeepSeek 分享链接"><button id="go" onclick="go()">获取</button></div>
<div class="hint" id="hint"></div>
<div id="res"><h2 id="rt"></h2><div id="rb"></div></div>
</div><script>
let P='deepseek';
const HINT={
 deepseek:'粘贴形如 https://chat.deepseek.com/a/chat/s/… 的分享链接（分享页需先用浏览器打开一次确认可访问）。',
 douyin:'不需要输入，直接点「获取」= 拉取最新私信会话列表（需先扫码：douyin_digest.py login）。',
 chatgpt:'填官方导出的 zip 或 conversations.json 的完整本地路径（设置 → 数据控制 → 导出数据）。'};
function pick(el){document.querySelectorAll('.tab').forEach(t=>t.classList.remove('on'));
 el.classList.add('on');P=el.dataset.p;document.getElementById('hint').textContent=HINT[P];
 document.getElementById('inp').placeholder={deepseek:'贴 DeepSeek 分享链接',douyin:'（不需要输入）',chatgpt:'官方导出 zip/json 的本地路径'}[P];}
document.getElementById('hint').textContent=HINT[P];
async function go(){const b=document.getElementById('go');b.disabled=true;const res=document.getElementById('res');
 res.style.display='block';document.getElementById('rt').textContent='处理中…';document.getElementById('rb').innerHTML='';
 try{const r=await fetch('/api/'+P,{method:'POST',headers:{'Content-Type':'application/json'},
  body:JSON.stringify({input:document.getElementById('inp').value})});
  const d=await r.json();show(d);}catch(e){show({ok:false,error:String(e)})}
 b.disabled=false;}
function show(d){const rt=document.getElementById('rt'),rb=document.getElementById('rb');
 if(!d.ok){rt.textContent='失败';rt.className='bad';rb.innerHTML='<div class="bad">'+esc(d.error||'未知错误')+'</div>'+
  (d.log?'<pre>'+esc(d.log)+'</pre>':'');return;}
 rt.textContent='完成';rt.className='good';
 if(d.sessions){let h='<table><tr><th>会话</th><th>最后消息</th><th>时间</th><th>未读</th></tr>';
  d.sessions.forEach(s=>{h+='<tr><td>'+esc(s.title)+'</td><td>'+esc(s.preview)+'</td><td class="muted">'+esc(s.time)+'</td><td>'+(s.unread?'<span class="unread">未读 '+s.unread+'</span>':'')+'</td></tr>';});
  rb.innerHTML=h+'</table><div class="muted">'+esc(d.note||'')+'</div>';}
 else{rb.innerHTML='<div class="muted">'+esc(d.conversations)+' 个会话 · '+esc(d.messages)+' 条消息 → '+esc(d.outDir)+'</div><pre>'+esc(d.files.join('\\n'))+'</pre>'+(d.source?'<div class="muted">提取路线：'+esc(d.source)+'</div>':'');}}
function esc(s){return String(s??'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: str, ctype="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, PAGE)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        body = json.loads(self.rfile.read(n) or b"{}")
        inp = (body.get("input") or "").strip()
        try:
            if self.path == "/api/deepseek":
                self._send(200, json.dumps(self.deepseek(inp), ensure_ascii=False))
            elif self.path == "/api/douyin":
                self._send(200, json.dumps(self.douyin(), ensure_ascii=False))
            elif self.path == "/api/chatgpt":
                self._send(200, json.dumps(self.chatgpt(inp), ensure_ascii=False))
            else:
                self._send(404, json.dumps({"ok": False, "error": "no route"}))
        except Exception as e:
            self._send(200, json.dumps({"ok": False, "error": f"{e.__class__.__name__}: {e}"},
                                       ensure_ascii=False))

    def deepseek(self, link: str) -> dict:
        if "chat.deepseek.com/" not in link:
            return {"ok": False, "error": "请粘贴 chat.deepseek.com 的分享链接"}
        nz = EXPORT_ROOT / "deepseek" / f"nz-{datetime.datetime.now():%H%M%S}.json"
        code, text = run_py("deepseek_fetch.py", [link, "--out", str(nz)])
        if code != 0:
            return {"ok": False, "error": "分享链接提取失败（见日志）", "log": text[-600:]}
        res = render(nz, "deepseek")
        res["source"] = json.loads(nz.read_text()).get("source")
        return res

    def chatgpt(self, path: str) -> dict:
        if not path or not pathlib.Path(path).expanduser().exists():
            return {"ok": False, "error": f"文件不存在：{path or '（未填路径）'}"}
        nz = EXPORT_ROOT / "chatgpt" / f"nz-{datetime.datetime.now():%H%M%S}.json"
        code, text = run_py("extract.py", ["chatgpt-export", path, "--out", str(nz)])
        if code != 0:
            return {"ok": False, "error": "导出解析失败（见日志）", "log": text[-600:]}
        return render(nz, "chatgpt")

    def douyin(self) -> dict:
        code, text = run_py("douyin_digest.py", ["pull"], timeout=180)
        digest_path = pathlib.Path.home() / ".workbuddy/pets/douyin-digest.json"
        if not digest_path.exists():
            return {"ok": False, "error": "采集脚本没跑起来（见日志）", "log": text[-600:]}
        d = json.loads(digest_path.read_text(encoding="utf-8"))
        if d.get("error") == "NEED_LOGIN":
            return {"ok": False, "error": "抖音登录态失效：终端跑一次 "
                    "python ~/.workbuddy/scripts/douyin_digest.py login 扫码"}
        if not d.get("ok"):
            return {"ok": False, "error": d.get("hint") or d.get("error") or "EMPTY", "log": text[-400:]}
        sessions = [{"title": s.get("title", ""), "preview": s.get("preview", ""),
                     "time": s.get("time", ""), "unread": s.get("unread", 0)}
                    for s in d.get("sessions") or []]
        out = EXPORT_ROOT / "douyin" / datetime.date.today().isoformat()
        out.mkdir(parents=True, exist_ok=True)
        (out / "douyin-digest.json").write_text(json.dumps(d, ensure_ascii=False, indent=1),
                                                encoding="utf-8")
        lines = ["# 抖音私信摘要 · " + d.get("fetchedAt", ""), ""]
        for s in sessions:
            u = f" · 未读{s['unread']}" if s["unread"] else ""
            lines += [f"- {s['title']}（{s['time']}{u}）：{s['preview']}"]
        (out / "digest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return {"ok": True, "sessions": sessions,
                "note": f"摘要已存 {out/'digest.md'}（要导出某条会话全文见 douyin-dm-export 技能）"}

    def log_message(self, fmt, *args):
        log(fmt % args)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    log(f"==> http://localhost:{port}")
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()
