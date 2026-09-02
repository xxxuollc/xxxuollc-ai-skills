 第一步：创建标准化的 Skills 仓库
所有主流 AI 工具（如 Claude Code, Cursor, Codex 等）都遵循 Agent Skills 规范，核心是一个 SKILL.md 文件。

创建仓库并初始化：在 GitHub 上新建一个仓库（建议命名如 my-ai-skills），然后在本地克隆。

建立标准目录结构：所有技能都放在 skills/ 目录下，每个技能一个独立文件夹。

text
my-ai-skills/
└── skills/
    └── your-skill-name/   # 技能名，使用小写字母和连字符
        ├── SKILL.md       # 核心文件，必须
        ├── scripts/       # 可选，存放可执行脚本
        ├── references/    # 可选，存放参考文档
        └── assets/        # 可选，存放静态资源
编写核心文件 SKILL.md：这是技能的灵魂，必须包含 YAML 格式的 frontmatter。

markdown
---
name: your-skill-name
description: 清晰描述这个技能的作用和何时使用它
version: '1.0.0' # 推荐添加，用于版本管理
author: your-github-username
---

# 技能标题

这里是技能的详细指令和步骤说明。

## 步骤 1
...

## 步骤 2
...
最佳实践：保持 SKILL.md 主文件在 500 行以内，详细参考信息可放入 references/ 目录。

🔗 第二步：让所有大模型共用这套 Skills
实现“一处更新，处处生效”的核心是避免复制，使用链接。主要有两种方法：

方法一：使用管理工具（推荐）
这是最简单、最优雅的方式。你已经在使用的 CC Switch 就完美支持。

在 CC Switch 的 Skills 页面，点击 “仓库管理” (Repository Management)。
点击 “添加仓库” (Add Repository)，填入你的 GitHub 仓库信息（Owner, Name, Branch 等）。
添加后，CC Switch 会自动识别仓库中的所有技能，你可以一键安装到 Claude Code, Codex, Gemini CLI 等所有支持的 AI 工具中。
原理：CC Switch 等工具通常会在本地创建一个“单一事实来源”（SSOT）目录，然后通过软链接 (Symlink) 的方式，让所有 AI 工具的技能目录都指向这个中心目录。你更新中心目录，所有工具自动同步。

方法二：手动创建软链接 (Symlink)
如果不使用管理工具，可以手动操作。以 macOS/Linux 为例：

bash
# 1. 将你的技能仓库克隆到本地一个固定位置
git clone https://github.com/your-username/my-ai-skills.git ~/my-ai-skills

# 2. 为每个AI工具创建软链接，指向仓库中的skills目录
# 例如，为 Claude Code 创建链接
ln -s ~/my-ai-skills/skills ~/.claude/skills

# 例如，为 Cursor 创建链接
ln -s ~/my-ai-skills/skills ~/.cursor/skills
这样，当你更新 ~/my-ai-skills 仓库时，所有工具都会立即感知到变化。

🚀 第三步：支持 Skills 的版本迭代
在团队协作或生产环境中，版本管理至关重要。Git 和 GitHub 提供了多种机制。

方案一：使用 gh skill 命令（最现代、最推荐）
GitHub 官方 CLI 工具提供了强大的技能管理功能。

安装特定版本：gh skill install github/your-username/my-ai-skills your-skill-name@v1.2.0

版本锁定：gh skill install ... --pin v1.2.0 可锁定版本，防止意外更新。

检测更新：gh skill update 命令会通过对比 Git 树 SHA 来检测内容是否真正发生了变化。

方案二：使用 Git Submodule（适合项目级集成）
如果你的 Skills 是某个项目的一部分，可以将其作为 Git Submodule 引入。

添加子模块：git submodule add https://github.com/your-username/my-ai-skills.git .claude/skills

更新到最新：cd .claude/skills && git pull origin main

这种方式可以锁定项目使用的技能版本。

方案三：使用 GitHub Releases（最通用）
这是最标准的软件版本发布方式。

在 GitHub 仓库页面，点击 "Releases" → "Draft a new release"。
创建一个 Git Tag（如 v1.2.0），填写发布说明，然后发布。
用户可以通过下载特定 Release 的源码包来获取特定版本的技能。
💎 总结
整个过程可以概括为：

建仓库：在 GitHub 上创建一个仓库，并按照 skills/技能名/SKILL.md 的标准结构来组织你的技能。

写技能：在 SKILL.md 中通过 YAML frontmatter 定义技能元数据，并用 Markdown 编写详细指令。

做同步：通过 CC Switch 等管理工具，或手动创建软链接的方式，让所有 AI 工具共用这一套技能文件。

管版本：使用 gh skill 命令、Git Submodule 或 GitHub Releases 来实现技能的版本锁定和更新。