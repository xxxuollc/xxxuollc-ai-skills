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

## 复用要点
- 复核工作区路径时看 `~/CareerPlanning/Internet/projects/shiny-5/shiny-sf/.claude/docs/workspaces`（主战场）与 `shiny-4/shiny-sf-4/docs/workspaces`。
- 判断技能是否真在用：看它产出的文件 mtime，不要看 `skills_repo.py` 的"N 天未改动"或 `skill-stats.json`。
