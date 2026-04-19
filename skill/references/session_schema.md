# Claude Code 会话 JSONL 字段速查

本文件供 skill 维护时参考。Claude Code 的每条会话是 `~/.claude/projects/{encoded}/{sessionId}.jsonl`，每行一条 JSON。项目路径编码规则：绝对路径中的 `/` 全部替换为 `-`。

## 行类型（顶层 `type`）

| type | 含义 |
|---|---|
| `permission-mode` | 权限模式变更（会话首行常见） |
| `file-history-snapshot` | 文件历史快照 |
| `user` | 用户消息；`message.content` 为字符串时是**真实提问**，为数组且元素含 `tool_use_id` 时是**工具返回结果** |
| `assistant` | AI 回复；`message.content` 是数组，元素 `type` 可为 `text` / `thinking` / `tool_use` |
| `attachment` | 附件：`attachment.type` 可为 `skill_listing` / `plan_mode` / `deferred_tools_delta` 等 |
| `last-prompt` | 会话最后一条提示记录（可能不总是出现） |

## 常见顶层字段

- `sessionId` — UUID，文件名即此
- `timestamp` — ISO8601 UTC（形如 `2026-04-19T03:54:27.279Z`）
- `uuid` / `parentUuid` — 消息链
- `cwd` — 当时的工作目录
- `gitBranch` / `slug` / `version`

## 识别 AI 工具调用

`type == "assistant"` 的 `message.content` 数组里，元素 `type == "tool_use"` 即一次工具调用：

- `name` — 工具名（Read / Edit / Bash / Grep / Glob / Task / Skill / `mcp__*` / …）
- `input` — 工具参数对象
- `id` — 工具调用 ID（后续在 user 消息里通过 `tool_use_id` 关联返回）

## Token 位置

在 `type == "assistant"` 行的 `message.usage`：

- `input_tokens`
- `output_tokens`
- `cache_creation_input_tokens`
- `cache_read_input_tokens`

同一条 message 可能在 jsonl 中被拆成多行（thinking / text / tool_use 各一行，`requestId` 与 `message.id` 相同）。脚本目前对每行独立累加，与官方的「按 request 聚合」接近但不完全等价。若需精确按请求去重，可按 `requestId` 去重。

## 会话开始 / 结束

- 开始：第一行 `timestamp`
- 结束：最后一行 `timestamp`

## 用户提问识别

`type == "user"` 且 `message.content` 为字符串 → 真实用户输入。`message.content` 为数组且包含 `tool_use_id` → 工具结果回传，不计入对话轮次。
