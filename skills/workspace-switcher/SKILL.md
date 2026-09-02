---
name: workspace-switcher
description: 列出所有功能工作区并切换到指定的工作区
---

# 工作区切换 Skill

## 执行流程

1. 扫描 `docs/workspaces/` 下所有子目录，获取工作区列表。
2. 向用户展示列表并等待选择。
3. 读取选中工作区的 `CONTEXT.md`，加载上下文。
4. 向用户复述当前进度，确认后开始工作。