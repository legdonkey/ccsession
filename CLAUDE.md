# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

ccsession 是一个 Claude Code Skill，用于分析任意项目目录下的历史会话。脚本解析 `~/.claude/projects/{编码路径}/*.jsonl`，输出 JSON 供 Claude 渲染为 Markdown 表格。

## 架构

- **`skill/SKILL.md`** — Skill 入口定义（frontmatter + 渲染规范）。所有输出格式（表格列、时间格式、Token 展示等）定义在此文件中，**不在脚本里**。脚本只输出 JSON 数据。
- **`skill/scripts/parse_sessions.py`** — 核心解析脚本。`aggregate()` 逐行读取 jsonl，按 `requestId` 去重（同一条 assistant message 会被拆成 thinking/text/tool_use 多行），累加 token 和工具调用。支持 `--format json`（Claude 渲染用）和 `--format markdown`（fallback）。
- **`skill/scripts/delete_session.py`** — 两步确认删除。复用 parse_sessions 的 aggregate 函数，先预览（exit 2），`--force` 时才删除。
- **软链** — `~/.claude/skills/ccsession → skill/`，全局可用。

## 关键设计决策

- JSONL 中同一条 message 共享 `requestId`，token 必须按 `requestId` 去重，否则 output/cache 会被重复累加约 2-3 倍
- `message.model` 以 `<` 开头的是 subagent 内部占位值（如 `<synthetic>`），需过滤
- 用户提问识别：`type=="user"` 且 `message.content` 为字符串（非数组的 tool_result）
- 会话数据流：脚本输出 JSON → Claude 读取 JSON 并生成问题摘要 → 组装 Markdown 表格

## 常用命令

```bash
# 直接运行脚本测试
python3 skill/scripts/parse_sessions.py --project "$PWD" --mode summary --format json
python3 skill/scripts/parse_sessions.py --project "$PWD" --mode detail --session <id> --format json

# 通过 Skill 调用
/ccsession list
/ccsession show <sessionId>
/ccsession show <sessionId> --full
/ccsession delete <sessionId>
```

## 依赖

Python 3 标准库，无第三方包。
