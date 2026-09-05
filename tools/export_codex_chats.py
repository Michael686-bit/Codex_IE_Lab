#!/usr/bin/env python3
"""Export user-visible Codex chats to a searchable, redacted Markdown archive.

The exporter reads Codex state in read-only mode. It deliberately excludes
system/developer instructions, reasoning, tool calls and tool outputs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


EXPORT_VERSION = 1
LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")


REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?"
            r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.DOTALL,
        ),
        "[REDACTED PRIVATE KEY]",
    ),
    (
        re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{12,}"),
        "Authorization: Bearer [REDACTED]",
    ),
    (
        re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}\b"),
        "[REDACTED OPENAI KEY]",
    ),
    (
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b|\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
        "[REDACTED GITHUB TOKEN]",
    ),
    (
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b"),
        "[REDACTED SLACK TOKEN]",
    ),
    (
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
        "[REDACTED AWS ACCESS KEY]",
    ),
    (
        re.compile(
            r"(?i)([\"']?(?:access_token|refresh_token|api_key|secret_key)[\"']?\s*[:=]\s*)"
            r"[\"']?[A-Za-z0-9._~+/=-]{12,}[\"']?"
        ),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)(\bpassword\s*[:=]\s*)[^\s,;]{4,}"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(密码\s*[:：=]\s*)[^\s,，;；]{4,}"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"https?://([^/@\s:]+):([^/@\s]+)@"),
        r"https://[REDACTED]@",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
        help="Codex state directory (default: CODEX_HOME or ~/.codex)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd(),
        help="Archive repository root (default: current directory)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace previously generated catalog/ and readable/ directories",
    )
    parser.add_argument(
        "--include-subagents",
        action="store_true",
        help="Also export internal subagent threads (excluded by default)",
    )
    return parser.parse_args()


def connect_readonly(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def redact(text: str) -> tuple[str, int]:
    result = text.replace("\x00", "")
    total = 0
    for pattern, replacement in REDACTION_PATTERNS:
        result, count = pattern.subn(replacement, result)
        total += count
    # Preserve message line structure while avoiding noisy Git whitespace errors.
    result = "\n".join(line.rstrip() for line in result.splitlines())
    return result.strip(), total


def safe_component(value: str, fallback: str, max_length: int = 80) -> str:
    value = " ".join(value.split()).strip()
    value = re.sub(r"[\\/:*?\"<>|\x00-\x1f]", "-", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-. ")
    return (value or fallback)[:max_length].rstrip("-. ") or fallback


def iso_from_epoch(value: Any, *, milliseconds: bool) -> str:
    if value in (None, ""):
        return ""
    try:
        number = float(value)
        if milliseconds:
            number /= 1000.0
        return datetime.fromtimestamp(number, tz=timezone.utc).astimezone(LOCAL_TIMEZONE).isoformat()
    except (TypeError, ValueError, OSError):
        return str(value)


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def load_display_titles(codex_home: Path) -> dict[str, str]:
    path = codex_home / "sqlite" / "codex-dev.db"
    if not path.is_file():
        return {}
    conn = connect_readonly(path)
    try:
        return {
            row["thread_id"]: row["display_title"]
            for row in conn.execute(
                "SELECT thread_id, display_title FROM local_thread_catalog "
                "WHERE display_title IS NOT NULL AND TRIM(display_title) <> ''"
            )
        }
    finally:
        conn.close()


def load_visible_messages(rollout_path: Path) -> tuple[list[dict[str, str]], int]:
    messages: list[dict[str, str]] = []
    redactions = 0
    if not rollout_path.is_file():
        return messages, redactions

    with rollout_path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            if record.get("type") != "event_msg":
                continue
            payload = record.get("payload") or {}
            kind = payload.get("type")
            if kind == "user_message":
                role = "user"
            elif kind == "agent_message":
                role = "assistant"
            else:
                continue

            raw_message = payload.get("message")
            if not isinstance(raw_message, str) or not raw_message.strip():
                continue
            message, count = redact(raw_message)
            redactions += count
            if not message:
                continue
            messages.append(
                {
                    "role": role,
                    "phase": str(payload.get("phase") or ""),
                    "timestamp": str(record.get("timestamp") or ""),
                    "text": message,
                }
            )
    return messages, redactions


def markdown_for_thread(
    *,
    thread_id: str,
    title: str,
    project_name: str,
    created_at: str,
    updated_at: str,
    archived: bool,
    messages: Iterable[dict[str, str]],
) -> str:
    lines = [
        f"# {title}",
        "",
        f"- 归档编号：`{thread_id}`",
        f"- 项目：{project_name}",
        f"- 创建时间：{created_at or '未知'}",
        f"- 更新时间：{updated_at or '未知'}",
        f"- 状态：{'已归档' if archived else '活动'}",
        "- 导出范围：用户可见消息与助手可见回复；不含隐藏推理和工具原始输出",
        "",
    ]

    count = 0
    for count, message in enumerate(messages, start=1):
        if message["role"] == "user":
            label = "用户"
        else:
            phase = message.get("phase", "")
            label = "助手（进展）" if phase == "commentary" else "助手"
        lines.extend(
            [
                f"## {count}. {label}",
                "",
                message["text"],
                "",
            ]
        )
    if count == 0:
        lines.extend(["_该线程未找到可导出的用户可见文本。_", ""])
    return "\n".join(lines).rstrip() + "\n"


def ensure_output_dirs(output: Path, overwrite: bool) -> tuple[Path, Path]:
    output = output.resolve()
    catalog = output / "catalog"
    readable = output / "readable"
    existing = [path for path in (catalog, readable) if path.exists()]
    if existing and not overwrite:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"generated output already exists: {joined}; use --overwrite")
    if overwrite:
        for path in existing:
            if path.parent != output or path.name not in {"catalog", "readable"}:
                raise RuntimeError(f"refusing to remove unexpected path: {path}")
            shutil.rmtree(path)
    catalog.mkdir(parents=True, exist_ok=False)
    readable.mkdir(parents=True, exist_ok=False)
    return catalog, readable


def main() -> int:
    args = parse_args()
    codex_home = args.codex_home.expanduser().resolve()
    output = args.output.expanduser().resolve()
    state_path = codex_home / "state_5.sqlite"
    global_state = read_json(codex_home / ".codex-global-state.json", {})
    assignments = global_state.get("thread-project-assignments", {})
    local_projects = global_state.get("local-projects", {})
    display_titles = load_display_titles(codex_home)

    catalog_dir, readable_dir = ensure_output_dirs(output, args.overwrite)
    state = connect_readonly(state_path)
    try:
        if args.include_subagents:
            query = "SELECT * FROM threads ORDER BY recency_at_ms DESC, updated_at DESC"
            rows = state.execute(query).fetchall()
        else:
            query = (
                "SELECT * FROM threads WHERE thread_source = 'user' "
                "ORDER BY recency_at_ms DESC, updated_at DESC"
            )
            rows = state.execute(query).fetchall()
    finally:
        state.close()

    index_rows: list[dict[str, Any]] = []
    project_counts: Counter[str] = Counter()
    total_redactions = 0
    missing_rollouts = 0

    for row in rows:
        thread_id = str(row["id"])
        title = display_titles.get(thread_id) or row["title"] or "无标题"
        title = " ".join(str(title).split())
        assignment = assignments.get(thread_id) or {}
        project_id = assignment.get("projectId")
        project = local_projects.get(project_id, {}) if project_id else {}
        project_name = str(project.get("name") or "无项目对话")
        project_slug = safe_component(project_name, "projectless")

        created_at = iso_from_epoch(
            row["created_at_ms"] or row["created_at"],
            milliseconds=bool(row["created_at_ms"]),
        )
        updated_at = iso_from_epoch(
            row["updated_at_ms"] or row["updated_at"],
            milliseconds=bool(row["updated_at_ms"]),
        )
        date_part = created_at[:10] if created_at else "unknown-date"
        filename = (
            f"{date_part}--{thread_id}--"
            f"{safe_component(title, 'untitled', max_length=64)}.md"
        )
        project_dir = readable_dir / project_slug
        project_dir.mkdir(parents=True, exist_ok=True)
        target = project_dir / filename

        rollout_raw = row["rollout_path"]
        rollout = Path(rollout_raw) if rollout_raw else Path("/__missing_rollout__")
        messages, redaction_count = load_visible_messages(rollout)
        if not rollout.is_file():
            missing_rollouts += 1
        total_redactions += redaction_count

        content = markdown_for_thread(
            thread_id=thread_id,
            title=title,
            project_name=project_name,
            created_at=created_at,
            updated_at=updated_at,
            archived=bool(row["archived"]),
            messages=messages,
        )
        target.write_text(content, encoding="utf-8")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        relative = target.relative_to(output).as_posix()

        project_counts[project_name] += 1
        index_rows.append(
            {
                "thread_id": thread_id,
                "title": title,
                "project": project_name,
                "created_at": created_at,
                "updated_at": updated_at,
                "archived": "yes" if row["archived"] else "no",
                "message_count": len(messages),
                "redaction_count": redaction_count,
                "sha256": digest,
                "file": relative,
            }
        )

    fieldnames = [
        "thread_id",
        "title",
        "project",
        "created_at",
        "updated_at",
        "archived",
        "message_count",
        "redaction_count",
        "sha256",
        "file",
    ]
    with (catalog_dir / "threads.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(index_rows)

    manifest = {
        "export_version": EXPORT_VERSION,
        "generated_at": datetime.now(tz=LOCAL_TIMEZONE).isoformat(),
        "thread_scope": "all" if args.include_subagents else "user",
        "thread_count": len(index_rows),
        "archived_count": sum(1 for row in index_rows if row["archived"] == "yes"),
        "message_count": sum(int(row["message_count"]) for row in index_rows),
        "redaction_count": total_redactions,
        "missing_rollout_count": missing_rollouts,
        "attachments_exported": False,
        "excluded_record_types": [
            "session_meta",
            "turn_context",
            "world_state",
            "reasoning",
            "tool calls and outputs",
            "subagent activity",
        ],
        "project_counts": dict(sorted(project_counts.items())),
    }
    (catalog_dir / "export_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
