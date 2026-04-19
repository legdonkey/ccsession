# ccsession

分析 Claude Code 项目会话历史的 Skill：列表、详情、Token 统计、删除。

## 功能

- **列表**：表格展示所有会话，包含会话ID、模型、时间、问题摘要、AI 执行摘要、文件编辑、Subagent、Token 用量等
- **详情**：单行摘要 + 用户提问（含 Claude 模式标识）+ 文件编辑 + Subagent + AI 执行步骤
- **删除**：两步确认删除会话 `.jsonl` 文件
- **排序**：列表支持按开始时间、结束时间、轮次、时长排序
- **Token 统计**：主会话 + Subagent 分开展示，支持 k/m/g 单位
- **API 错误追踪**：统计错误次数、重试次数和等待时间

## 结构

```
ccsession/
├── CLAUDE.md
├── README.md
└── skill/
    ├── SKILL.md              # Skill 定义（user-invocable）+ 渲染规范
    ├── scripts/
    │   ├── parse_sessions.py # 解析 JSONL，输出 JSON/Markdown
    │   └── delete_session.py # 两步确认删除
    └── references/
        └── session_schema.md # JSONL 字段速查
```

## 安装

```bash
ln -s /path/to/ccsession/skill ~/.claude/skills/ccsession
```

在新 Claude Code 会话里输入 `/ccsession` 即可调用。

## 使用

### 通过 Skill 调用

| 命令 | 说明 |
|---|---|
| `/ccsession list [--project <path>]` | 表格列出所有会话 |
| `/ccsession show <sessionId>` | 会话详情（默认展示前 3 步） |
| `/ccsession show <sessionId> --full` | 会话详情（展示全部步骤） |
| `/ccsession delete <sessionId>` | 删除会话 .jsonl（需确认） |

`--project` 缺省时使用当前工作目录。`<sessionId>` 支持完整 UUID 或前缀匹配。

### 直接运行脚本

```bash
# 摘要
python3 skill/scripts/parse_sessions.py --project /path/to/project --mode summary --format json

# 详情（默认 3 步）
python3 skill/scripts/parse_sessions.py --project /path/to/project \
    --mode detail --session <id> --format json

# 详情（全部步骤）
python3 skill/scripts/parse_sessions.py --project /path/to/project \
    --mode detail --session <id> --format json --full

# 删除
python3 skill/scripts/delete_session.py --project <path> --session <id>          # 预览
python3 skill/scripts/delete_session.py --project <path> --session <id> --force  # 执行
```

## 依赖

Python 3 标准库，无第三方包。
