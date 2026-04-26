#!/usr/bin/env python3
"""Write AI-generated session summaries into the per-project cache file.

缓存文件：{project_dir}/.ccsession_cache.json
结构：
    {
      "version": 1,
      "summaries": {
        "<sessionId>": {
          "mtime": 1745712345.123,
          "size": 12345,
          "summary": "**核心一句**：...",
          "generated_at": "2026-04-27T10:00:00+08:00"
        }
      }
    }

用法：
    cache_summary.py --project <path> --bulk <json_file>
    cache_summary.py --project <path> --session <id> --text <text_file>

--bulk 的 json_file 内容：
    {"<sid1>": "summary1", "<sid2>": "summary2"}
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

# 复用 parse_sessions 的项目目录解析
sys.path.insert(0, str(Path(__file__).resolve().parent))
from parse_sessions import project_dir  # noqa: E402

CACHE_FILENAME = ".ccsession_cache.json"
CACHE_VERSION = 1


def _cache_path(project_root: Path) -> Path:
    return project_root / CACHE_FILENAME


def load_cache(project_root: Path) -> dict:
    """读缓存，文件不存在/损坏返回空骨架。"""
    p = _cache_path(project_root)
    if not p.is_file():
        return {"version": CACHE_VERSION, "summaries": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("summaries"), dict):
            return {"version": CACHE_VERSION, "summaries": {}}
        data.setdefault("version", CACHE_VERSION)
        return data
    except (json.JSONDecodeError, OSError):
        return {"version": CACHE_VERSION, "summaries": {}}


def save_cache(project_root: Path, data: dict) -> None:
    """tempfile + os.replace 原子换文件，避免半截写入。"""
    p = _cache_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ccsession_cache_", suffix=".tmp", dir=str(p.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, p)
    except Exception:
        # 失败时清理临时文件
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def _stat_jsonl(project_root: Path, session_id: str) -> tuple[float, int] | None:
    """返回对应 jsonl 的 (mtime, size)；不存在返回 None。"""
    jsonl = project_root / f"{session_id}.jsonl"
    if not jsonl.is_file():
        return None
    st = jsonl.stat()
    return (st.st_mtime, st.st_size)


def write_entries(project_root: Path, items: dict[str, str]) -> tuple[int, list[str]]:
    """批量写入。返回 (写入成功条数, 跳过的 sessionId 列表)。"""
    if not items:
        return 0, []
    cache = load_cache(project_root)
    summaries: dict = cache["summaries"]
    written = 0
    skipped: list[str] = []
    now = _iso_now()
    for sid, summary in items.items():
        if not isinstance(summary, str) or not summary.strip():
            skipped.append(sid)
            continue
        st = _stat_jsonl(project_root, sid)
        if st is None:
            skipped.append(sid)
            continue
        mtime, size = st
        summaries[sid] = {
            "mtime": mtime,
            "size": size,
            "summary": summary,
            "generated_at": now,
        }
        written += 1
    if written:
        save_cache(project_root, cache)
    return written, skipped


def purge_entry(project_root: Path, session_id: str) -> bool:
    """从缓存中删除指定 sessionId；返回是否实际删了一条。"""
    p = _cache_path(project_root)
    if not p.is_file():
        return False
    cache = load_cache(project_root)
    summaries: dict = cache["summaries"]
    if session_id not in summaries:
        return False
    del summaries[session_id]
    save_cache(project_root, cache)
    return True


def cmd_bulk(args: argparse.Namespace) -> int:
    bulk_path = Path(args.bulk).expanduser()
    if not bulk_path.is_file():
        print(f"--bulk 指定的 JSON 文件不存在：{bulk_path}", file=sys.stderr)
        return 2
    try:
        items = json.loads(bulk_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"--bulk JSON 解析失败：{e}", file=sys.stderr)
        return 2
    if not isinstance(items, dict):
        print("--bulk JSON 必须是 {sessionId: summary} 形式的 object", file=sys.stderr)
        return 2
    project_root = project_dir(args.project)
    if not project_root.is_dir():
        print(f"项目目录不存在：{project_root}", file=sys.stderr)
        return 1
    written, skipped = write_entries(project_root, items)
    print(f"✅ 写入缓存 {written} 条；跳过 {len(skipped)} 条（无对应 jsonl 或摘要为空）")
    if skipped:
        for sid in skipped:
            print(f"  - 跳过：{sid}")
    return 0


def cmd_single(args: argparse.Namespace) -> int:
    text_path = Path(args.text).expanduser()
    if not text_path.is_file():
        print(f"--text 指定的文本文件不存在：{text_path}", file=sys.stderr)
        return 2
    summary = text_path.read_text(encoding="utf-8").strip()
    if not summary:
        print("摘要文本为空，拒绝写入", file=sys.stderr)
        return 2
    project_root = project_dir(args.project)
    if not project_root.is_dir():
        print(f"项目目录不存在：{project_root}", file=sys.stderr)
        return 1
    written, skipped = write_entries(project_root, {args.session: summary})
    if written:
        print(f"✅ 已缓存 {args.session} 的摘要")
        return 0
    print(f"⚠️  未写入：{args.session}（无对应 jsonl 或摘要为空）", file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Write AI-generated session summaries into per-project cache.")
    ap.add_argument("--project", required=True, help="项目绝对路径")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--bulk", help="批量回写：{sessionId: summary} 形式的 JSON 文件路径")
    g.add_argument("--session", help="单条回写：sessionId（需配合 --text）")
    ap.add_argument("--text", help="单条回写时的摘要文本文件路径")
    args = ap.parse_args()

    if args.bulk:
        return cmd_bulk(args)
    if not args.text:
        print("--session 必须配合 --text 使用", file=sys.stderr)
        return 2
    return cmd_single(args)


if __name__ == "__main__":
    sys.exit(main())
