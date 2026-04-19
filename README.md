# ccsession

分析 Claude Code 项目会话历史的 Skill：列表、详情、Token 统计、删除。

## 结构

```
ccsession/
├── README.md
└── skill/
    ├── SKILL.md              # Skill 定义（user-invocable）
    ├── scripts/
    │   ├── parse_sessions.py # 列表 + 详情
    │   └── delete_session.py # 两步确认删除
    └── references/
        └── session_schema.md # jsonl 字段速查
```

## 安装（软链到全局 skills）

```bash
ln -s /Users/yangguandao/Projects/ccsession/skill ~/.claude/skills/ccsession
```

在新 Claude Code 会话里输入 `/ccsession` 即可调用。

## 直接运行脚本（不走 Skill）

```bash
# 摘要模式（默认扫描当前目录）
python3 skill/scripts/parse_sessions.py --project /Users/yangguandao/Projects/ccsession --mode summary

# 详情模式
python3 skill/scripts/parse_sessions.py --project /Users/yangguandao/Projects/ccsession \
    --mode detail --session <sessionId>

# 删除（两步）
python3 skill/scripts/delete_session.py --project <path> --session <id>          # 预览
python3 skill/scripts/delete_session.py --project <path> --session <id> --force  # 执行
```

## 子命令

| 命令 | 说明 |
|---|---|
| `/ccsession list [--project <path>]` | 表格列出所有会话 |
| `/ccsession show <sessionId>` | 查看某会话完整步骤 |
| `/ccsession delete <sessionId>` | 删除会话 .jsonl（需确认） |

## 依赖

Python 3 标准库，无第三方包。
