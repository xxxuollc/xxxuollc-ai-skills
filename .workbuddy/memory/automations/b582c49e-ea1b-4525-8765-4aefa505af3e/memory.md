# skills-repo-review 执行记录

## 2026-11-04（首次运行）
- 仓库：5 个技能，git 干净，main 已同步；待提交仅 `?? .workbuddy/`。0 错误 / 1 警告 / 4 时间提示。
- 关键发现（脚本查不出、靠读代码与核本机项目得出）：
  - `audit` 用 `.claude/docs/workspaces/`，`project-auditor` + `workspace-switcher` 用 `docs/workspaces/`，两套前缀并存；主项目 shiny-sf（18 工作区）只认前者 → 后两者会产出通篇"未发现"的假报告。
  - 全库 `FEEDBACK.md` = 0，`audit` 步骤 4 是死代码。
  - `simple-api-doc` 参考标准 3 个路径中 2 个不存在，且漏了实际存在且最贴题的 `YUYAO_NINGBO_DATA_INTERFACE_SIMPLE.md`。
  - `skill-stats.json` 只有 morning-review/wiki-digest，不能作为这 5 个技能的使用证据（技能经 symlink 装到其他工具，不写此文件）。
- 建议 5 条已写入 `~/.workbuddy/reports/skills-review/2026-11-04.md`（未改动仓库任何文件）。
- 宠物状态 `ok`。

## 2026-11-05
- 5 技能，0 错误 / 1 警告（workspace-switcher description 19 字）/ 4 条时间提示；领先远端 1 个提交，待提交 1 项（自动化 memory 自身）。
- 新发现（脚本查不出）：`~/.claude/skills/` 只有 4 个技能且是**实体拷贝**非软链 → 11-03 新增的 simple-api-doc 根本没安装；conversation-naming 安装版停在 9-02 老文案，与仓库 9-15 版本已漂移。
- 复现：`git rm --cached` 需求确认 —— `skills/.DS_Store` 与 `.workbuddy/memory/automations/*/memory.md` 被跟踪（.gitignore 对已跟踪文件无效）。
- 昨日 3 条建议（audit/project-auditor 合并、simple-api-doc 参考路径、FEEDBACK 死代码）均未采纳，今日复核仍成立，已重新列入。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-05.md`；宠物 ok。

## 2026-11-06
- 5 技能，0 错误 / 1 警告（workspace-switcher description） / 4 时间提示；main 已同步，待提交仅自动化 memory 1 项（每日 chore 自动收走，不堆积）。
- 复核实测：主项目 FEEDBACK.md 仍为 0；simple-api-doc 3 个参考路径仅 API_USAGE 存在，MIGRATION_API/SAMPLE_STRUCTURES 不存在，DATA_INTERFACE_SIMPLE 仍未列；~/.claude/skills 仍是 9-02 四技能实体拷贝、simple-api-doc 未装。
- 11-04/11-05 建议均未采纳，本轮按价值重新排序列出 5 条：①删 project-auditor 合并入 audit ②修 workspace-switcher 前缀+description ③修 simple-api-doc 参考路径与前缀统一 ④安装目录改 symlink/重拷贝（放大器）⑤删 FEEDBACK 死代码。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-06.md`；宠物 ok。

## 2026-11-07
- 5 技能，0 错误 / 1 警告（workspace-switcher description）/ 4 时间提示；领先远端 1 提交（每日 chore，正常），待提交仅自动化 memory 1 项。
- 复核：shiny-sf 工作区现为 8 个（此前 18，主人可能清理过）；FEEDBACK.md 仍 0；simple-api-doc 参考路径 MIGRATION_API/SAMPLE_STRUCTURES 仍不存在、DATA_INTERFACE_SIMPLE 仍未列；~/.claude/skills 仍是 9-02 四技能实体拷贝、simple-api-doc 未装。
- 建议仍为 5 条（同 11-06 排序），全部未采纳；明确"今天不建议动"了 conversation-naming 与正文重写（先解决合并与安装放大器）。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-07.md`；宠物 ok。

## 2026-11-08
- 5 技能，0 错误 / 1 警告（workspace-switcher description）/ 4 时间提示；领先远端 2 提交（每日 chore），待提交仅自动化 memory 1 项。
- 复核：shiny-sf 8 工作区、FEEDBACK.md 仍 0；simple-api-doc 参考 MIGRATION_API/SAMPLE_STRUCTURES 仍缺失、DATA_INTERFACE_SIMPLE 仍未列；~/.claude/skills diff 确认 conversation-naming 已漂移、simple-api-doc 未装（其余 3 个一致）。
- 5 条建议与前几日相同（删 project-auditor、修 workspace-switcher、修 simple-api-doc 路径、symlink 安装、删 FEEDBACK 死代码），全部未采纳。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-08.md`；宠物 ok。

## 2026-11-09
- 5 技能，0 错误 / 1 警告（workspace-switcher description）/ 4 时间提示；main 已同步（0/0），待提交仅自动化 memory 1 项。
- **本轮关键新证据**：shiny-5/shiny-sf 里带 CONTEXT.md 的真实功能工作区有 **19 个**，但 `docs/workspaces/` 顶层只有 **8 个** —— 11 个嵌在 `余姚/`、`龙泉信创/` 二级下。⇒ workspace-switcher 的"列顶层子目录"只能列出 8 个且把分组当工作区（读 `余姚/CONTEXT.md` 必空）。首次把这条排到第 1。
- `.claude/docs/PROJECT_HEALTH_REPORT.md` 存在（mtime 10-20，5.8KB，扫 18 个工作区）→ 证明 `audit`（`.claude` 前缀那版）确实在用且有用，但正文 glob 写的是单层 `*`、与实际执行（模型自行扩到二级）不符；且报告已过期（18→19，project-cash-money 10-21 新增后未重跑）。
- simple-api-doc：`YUYAO_NINGBO_DATA_INTERFACE_SIMPLE.md` 已存在（11-03 由该技能产出）却未列入参考；MIGRATION_API / SAMPLE_STRUCTURES 仍不存在；第 42 行前缀与第 14-16 行不一致。
- 安装层 dp 仍为 9-02 四份实体拷贝：audit/project-auditor/workspace-switcher 与仓库一致，conversation-naming 漂移，simple-api-doc 未装。`readMe.md` 是通用教程抄写、不是本仓库说明。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-09.md`；宠物 ok。

## 2026-11-10（**结论转向，务必先读这条**）
- 5 技能，0 错误 / 1 警告（workspace-switcher description）/ 4 时间提示；main 已同步，待提交仅自动化 memory 1 项。
- **推翻前 6 天前提：仓库已不是真源。** 项目 `shiny-sf/.agents/skills/`（Codex 读）与 `shiny-sf/.claude/skills/`（Claude Code 读）里的副本**比仓库新且更完整**：audit 项目版 9-03（仓库 8-12）多"第 0 步读 AGENTS.md:15 的 Workspace Output Convention"+整节《报告格式（必须遵守）》六段式契约；conversation-naming / workspace-switcher 项目版 9-30 多 `[skip]` 逃生口，conversation-naming 还去掉了"回复 1"确认协议。10-20 那份 PROJECT_HEALTH_REPORT.md 用的正是项目版格式 → 项目版才是有效版。
- 5 技能共 **13 份实体拷贝**（仓库 5 + ~/.claude 4 + 项目 .agents 2 + 项目 .claude 2），conversation-naming 有 **3 个版本**；simple-api-doc 一份都没装。
- **workspace-switcher 实测完全不可用**：项目根 `docs/` 下只有一个 electron md，`docs/workspaces` 不存在 → 照文本扫是 0 个工作区；`~/.claude/skills` 与项目 `.claude/skills` 两个副本也都还是错的。且顶层 8 个里 2 个是分组目录（余姚/龙泉信创）无 CONTEXT.md，13 个真实工作区在二级（余姚 4 + 龙泉信创 9）。
- `~/.codex/skills/` 只有 `.system` 和 `hatch-pet`，5 个技能全不在 Codex 可见范围。
- 建议 5 条（报告 `~/.workbuddy/reports/skills-review/2026-11-10.md`）：①项目 audit 回填仓库 ②修 workspace-switcher 前缀+嵌套发现+description ③删 project-auditor ④回填 `[skip]` ⑤用 `agent-skills-sync` 改软链分发。前 4 条都小改，第 5 条要重写。
- 明确"今天不建议动"：simple-api-doc 正文（质量最好，且没装，改了无感）、audit 的 FEEDBACK.md 步骤（0 个但属优雅降级，别当死代码删）、conversation-naming 英文措辞、readMe.md、.DS_Store 索引。
- 宠物 ok。**未改仓库任何文件。**

## 2026-11-11
- 5 技能，0 错误 / 1 警告 / 4 时间提示；main 已同步，待提交仅自动化 memory 1 项。
- **项目侧目录被主人主动重组（本轮最大新发现）**：shiny-sf `.claude/skills/` 移除了 audit、conversation-naming，只剩 project-auditor、workspace-switcher + 新增 `code-review-security`；`.agents/skills/` 现有 audit、conversation-naming + 新增 `concise-response`、`dotnet-to-java`。即仓库外已有 3 个活跃新技能未入库，其中 code-review-security（含 references 铁律/脱敏/git 基线）是全库质量最高的技能正文。
- 其余复核不变：19 工作区嵌套、HEALTH_REPORT 停 10-20、simple-api-doc 四处均未装、~/.claude conversation-naming 仍 9-02 漂移版、~/.codex/skills 只剩 hatch-pet（.system 消失）。
- 建议 5 条：①回收 3 个新技能入库 ②audit 回填 .agents 版 ③workspace-switcher 回填+嵌套发现+description ④conversation-naming 三副本统一 ⑤安装 simple-api-doc。前四条小改。
- 向主人提出：若某条不打算采纳请说一声，从清单撤掉，避免每日复读（连续第 8 天未采纳）。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-11.md`；宠物 ok。未改仓库任何文件。

## 2026-11-12
- **技能增至 6 个**：今日 09:17 新增 `llm-chat-extract`（78 行 + 3 脚本，全库唯一带脚本的技能，质量最好的新技能之一）。0 错误 / 1 警告（workspace-switcher description）/ 4 时间提示；main 已同步，待提交 0 项。
- **新技能首用会连撞坑（本轮主要新证据）**：①`## 用法` 写裸 `extract.py`，实际在 `scripts/` 下，照抄 command not found；②文档明令"不要正则硬猜正文"，`extract.py` 的 `PARTS_RE` 恰恰在硬扫 `"parts":[...]` 并 `return 0`，产出全 unknown 的静默错数据；③`deepseek_dom.py` 的 `is_logged_in` 用"cookie 名含 token/session"判定，访客态会误判已登录 → 采到登录页不报 NEED_LOGIN；④`render.py` meta 把会话 `createdAt` 标成"提取"时间（真值 `extractedAt` 未用）。
- 复核不变：shiny-sf 根 `docs/` 只有 electron md，`docs/workspaces` 不存在 → workspace-switcher 两个副本（仓库 + 项目 .claude，后者只多 `[skip]`）前缀仍全错；顶层 8 个里 余姚/龙泉信创 是分组，真实工作区 19（13 在二级）；HEALTH_REPORT 停 10-20（扫 18）；FEEDBACK.md 仍 0。
- 外部 3 个技能（code-review-security / concise-response / dotnet-to-java）仍未入库；`llm-chat-extract` **五个安装位置全都没有**。
- 建议 5 条：①workspace-switcher 前缀+两级发现+description ②llm-chat-extract 用法路径+3 处脚本 bug ③audit 回填 .agents 版六段式契约+glob 两级 ④删 project-auditor ⑤分发改 symlink（要重写）。③④⑤为连续第 9 天未采纳项。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-12.md`；宠物 ok。未改仓库任何文件（py_compile 产生的 `__pycache__` 已删，git status 为空）。

## 2026-11-13
- 6 技能，0 错误 / 1 警告（workspace-switcher description）/ 4 时间提示；main 领先 1（chore），待提交仅自动化 memory 1 项。
- **主人部分采纳了 llm-chat-extract 建议**：commit 8a5ea2a 新增 app.py 统一入口（198 行）+ deepseek_fetch.py（182 行），SKILL.md 用法改 app.py 推荐。残留：单命令块仍裸脚本名、extract.py PARTS_RE 硬猜、deepseek_dom is_logged_in 宽松判定、render.py createdAt 误标——全部核实仍在。
- 建议 5 条：①workspace-switcher 前缀+两级发现+description ②llm-chat-extract 4 处残留 ③audit 回填 .agents 版 ④删 project-auditor（连续第 10 天）⑤symlink 分发。外部 13 份拷贝、simple-api-doc 五处未装、~/.claude conversation-naming 9-02 漂移均复核不变。
- 报告：`~/.workbuddy/reports/skills-review/2026-11-13.md`；宠物 ok。未改仓库任何文件。

## 复用要点
- 复核工作区路径时看 `~/CareerPlanning/Internet/projects/shiny-5/shiny-sf/.claude/docs/workspaces`（主战场）与 `shiny-4/shiny-sf-4/docs/workspaces`。
- 判断技能是否真在用：看它产出的文件 mtime，不要看 `skills_repo.py` 的"N 天未改动"或 `skill-stats.json`。
- **复核技能内容前，先比对项目内副本与仓库**：`shiny-sf/.agents/skills`、`shiny-sf/.claude/skills`、`~/.claude/skills` 三处 `diff -u`，别默认仓库是最新版。
- 安装/分发机制的权威说明在 `~/.workbuddy/skills/agent-skills-sync/SKILL.md`（cc-switch 只能装 ~/.claude/skills、拷贝式、无更新检测；Codex 读 ~/.codex/skills + 项目 .agents/skills，不读 .claude/skills）。
