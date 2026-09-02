---
name: project-auditor
description: 基于所有工作区文档进行全局架构审计和优化建议
---

# 全局项目审计 Skill

## 触发方式
用户输入 `/audit` 或“全局分析”时触发。

## 执行流程

1. 扫描 `docs/workspaces/*/OUTPUT/DATABASE_CHANGES.sql`，检查字段冲突。
2. 扫描 `docs/workspaces/*/OUTPUT/FILE_MANIFEST.md`，识别高频修改文件。
3. 扫描 `docs/workspaces/*/CONTEXT.md`，提取业务规则横向对比。
4. 扫描所有 `OUTPUT/FEEDBACK.md`，计算各维度平均分，提取关键词。
5. 生成 `docs/PROJECT_HEALTH_REPORT.md`，包含：
    - 🔴 高风险冲突（数据表字段重复定义）
    - 🟡 架构耦合点（多个功能改同一套核心类）
    - 🟢 已沉淀的业务资产
    - 📊 体验质量回溯（模型分、工作流分、完成度分的平均值）
    - 🤖 优化建议