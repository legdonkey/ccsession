#!/usr/bin/env python3
"""Delete a Claude Code session .jsonl file (two-step: preview -> --force)."""
from __future__ import annotations

import argparse
import re
import shutil
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

# UUID 正则——sessionId 必须严格匹配，否则不连带删同名目录
SID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def _dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def _safe_rmtree_session_dir(sub_dir: Path, project_root: Path, session_id: str) -> None:
    """连带删同名 sessionId 子目录前的安全断言——避免误删项目级共享目录。"""
    assert SID_RE.match(session_id), f"sessionId 不是合法 UUID：{session_id}"
    assert sub_dir.parent == project_root, f"sub_dir 不在项目根下：{sub_dir}"
    assert sub_dir.name == session_id, f"sub_dir 名字与 sessionId 不一致：{sub_dir.name} vs {session_id}"
    shutil.rmtree(sub_dir)


def find_orphan_dirs(project_root: Path) -> list[Path]:
    """扫项目目录下所有 UUID 形态的子目录，挑出没有对应 .jsonl 的孤儿。"""
    if not project_root.is_dir():
        return []
    return sorted(
        d for d in project_root.iterdir()
        if d.is_dir() and SID_RE.match(d.name)
        and not (project_root / f"{d.name}.jsonl").exists()
    )


def cmd_delete(args: argparse.Namespace) -> int:
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

    project_root = target.parent
    session_id = target.stem
    sub_dir = project_root / session_id
    has_sub_dir = sub_dir.is_dir() and SID_RE.match(session_id) is not None

    print(f"目标文件：{target}")
    if has_sub_dir:
        size = _dir_size(sub_dir)
        print(f"目标子目录：{sub_dir}（含 subagent / tool-results，共 {size:,} 字节）")

    if not args.force:
        print("")
        print("⚠️  以上将被永久删除（jsonl + 同名 sessionId 子目录）。"
              "请让 Claude 向用户确认后，加 --force 重新调用本脚本执行。")
        return 2

    # 顺序：先删子目录，再删 jsonl——保证不出现"jsonl 已删但 list 仍能引用旧子目录"的中间态
    if has_sub_dir:
        _safe_rmtree_session_dir(sub_dir, project_root, session_id)
        print(f"✅ 已删除子目录：{sub_dir}")
    target.unlink()
    print(f"✅ 已删除：{target}")
    return 0


def cmd_clean_orphan_dirs(args: argparse.Namespace) -> int:
    project_root = project_dir(args.project)
    orphans = find_orphan_dirs(project_root)
    if not orphans:
        print(f"未发现孤儿子目录。项目目录：{project_root}")
        return 0

    total_size = 0
    print(f"发现 {len(orphans)} 个孤儿子目录（无对应 .jsonl，sessionId 命名）：")
    print("")
    for d in orphans:
        size = _dir_size(d)
        total_size += size
        files = sum(1 for _ in d.rglob("*") if _.is_file())
        print(f"  {d.name}  —  {files} 文件，{size:,} 字节")
    print("")
    print(f"合计 {total_size:,} 字节")
    print(f"项目目录：{project_root}")

    if not args.force:
        print("")
        print("⚠️  以上孤儿子目录将被永久删除。"
              "请让 Claude 向用户确认后，加 --force 重新调用本脚本执行。")
        return 2

    for d in orphans:
        _safe_rmtree_session_dir(d, project_root, d.name)
        print(f"✅ 已删除：{d}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Delete a Claude Code session jsonl file (and its same-name sessionId subdir).")
    ap.add_argument("--project", required=True, help="项目绝对路径")
    ap.add_argument("--session", default=None, help="要删除的 sessionId（与 --clean-orphan-dirs 互斥）")
    ap.add_argument("--clean-orphan-dirs", action="store_true",
                    help="清理项目目录下所有孤儿子目录（无对应 .jsonl 的 sessionId 命名子目录）")
    ap.add_argument("--force", action="store_true", help="实际执行删除")
    args = ap.parse_args()

    if args.clean_orphan_dirs:
        if args.session:
            print("--clean-orphan-dirs 与 --session 互斥", file=sys.stderr)
            return 2
        return cmd_clean_orphan_dirs(args)

    if not args.session:
        print("必须提供 --session 或 --clean-orphan-dirs", file=sys.stderr)
        return 2
    return cmd_delete(args)


if __name__ == "__main__":
    sys.exit(main())
