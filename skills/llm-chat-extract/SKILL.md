---
name: llm-chat-extract
description: 提取主流大模型（ChatGPT、DeepSeek，可扩展）的历史对话记录，按会话产出提问汇总、回答汇总、原始消息 JSON 三类文件，并给出概括规程。适用于用户要求"导出/整理我和 ChatGPT/DeepSeek 的聊天记录""总结我的提问思路"。只处理本人账号数据。
---

# LLM 历史对话提取

把"我和大模型的聊天记录"转成三份本地产物。**核心设计：先归一，再渲染**——每家平台的原始格式先转成统一的中间 JSON（schema `llm-chat-extract/1`），渲染层只消费中间格式；适配新平台只多写一个 extractor，三个产物和概括规程全部复用。

## 来源优先级（可靠性递减，别跳级）

| 级 | 来源 | 适用 | 状态 |
|---|---|---|---|
| ① | **官方全量导出** | ChatGPT：设置 → 数据控制 → 导出数据（邮件收 zip，含 `conversations.json`） | ✅ 已实现，首选 |
| ② | **分享链接** | 两家都支持单会话分享页；免登录，但内容是否内嵌 JSON 随页面版本漂移 | ⚠️ best-effort |
| ③ | **DOM 实时爬** | DeepSeek 无官方导出时的兜底；需登录态 | ⚠️ 未实测，首跑必须人工校验 |

**优先问用户手里有没有官方导出 zip**——有就绝不爬网页。DeepSeek 若只有零星几段重要对话，优先让用户生成分享链接。

## 用法

```bash
# ① ChatGPT 官方导出（zip 或解出的 conversations.json 都收）
extract.py chatgpt-export ~/Downloads/chatgpt-export.zip --out normalized.json

# ② 分享页（两家同构）
extract.py chatgpt-share "https://chatgpt.com/share/xxx" --out normalized.json
extract.py deepseek-share "https://chat.deepseek.com/a/chat/s/xxx" --out normalized.json

# ③ DeepSeek DOM（登录态在 ~/.workbuddy/secrets/deepseek.state.json）
deepseek_dom.py login                 # 人工扫码/验证码，一次
deepseek_dom.py pull --conv 关键词 --out normalized.json

# 渲染产物（三种产物一次出齐）
render.py normalized.json --out ~/.workbuddy/exports/llm-chat/chatgpt/2026-11-12/
```

## 产物布局（按会话分）

```
~/.workbuddy/exports/llm-chat/<platform>/<run-date>/
  raw/<NN>-<slug>.json        # 原始消息（源：role/时间戳/全文，可重渲染）
  questions/<NN>-<slug>.md    # 该会话所有用户提问
  answers/<NN>-<slug>.md      # 该会话所有模型回答
  _todo-summaries.md          # 概括任务清单
  summaries/<NN>-<slug>.md    # （agent 写）该会话提问思路 + 回答思路概括
  SUMMARY.md                  # （agent 写）跨会话总概括
```

原始内容用 **JSON 不用 md**：它是"源"，保真、可重新加工；questions/answers 是渲染视图，删了能重出。

## 概括规程（agent 执行，脚本不代替）

1. **逐会话概括**，别把多会话混在一起硬概括：读 `questions/<slug>.md` 写"用户提问思路"（在解决什么、怎么推进、卡在哪）；读 `answers/<slug>.md` 写"模型回答思路"（方案取向、套路、有无反复返工）。各 5~8 行。
2. **长会话分块**：单会话消息 >100 条时先按时间段分块小结，再汇总；禁止一次读完全文硬概括（必丢信息）。
3. **注明数据范围**：SUMMARY.md 开头写清"基于 <平台> <日期范围> 的 <N> 个会话"。
4. 概括里引用具体结论时标注来自哪个会话（slug）。

## 硬边界与坑

- **只导本人账号**。导他人通信内容违法（《个保法》《刑法》253 条之一）。自动化访问违反平台用户协议，有风控风险，向用户明示。
- **ChatGPT 导出结构**：`conversations.json` 是数组，每项的 `mapping` 是**树**不是列表——沿 `current_node` 回溯 `parent` 得主链再反转（extract.py 已实现）；`content_type` 有 text/code/multimodal 等，非文本不解释、落占位符。
- **分享页结构会漂移**：`__NEXT_DATA__` → react-router 流式内嵌，挖不到 JSON 就如实报失败改走 DOM，**不要正则硬猜正文**。
- **DeepSeek DOM 是虚拟列表**（只渲染一屏），长会话必须**滚动累积**——协议（小步长、滚动校验、W=abs−2·st 跨屏定序、LIS 时间戳收尾）全文见 `~/.workbuddy/skills/douyin-dm-export/SKILL.md` 的"硬边界"，那边实测过的教训这里直接引用不重复踩。
- **历史消息没有 HTTP 接口**（DeepSeek 走 WebSocket protobuf）：别去啃协议，DOM/fiber 是正路。
- 登录态文件一律放 `~/.workbuddy/secrets/`（600），**不进 git 仓库**；产物含工作隐私，只落本地 `~/.workbuddy/exports/`，不外传不进 repo。
- 增量导出按**会话 id 去重**，同一段对话多次提取不要重复落盘。
- 平台改版（选择器/内嵌 JSON 失效）时，先跑首跑自检三步定位是提取坏了还是数据真变了。

## 首跑自检（deepseek_dom.py / 分享页路线必做）

1. 抽一条会话对照网页原文：消息条数一致、顺序无错位（"搜得到页面有、结果里没有" = 漏采）；
2. role 判定抽查 5 条：fiber 的 role 字段 vs 页面实际谁说的；
3. 多跑一次提取，两次结果应一致（ fiber 命中抖动会导致重复/漏行）。

## 扩展新平台

新增 `<platform>_dom.py`（或官方导出解析器）→ 输出同一 schema 的 normalized JSON → render.py 不动。schema 字段：`conversations[].{id,title,createdAt,messages[].{idx,role,time,text}}`，role ∈ user/assistant/unknown（unknown 渲染时会带人工核对警示）。
