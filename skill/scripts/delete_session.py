#!/usr/bin/env python3
"""Delete a Claude Code session .jsonl file (two-step: preview -> --force)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 允许直接用相对导入（scripts 同目录）
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_sessions import (  # noqa: E402
    aggregate,
    find_sessions,
    project_dir,
    render_detail,
)


def main() -> int:
    ap = argparse.ArgumentParser(description="Delete a Claude Code session jsonl file.")
    ap.add_argument("--project", required=True, help="项目绝对路径")
    ap.add_argument("--session", required=True, help="要删除的 sessionId")
    ap.add_argument("--force", action="store_true", help="实际执行删除")
    args = ap.parse_args()

    files = find_sessions(args.project)
    target = next(
        (f for f in files if f.stem == args.session or f.stem.startswith(args.session)),
        None,
    )
    if not target:
        print(f"未找到 session {args.session}。项目目录：{project_dir(args.project)}")
        return 1

    stats = aggregate(target)
    print(render_detail(stats))
    print("")
    print(f"目标文件：{target}")

    if not args.force:
        print("")
        print("⚠️  以上会话将被永久删除。请让 Claude 向用户确认后，加 --force 重新调用本脚本执行。")
        return 2

    target.unlink()
    print(f"✅ 已删除：{target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
