---
name: conversation-naming
description: Require and confirm a user-selected conversation title before starting substantive work in a new project conversation.
---

# Conversation Naming Gate

Use this skill at the start of every new conversation in this project, before doing substantive work.

1. Ask the user for the exact title to use. If the user's first message clearly supplies a title, use that title instead of asking again.
2. Tell the user to enter `/rename`, then enter that exact title in the Codex naming prompt. Do not claim that the title was changed: the agent has no tool to read or mutate the conversation title.
3. Wait for the user to confirm the rename is complete. Do not inspect files, run commands, analyze the task, or make changes before that confirmation.
4. After confirmation, acknowledge the title and continue with the user's pending request.

Keep the title concise and task-oriented. Do not add an inferred title, edit the user's title, or persist conversation names in repository files.
