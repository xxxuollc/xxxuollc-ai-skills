---
name: audit
description: 对当前项目的所有工作区文档进行全局架构审计，检查数据库字段冲突、文件耦合、业务规则一致性和反馈质量，并生成项目健康报告。用户输入 /audit、$audit 或“全局分析”时使用。
---

# 全局项目审计

执行以下检查，并将结果写入 `.claude/docs/PROJECT_HEALTH_REPORT.md`：

1. 扫描 `.claude/docs/workspaces/*/OUTPUT/DATABASE_CHANGES.sql`，检查字段冲突和重复定义。
2. 扫描 `.claude/docs/workspaces/*/OUTPUT/FILE_MANIFEST.md`，识别高频修改文件和架构耦合点。
3. 扫描 `.claude/docs/workspaces/*/CONTEXT.md`，提取并横向对比业务规则。
4. 扫描所有 `.claude/docs/workspaces/*/OUTPUT/FEEDBACK.md`，计算模型分、工作流分和完成度分的平均值，提取关键词。
5. 生成报告，包含高风险冲突、架构耦合点、已沉淀的业务资产、体验质量回溯和可执行的优化建议。

如果某类输入文件不存在，在报告中明确标注“未发现”，不要虚构数据。报告生成后，简要汇总关键风险、资产和建议。
