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

## 复用要点
- 复核工作区路径时看 `~/CareerPlanning/Internet/projects/shiny-5/shiny-sf/.claude/docs/workspaces`（主战场）与 `shiny-4/shiny-sf-4/docs/workspaces`。
- 判断技能是否真在用：看它产出的文件 mtime，不要看 `skills_repo.py` 的"N 天未改动"或 `skill-stats.json`。
