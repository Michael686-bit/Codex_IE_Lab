#!/usr/bin/env python3
"""Export user-visible Codex chats and recover safe embedded assets.

The exporter reads Codex state in read-only mode. It deliberately excludes
system/developer instructions, reasoning and raw tool text. Embedded images
and explicitly referenced safe local assets are copied into a content-addressed
assets directory and linked from each conversation.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import csv
import hashlib
import ipaddress
import mimetypes
import json
import os
import re
import shutil
import socket
import sqlite3
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo


EXPORT_VERSION = 2
LOCAL_TIMEZONE = ZoneInfo("Asia/Shanghai")
MAX_ASSET_BYTES = 25 * 1024 * 1024
MAX_TOTAL_REFERENCED_BYTES = 100 * 1024 * 1024

GENERATED_CONTEXT_MARKERS = (
    "<skills_instructions>",
    "<permissions instructions>",
    "<collaboration_mode>",
    "<apps_instructions>",
    "<plugins_instructions>",
    "<model_switch>",
    "<app-context>",
    "<developer>",
    "<environment_context>",
    "# AGENTS.md instructions",
)

URL_RE = re.compile(r"(?<![\w@])https?://[^\s<>()\[\]{}\"'`，。；：！？、）》】」]+")
MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
LOCAL_PATH_RE = re.compile(
    r"(?<![\w:/])/(?:home|tmp|mnt|workspace|var/tmp)/[^\s<>\[\]{}\"'`]+"
    r"|(?<![\w])~/[^\s<>\[\]{}\"'`]+"
    r"|file:///[^\s<>\[\]{}\"'`]+"
)
CODEX_ATTACHMENT_RE = re.compile(
    r"(?P<path>/[^\s<>\[\]{}\"'`]*?\.codex/attachments/"
    r"[A-Za-z0-9-]+/[^\s<>\[\]{}\"'`]+)"
)
DATA_URL_RE = re.compile(r"^data:(?P<mime>[^;,]+)?(?:;[^,]*)?;base64,(?P<data>.*)$", re.DOTALL)

LOCAL_ASSET_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".pdf",
    ".xlsx",
    ".xls",
    ".csv",
    ".tsv",
    ".docx",
    ".pptx",
    ".zip",
    ".txt",
    ".md",
    ".html",
    ".json",
}
TEXT_ASSET_SUFFIXES = {".txt", ".md", ".csv", ".tsv", ".html", ".json"}
MIME_EXTENSIONS = {
    "image/png": ".png",
    "image/jpeg": ".jpg",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
}


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
        re.compile(r"(密码\s*(?:[:：=]|是|为)\s*)[^\s,，;；]{4,}"),
        r"\1[REDACTED]",
    ),
    (
        re.compile(r"(?i)(\bpassword\s*(?:is|[:=])\s*)[^\s,;]{4,}"),
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
    parser.add_argument(
        "--skip-link-check",
        action="store_true",
        help="Do not make network requests for external HTTP/HTTPS link checks",
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


def quote_relative_path(path: str) -> str:
    """Quote a repository-relative path for a Markdown link."""
    return urllib.parse.quote(path.replace(os.sep, "/"), safe="/-._~:@+")


def clean_url(value: str) -> str:
    value = value.strip().strip(".,;:!?`\"'")
    value = value.rstrip("。，；：！？）》】>」")
    # URLs copied from prose are sometimes followed immediately by Chinese
    # explanatory text without a space. Treat that text as the boundary.
    value = re.split(r"[\u3400-\u4dbf\u4e00-\u9fff]", value, maxsplit=1)[0]
    return value.rstrip(".,;:!?`\"'")


def redacted_url(value: str) -> str:
    """Remove credential-like query values before putting a URL in an index."""
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return value
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return value
    try:
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    except ValueError:
        return value
    changed = False
    safe_pairs: list[tuple[str, str]] = []
    for key, item in pairs:
        if re.search(r"(?i)(token|secret|password|passwd|api[_-]?key|signature|^sig$|auth)", key):
            item = "[REDACTED]"
            changed = True
        safe_pairs.append((key, item))
    if not changed:
        return value
    query = urllib.parse.urlencode(safe_pairs, doseq=True)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))


def extract_external_urls(text: str) -> list[str]:
    urls: list[str] = []
    candidates = URL_RE.findall(text)
    for target in candidates:
        target = clean_url(target)
        try:
            parsed = urllib.parse.urlsplit(target)
        except ValueError:
            continue
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            continue
        # Reject obvious parser artefacts such as http://$ and bare fragments.
        if not re.fullmatch(r"[A-Za-z0-9.-]+|\[[0-9A-Fa-f:]+\]", parsed.hostname):
            continue
        urls.append(redacted_url(target))
    return urls


def extract_local_paths(text: str) -> list[str]:
    """Find explicit local paths while leaving ordinary prose untouched."""
    found: list[str] = []
    candidates = list(LOCAL_PATH_RE.findall(text))
    for match in MARKDOWN_LINK_RE.findall(text):
        target = match.strip().split("#", 1)[0]
        if target.startswith("<") and target.endswith(">"):
            target = target[1:-1]
        if target.startswith(("/", "~/", "file://")):
            candidates.append(target)
    for candidate in candidates:
        candidate = candidate.strip().strip(".,;:!?`\"'")
        candidate = candidate.rstrip("。，；：！？）》】>」")
        if candidate.startswith("file://"):
            candidate = urllib.parse.unquote(candidate[7:])
        else:
            candidate = urllib.parse.unquote(candidate)
        candidate = re.sub(r":\d+(?::\d+)?$", "", candidate)
        candidate = re.sub(r"#L\d+(?:-L\d+)?$", "", candidate)
        if candidate.startswith("~/"):
            candidate = str(Path.home() / candidate[2:])
        if candidate.startswith(("/", "~")) and candidate not in found:
            found.append(candidate)
    return found


def source_reference(path: Path, codex_home: Path) -> str:
    """Return a portable source label without exposing the full home path."""
    try:
        rel = path.resolve().relative_to(codex_home.resolve())
        return f"codex-home/{rel.as_posix()}"
    except (ValueError, OSError):
        try:
            rel = path.resolve().relative_to(Path.home().resolve())
            return f"home/{rel.as_posix()}"
        except (ValueError, OSError):
            return path.as_posix()


def is_generated_user_context(text: str) -> bool:
    return any(marker in text for marker in GENERATED_CONTEXT_MARKERS)


def normalize_user_text(text: str) -> str:
    """Drop app-generated context around a user request and image placeholders."""
    if "# Files mentioned by the user:" in text or "# Files pasted by the user:" in text:
        match = re.search(r"## My request:\s*(.*)", text, flags=re.DOTALL)
        if match:
            text = match.group(1)
    text = re.sub(r"<image\b[^>]*>\s*</image>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<image\b[^>]*/?>", "", text, flags=re.IGNORECASE)
    text = re.sub(r"</image>", "", text, flags=re.IGNORECASE)
    return text.strip()


def metadata_turn_id(payload: dict[str, Any]) -> str:
    metadata = payload.get("internal_chat_message_metadata_passthrough")
    if isinstance(metadata, dict):
        return str(metadata.get("turn_id") or "")
    return ""


def guess_mime(path: Path, data: bytes | None = None) -> str:
    guessed, _ = mimetypes.guess_type(path.name)
    if guessed:
        return guessed
    if data:
        if data.startswith(b"\x89PNG"):
            return "image/png"
        if data.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if data.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            return "image/webp"
        if data.startswith(b"%PDF"):
            return "application/pdf"
    return "application/octet-stream"


def extension_for(mime_type: str, original_name: str = "") -> str:
    suffix = Path(original_name).suffix.lower()
    if suffix:
        return suffix
    return MIME_EXTENSIONS.get(mime_type, ".bin")


def is_text_asset(path: Path, mime_type: str) -> bool:
    return mime_type.startswith("text/") or path.suffix.lower() in TEXT_ASSET_SUFFIXES


class AssetStore:
    """Content-addressed storage for embedded and explicitly referenced files."""

    def __init__(self, output: Path, assets_dir: Path, codex_home: Path) -> None:
        self.output = output
        self.assets_dir = assets_dir
        self.codex_home = codex_home
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, dict[str, Any]] = {}
        self.mentions: list[dict[str, Any]] = []
        self._mention_keys: set[tuple[str, str, str, str, str]] = set()
        self.text_sources: dict[str, str] = {}
        self.redactions = 0
        self.stored_bytes = 0

    def _mention(
        self,
        *,
        thread_id: str,
        turn_id: str,
        kind: str,
        source: str,
        status: str,
        asset_id: str | None = None,
        detail: str = "",
    ) -> None:
        key = (thread_id, turn_id, kind, source, status)
        if key in self._mention_keys:
            return
        self._mention_keys.add(key)
        self.mentions.append(
            {
                "thread_id": thread_id,
                "turn_id": turn_id,
                "kind": kind,
                "source": source,
                "status": status,
                "asset_id": asset_id,
                "detail": detail,
            }
        )

    def add_bytes(
        self,
        data: bytes,
        *,
        mime_type: str,
        original_name: str,
        source_kind: str,
        source: str,
        thread_id: str,
        turn_id: str,
        text_for_links: str | None = None,
    ) -> dict[str, Any] | None:
        if len(data) > MAX_ASSET_BYTES:
            self._mention(
                thread_id=thread_id,
                turn_id=turn_id,
                kind=source_kind,
                source=source,
                status="too_large",
                detail=f"超过 {MAX_ASSET_BYTES // (1024 * 1024)} MiB 单文件限制",
            )
            return None
        digest = hashlib.sha256(data).hexdigest()
        asset_id = digest[:16]
        if asset_id not in self.records:
            if self.stored_bytes + len(data) > MAX_TOTAL_REFERENCED_BYTES:
                self._mention(
                    thread_id=thread_id,
                    turn_id=turn_id,
                    kind=source_kind,
                    source=source,
                    status="total_size_limit",
                    detail=f"归档资源总量超过 {MAX_TOTAL_REFERENCED_BYTES // (1024 * 1024)} MiB",
                )
                return None
            stem = safe_component(Path(original_name).stem, "asset", max_length=48)
            suffix = extension_for(mime_type, original_name)
            filename = f"{digest[:16]}--{stem}{suffix}"
            target = self.assets_dir / filename
            if not target.exists():
                target.write_bytes(data)
            rel = target.relative_to(self.output).as_posix()
            self.records[asset_id] = {
                "asset_id": asset_id,
                "path": rel,
                "filename": filename,
                "mime_type": mime_type,
                "size_bytes": len(data),
                "sha256": digest,
                "original_names": set(),
                "source_references": set(),
                "thread_ids": set(),
                "reference_count": 0,
            }
            self.stored_bytes += len(data)
        record = self.records[asset_id]
        record["original_names"].add(Path(original_name).name or "asset")
        record["source_references"].add(source)
        record["thread_ids"].add(thread_id)
        record["reference_count"] += 1
        self._mention(
            thread_id=thread_id,
            turn_id=turn_id,
            kind=source_kind,
            source=source,
            status="archived",
            asset_id=asset_id,
        )
        if text_for_links is not None:
            self.text_sources[asset_id] = text_for_links
        return record

    def add_data_url(
        self,
        value: str,
        *,
        thread_id: str,
        turn_id: str,
        ordinal: Any,
        source_kind: str = "embedded_image",
        source: str | None = None,
    ) -> dict[str, Any] | None:
        source = source or f"response-item/{ordinal}"
        match = DATA_URL_RE.match(value)
        if not match:
            self._mention(
                thread_id=thread_id,
                turn_id=turn_id,
                kind=source_kind,
                source=source,
                status="unrecognized",
                detail="图片不是可导出的 data URL",
            )
            return None
        mime_type = match.group("mime") or "application/octet-stream"
        try:
            data = base64.b64decode(match.group("data"), validate=False)
        except (ValueError, binascii.Error):
            self._mention(
                thread_id=thread_id,
                turn_id=turn_id,
                kind=source_kind,
                source=source,
                status="decode_failed",
            )
            return None
        digest = hashlib.sha256(data).hexdigest()
        return self.add_bytes(
            data,
            mime_type=mime_type,
            original_name=f"image-{digest[:12]}",
            source_kind=source_kind,
            source=source,
            thread_id=thread_id,
            turn_id=turn_id,
        )

    def add_local_file(
        self,
        path: Path,
        *,
        thread_id: str,
        turn_id: str,
        source_kind: str,
        source: str,
    ) -> dict[str, Any] | None:
        try:
            stat = path.stat()
        except OSError as exc:
            self._mention(
                thread_id=thread_id,
                turn_id=turn_id,
                kind=source_kind,
                source=source,
                status="missing",
                detail=str(exc),
            )
            return None
        if not path.is_file():
            self._mention(
                thread_id=thread_id,
                turn_id=turn_id,
                kind=source_kind,
                source=source,
                status="not_a_file",
            )
            return None
        if stat.st_size > MAX_ASSET_BYTES:
            self._mention(
                thread_id=thread_id,
                turn_id=turn_id,
                kind=source_kind,
                source=source,
                status="too_large",
                detail=f"超过 {MAX_ASSET_BYTES // (1024 * 1024)} MiB 单文件限制",
            )
            return None
        try:
            raw = path.read_bytes()
        except OSError as exc:
            self._mention(
                thread_id=thread_id,
                turn_id=turn_id,
                kind=source_kind,
                source=source,
                status="read_failed",
                detail=str(exc),
            )
            return None
        mime_type = guess_mime(path, raw)
        text_for_links: str | None = None
        data = raw
        if is_text_asset(path, mime_type):
            text, count = redact(raw.decode("utf-8", errors="replace"))
            self.redactions += count
            data = text.encode("utf-8")
            text_for_links = text
        return self.add_bytes(
            data,
            mime_type=mime_type,
            original_name=path.name,
            source_kind=source_kind,
            source=source,
            thread_id=thread_id,
            turn_id=turn_id,
            text_for_links=text_for_links,
        )

    def finalize(self) -> list[dict[str, Any]]:
        assets: list[dict[str, Any]] = []
        for record in sorted(self.records.values(), key=lambda item: item["path"]):
            item = dict(record)
            for key in ("original_names", "source_references", "thread_ids"):
                item[key] = sorted(item[key])
            assets.append(item)
        return assets


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


class LinkCollector:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}

    def add_text(self, text: str, *, thread_id: str, turn_id: str, role: str) -> None:
        for target in extract_external_urls(text):
            record = self.records.setdefault(
                target,
                {
                    "url": target,
                    "references": set(),
                    "status": "not_checked",
                    "http_status": None,
                    "final_url": None,
                    "detail": "",
                },
            )
            record["references"].add((thread_id, turn_id, role))

    @staticmethod
    def _is_private_or_local(url: str) -> tuple[bool, str]:
        try:
            parsed = urllib.parse.urlsplit(url)
            host = parsed.hostname or ""
            if parsed.username or parsed.password:
                return True, "URL 含用户信息，跳过请求"
            if "[REDACTED]" in parsed.query:
                return True, "查询参数已脱敏，跳过请求"
            if host.lower() in {"localhost", "localhost.localdomain"} or host.lower().endswith(".local"):
                return True, "本机或局域网主机"
            try:
                address = ipaddress.ip_address(host)
                if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
                    return True, "私有、回环或保留地址"
            except ValueError:
                # Resolve a hostname only to avoid sending requests to private services.
                try:
                    infos = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == "https" else 80), type=socket.SOCK_STREAM)
                except (OSError, ValueError):
                    infos = []
                for info in infos:
                    address = ipaddress.ip_address(info[4][0])
                    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved:
                        return True, "域名解析到私有、回环或保留地址"
            return False, ""
        except (ValueError, UnicodeError):
            return True, "URL 格式无法解析"

    @classmethod
    def _check_one(cls, url: str) -> dict[str, Any]:
        private, detail = cls._is_private_or_local(url)
        if private:
            return {"status": "skipped", "http_status": None, "final_url": None, "detail": detail}
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "CodexConversationArchive/2.0"},
            method="HEAD",
        )
        try:
            with urllib.request.urlopen(request, timeout=8) as response:
                final_url = redacted_url(response.geturl())
                return {
                    "status": "redirected" if final_url != redacted_url(url) and 200 <= response.status < 400 else ("ok" if 200 <= response.status < 400 else "http_error"),
                    "http_status": response.status,
                    "final_url": final_url,
                    "detail": "",
                }
        except urllib.error.HTTPError as exc:
            if exc.code == 405:
                try:
                    fallback = urllib.request.Request(
                        url,
                        headers={"User-Agent": "CodexConversationArchive/2.0", "Range": "bytes=0-0"},
                        method="GET",
                    )
                    with urllib.request.urlopen(fallback, timeout=8) as response:
                        final_url = redacted_url(response.geturl())
                        return {
                            "status": "redirected" if final_url != redacted_url(url) and 200 <= response.status < 400 else ("ok" if 200 <= response.status < 400 else "http_error"),
                            "http_status": response.status,
                            "final_url": final_url,
                            "detail": "GET fallback",
                        }
                except urllib.error.HTTPError as fallback_exc:
                    return {
                        "status": "http_error",
                        "http_status": fallback_exc.code,
                        "final_url": None,
                        "detail": "HEAD/GET 均返回 HTTP 错误",
                    }
                except (urllib.error.URLError, TimeoutError, OSError) as fallback_exc:
                    return {
                        "status": "network_error",
                        "http_status": None,
                        "final_url": None,
                        "detail": str(fallback_exc)[:180],
                    }
            return {
                "status": "http_error",
                "http_status": exc.code,
                "final_url": None,
                "detail": str(exc.reason)[:180],
            }
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return {
                "status": "network_error",
                "http_status": None,
                "final_url": None,
                "detail": str(exc)[:180],
            }

    def check_all(self, enabled: bool) -> None:
        if not enabled:
            return
        # The archive currently contains a few hundred unique links at most. Keep
        # a small pool so link checks do not overwhelm a site or the local network.
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(self._check_one, url): url for url in self.records}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    result = future.result()
                except Exception as exc:  # defensive: a malformed URL must not abort export
                    result = {"status": "network_error", "http_status": None, "final_url": None, "detail": str(exc)[:180]}
                self.records[url].update(result)

    def finalize(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for record in sorted(self.records.values(), key=lambda item: item["url"]):
            item = dict(record)
            item["references"] = [
                {"thread_id": thread_id, "turn_id": turn_id, "role": role}
                for thread_id, turn_id, role in sorted(item["references"])
            ]
            items.append(item)
        return items


def allowed_local_roots(output: Path) -> list[Path]:
    home = Path.home()
    return [
        Path("/tmp"),
        home / "文档" / "ChatGPT",
        home / "Lsy03_document",
        home / "GalbotS1文件",
        home / ".codex" / "visualizations",
        output,
    ]


def sensitive_local_path(path: Path, codex_home: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    if {".ssh", ".config", ".git", "trash"} & parts:
        return True
    if path.name.lower() in {
        "auth.json",
        ".bashrc",
        "memory.md",
        "agents.md",
        "config.toml",
        "session_index.jsonl",
        "history.jsonl",
    }:
        return True
    if path.suffix.lower() in {".env", ".pem", ".key", ".p12", ".pfx", ".pub", ".sqlite", ".db", ".jsonl"}:
        return True
    try:
        path.relative_to(codex_home / "skills")
        return True
    except ValueError:
        return False


def process_local_reference(
    path_text: str,
    *,
    thread_id: str,
    turn_id: str,
    output: Path,
    codex_home: Path,
    asset_store: AssetStore,
) -> dict[str, Any] | None:
    try:
        path = Path(path_text).expanduser().resolve()
    except (OSError, RuntimeError):
        asset_store._mention(
            thread_id=thread_id,
            turn_id=turn_id,
            kind="local_reference",
            source=path_text,
            status="invalid_path",
        )
        return None
    source = source_reference(path, codex_home)
    try:
        path.relative_to(codex_home / "attachments")
        in_codex_attachments = True
    except ValueError:
        in_codex_attachments = False
    if in_codex_attachments:
        return asset_store.add_local_file(
            path,
            thread_id=thread_id,
            turn_id=turn_id,
            source_kind="pasted_text_attachment",
            source=source,
        )
    if sensitive_local_path(path, codex_home):
        asset_store._mention(
            thread_id=thread_id,
            turn_id=turn_id,
            kind="local_reference",
            source=source,
            status="excluded_sensitive",
        )
        return None
    allowed = False
    for root in allowed_local_roots(output):
        try:
            path.relative_to(root)
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        asset_store._mention(
            thread_id=thread_id,
            turn_id=turn_id,
            kind="local_reference",
            source=source,
            status="outside_allowed_root",
        )
        return None
    if path.suffix.lower() not in LOCAL_ASSET_SUFFIXES:
        asset_store._mention(
            thread_id=thread_id,
            turn_id=turn_id,
            kind="local_reference",
            source=source,
            status="unsupported_type",
        )
        return None
    return asset_store.add_local_file(
        path,
        thread_id=thread_id,
        turn_id=turn_id,
        source_kind="local_reference",
        source=source,
    )


def load_visible_messages(
    rollout_path: Path,
    *,
    thread_id: str,
    output: Path,
    codex_home: Path,
    asset_store: AssetStore,
    link_collector: LinkCollector,
) -> tuple[list[dict[str, Any]], int, int]:
    """Read visible response messages and recover embedded/reference assets."""
    messages: list[dict[str, Any]] = []
    redactions = 0
    parse_errors = 0
    if not rollout_path.is_file():
        return messages, redactions, parse_errors

    with rollout_path.open(encoding="utf-8", errors="replace") as stream:
        for line_number, line in enumerate(stream, start=1):
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if record.get("type") != "response_item":
                continue
            payload = record.get("payload") or {}
            if payload.get("type") == "custom_tool_call_output":
                # Tool output text remains outside the archive boundary, but
                # image blocks are user-visible artifacts and can be recovered.
                output_items = payload.get("output") or []
                if not isinstance(output_items, list):
                    continue
                turn_id = metadata_turn_id(payload)
                ordinal = record.get("ordinal") or line_number
                call_id = str(payload.get("call_id") or ordinal)
                attachments: list[dict[str, Any]] = []
                for index, item in enumerate(output_items):
                    if not isinstance(item, dict) or item.get("type") != "input_image":
                        continue
                    image_url = item.get("image_url")
                    if not isinstance(image_url, str):
                        continue
                    asset = asset_store.add_data_url(
                        image_url,
                        thread_id=thread_id,
                        turn_id=turn_id,
                        ordinal=ordinal,
                        source_kind="tool_output_image",
                        source=f"tool-call/{call_id}/{index}",
                    )
                    if asset is not None and asset["asset_id"] not in {entry["asset_id"] for entry in attachments}:
                        attachments.append(asset)
                if attachments:
                    messages.append(
                        {
                            "role": "assistant",
                            "phase": "tool_output",
                            "timestamp": str(record.get("timestamp") or ""),
                            "turn_id": turn_id,
                            "text": "_工具输出图片（原始工具文本未纳入归档）。_",
                            "attachments": attachments,
                            "unresolved": [],
                        }
                    )
                continue
            if payload.get("type") != "message" or payload.get("role") not in {"user", "assistant"}:
                continue
            role = str(payload.get("role"))
            turn_id = metadata_turn_id(payload)
            ordinal = record.get("ordinal") or line_number
            content = payload.get("content") or []
            if not isinstance(content, list):
                continue
            text_parts = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict)
                and item.get("type") in {"input_text", "output_text"}
                and isinstance(item.get("text"), str)
            ]
            raw_text = "\n".join(text_parts)
            if role == "user" and is_generated_user_context(raw_text):
                continue
            text = normalize_user_text(raw_text) if role == "user" else raw_text.strip()
            if role == "assistant":
                text, count = redact(text)
                redactions += count
            else:
                text, count = redact(text)
                redactions += count

            attachments: list[dict[str, Any]] = []
            unresolved: list[dict[str, str]] = []
            path_assets: dict[str, dict[str, Any]] = {}
            for item in content:
                if not isinstance(item, dict) or item.get("type") != "input_image":
                    continue
                image_url = item.get("image_url")
                if not isinstance(image_url, str):
                    continue
                asset = asset_store.add_data_url(
                    image_url,
                    thread_id=thread_id,
                    turn_id=turn_id,
                    ordinal=ordinal,
                )
                if asset is not None and asset["asset_id"] not in {entry["asset_id"] for entry in attachments}:
                    attachments.append(asset)

            # Pasted-text attachments and explicit local files are represented in
            # the surrounding input text rather than as response content items.
            path_candidates = extract_local_paths(raw_text if role == "user" else text)
            for candidate in path_candidates:
                if candidate.startswith("/tmp/codex-clipboard-"):
                    # The corresponding embedded image is authoritative; the
                    # temporary path often disappears after the turn is stored.
                    continue
                before = len(asset_store.mentions)
                asset = process_local_reference(
                    candidate,
                    thread_id=thread_id,
                    turn_id=turn_id,
                    output=output,
                    codex_home=codex_home,
                    asset_store=asset_store,
                )
                if asset is not None and asset["asset_id"] not in {entry["asset_id"] for entry in attachments}:
                    attachments.append(asset)
                if asset is not None:
                    path_assets[candidate] = asset
                if asset is None and len(asset_store.mentions) > before:
                    mention = asset_store.mentions[-1]
                    if mention["status"] in {"missing", "not_a_file", "too_large", "read_failed", "invalid_path", "decode_failed", "unrecognized"}:
                        unresolved.append({"source": mention["source"], "status": mention["status"]})

            if text:
                link_collector.add_text(text, thread_id=thread_id, turn_id=turn_id, role=role)
            if not text and not attachments and not unresolved:
                continue
            messages.append(
                {
                    "role": role,
                    "phase": str(payload.get("phase") or ""),
                    "timestamp": str(record.get("timestamp") or ""),
                    "turn_id": turn_id,
                    "text": text,
                    "attachments": attachments,
                    "path_assets": path_assets,
                    "unresolved": unresolved,
                }
            )
    return messages, redactions, parse_errors


def rewrite_archived_markdown_links(
    text: str,
    *,
    path_assets: dict[str, dict[str, Any]],
    output: Path,
    target: Path,
) -> str:
    """Rewrite only Markdown link targets that resolve to archived assets."""
    for source, asset in sorted(path_assets.items(), key=lambda item: len(item[0]), reverse=True):
        try:
            relative = os.path.relpath(output / asset["path"], start=target.parent)
        except (KeyError, ValueError):
            continue
        replacement = quote_relative_path(relative)
        encoded_source = urllib.parse.quote(source, safe="/-._~:@+")
        source_forms = {source, encoded_source}
        for source_form in sorted(source_forms, key=len, reverse=True):
            escaped = re.escape(source_form)
            pattern = re.compile(
                r"(?P<prefix>!?\[[^\]]*\]\()(?P<left><)?"
                + escaped
                + r"(?P<anchor>:[0-9]+(?::[0-9]+)?|#L[0-9]+(?:-L[0-9]+)?)?(?P<right>>?\))"
            )
            text = pattern.sub(
                lambda match: (
                    f"{match.group('prefix')}<{replacement}{match.group('anchor') or ''}>)"
                    if match.group("left") and match.group("right").startswith(">")
                    else f"{match.group('prefix')}{replacement}{match.group('anchor') or ''})"
                ),
                text,
            )
    return text


def markdown_for_thread(
    *,
    thread_id: str,
    title: str,
    project_name: str,
    created_at: str,
    updated_at: str,
    archived: bool,
    messages: Iterable[dict[str, Any]],
    output: Path,
    target: Path,
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
        lines.extend([f"## {count}. {label}", ""])
        message_text = rewrite_archived_markdown_links(
            message.get("text", ""),
            path_assets=message.get("path_assets", {}),
            output=output,
            target=target,
        )
        if message_text:
            lines.extend([message_text, ""])
        for asset in message.get("attachments", []):
            try:
                relative = os.path.relpath(output / asset["path"], start=target.parent)
            except (KeyError, ValueError):
                continue
            link = quote_relative_path(relative)
            if str(asset.get("mime_type", "")).startswith("image/"):
                lines.extend([f"![{asset.get('filename', '归档图片')}]({link})", ""])
            else:
                lines.extend([f"[附件：{asset.get('filename', '下载文件')}]({link})", ""])
        for missing in message.get("unresolved", []):
            lines.extend([f"> 资源未归档：`{missing.get('source', '')}`（{missing.get('status', 'unknown')}）", ""])
    if count == 0:
        lines.extend(["_该线程未找到可导出的用户可见文本。_", ""])
    return "\n".join(lines).rstrip() + "\n"


def ensure_output_dirs(output: Path, overwrite: bool) -> tuple[Path, Path, Path, Path]:
    output = output.resolve()
    catalog = output / "catalog"
    readable = output / "readable"
    assets = output / "assets"
    reports = output / "reports"
    generated = (catalog, readable, assets, reports)
    existing = [path for path in generated if path.exists()]
    if existing and not overwrite:
        joined = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"generated output already exists: {joined}; use --overwrite")
    if overwrite:
        for path in existing:
            if path.parent != output or path.name not in {"catalog", "readable", "assets", "reports"}:
                raise RuntimeError(f"refusing to remove unexpected path: {path}")
            shutil.rmtree(path)
    for path in generated:
        path.mkdir(parents=True, exist_ok=False)
    return catalog, readable, assets, reports


def load_history_image_paths(codex_home: Path, thread_ids: set[str]) -> dict[str, list[dict[str, str]]]:
    """Read the historical projection for imageView/localImage references."""
    path = codex_home / "thread_history_1.sqlite"
    if not path.is_file() or not thread_ids:
        return {}
    connection = connect_readonly(path)
    result: dict[str, list[dict[str, str]]] = {}
    try:
        rows = connection.execute(
            "SELECT thread_id, item_id, item_type, item_json FROM thread_items "
            "WHERE item_type IN ('userMessage', 'imageView')"
        ).fetchall()
    finally:
        connection.close()

    def walk(value: Any, found: list[str]) -> None:
        if isinstance(value, dict):
            if value.get("type") == "localImage" and isinstance(value.get("path"), str):
                found.append(value["path"])
            elif value.get("type") == "imageView" and isinstance(value.get("path"), str):
                found.append(value["path"])
            for child in value.values():
                walk(child, found)
        elif isinstance(value, list):
            for child in value:
                walk(child, found)

    for row in rows:
        thread_id = str(row["thread_id"])
        if thread_id not in thread_ids:
            continue
        try:
            item = json.loads(row["item_json"])
        except (TypeError, json.JSONDecodeError):
            continue
        found: list[str] = []
        walk(item, found)
        for item_path in found:
            result.setdefault(thread_id, []).append(
                {
                    "path": item_path,
                    "item_id": str(row["item_id"]),
                    "item_type": str(row["item_type"]),
                }
            )
    return result


def add_history_assets(
    *,
    thread_id: str,
    history_paths: list[dict[str, str]],
    output: Path,
    codex_home: Path,
    asset_store: AssetStore,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    attachments: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in history_paths:
        path_text = entry.get("path", "")
        if not path_text or path_text in seen:
            continue
        seen.add(path_text)
        try:
            path = Path(path_text).expanduser().resolve()
        except (OSError, RuntimeError):
            asset_store._mention(
                thread_id=thread_id,
                turn_id=f"history:{entry.get('item_id', '')}",
                kind="history_image",
                source=path_text,
                status="invalid_path",
            )
            unresolved.append({"source": path_text, "status": "invalid_path"})
            continue
        before = len(asset_store.mentions)
        asset = process_local_reference(
            path.as_posix(),
            thread_id=thread_id,
            turn_id=f"history:{entry.get('item_id', '')}",
            output=output,
            codex_home=codex_home,
            asset_store=asset_store,
        )
        if asset is not None and asset["asset_id"] not in {entry["asset_id"] for entry in attachments}:
            attachments.append(asset)
        if asset is None and len(asset_store.mentions) > before:
            mention = asset_store.mentions[-1]
            if mention["status"] in {"missing", "not_a_file", "too_large", "read_failed", "invalid_path"}:
                unresolved.append({"source": mention["source"], "status": mention["status"]})
    return attachments, unresolved


def add_unassociated_attachment_mentions(
    *,
    codex_home: Path,
    selected_thread_ids: set[str],
    asset_store: AssetStore,
) -> list[str]:
    """Record pasted files that exist locally but cannot be tied to a user thread."""
    metadata = read_json(codex_home / "attachments" / "pasted-text-attachments.json", {})
    paths = metadata.get("attachmentPaths", []) if isinstance(metadata, dict) else []
    if not isinstance(paths, list):
        return []
    referenced = {
        str(item.get("source"))
        for item in asset_store.mentions
        if "/attachments/" in str(item.get("source"))
    }
    orphaned: list[str] = []
    for raw_path in paths:
        if not isinstance(raw_path, str):
            continue
        source = source_reference(Path(raw_path), codex_home)
        if source in referenced:
            continue
        orphaned.append(source)
        asset_store.add_local_file(
            Path(raw_path),
            thread_id="unknown-attachment",
            turn_id="orphan",
            source_kind="orphan_attachment",
            source=source,
        )
        asset_store._mention(
            thread_id="unknown-attachment",
            turn_id="orphan",
            kind="pasted_text_attachment",
            source=source,
            status="orphan_unassociated",
            detail="附件文件存在，但当前用户线程中没有可确认的关联引用",
        )
    return orphaned


def add_visualization_assets(
    *,
    codex_home: Path,
    asset_store: AssetStore,
    link_collector: LinkCollector,
) -> list[dict[str, Any]]:
    """Archive generated visualization files even when a chat only cited them indirectly."""
    root = codex_home / "visualizations"
    if not root.is_dir():
        return []
    result: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path.suffix.lower() not in LOCAL_ASSET_SUFFIXES:
            continue
        asset = process_local_reference(
            path.as_posix(),
            thread_id="visualizations",
            turn_id=f"visualization:{path.relative_to(root).as_posix()}",
            output=asset_store.output,
            codex_home=codex_home,
            asset_store=asset_store,
        )
        if asset is None:
            continue
        result.append({"path": path.relative_to(root).as_posix(), "asset_id": asset["asset_id"], "asset": asset})
        text_source = asset_store.text_sources.get(asset["asset_id"])
        if text_source:
            link_collector.add_text(
                text_source,
                thread_id="visualizations",
                turn_id=f"visualization:{path.name}",
                role="visualization",
            )
    return result


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_sync_report(
    path: Path,
    *,
    manifest: dict[str, Any],
    asset_summary: dict[str, Any],
    link_summary: dict[str, Any],
    mentions: list[dict[str, Any]],
) -> None:
    status_counts = Counter(str(item.get("status") or "unknown") for item in mentions)
    missing = [item for item in mentions if item.get("status") not in {"archived", "outside_allowed_root", "unsupported_type", "excluded_sensitive"}]
    lines = [
        "# Codex 对话归档同步报告",
        "",
        f"- 归档截止/生成时间：{manifest['generated_at']}",
        f"- 对话：{manifest['thread_count']} 条；可见消息：{manifest['message_count']} 条",
        f"- 图片与附件：{asset_summary['asset_count']} 个去重资源，共 {asset_summary['bytes']} bytes；可视化文件 {asset_summary['visualization_count']} 个",
        f"- 资源引用：{asset_summary['mention_count']} 条；状态：{dict(sorted(status_counts.items()))}",
        f"- 无法关联到用户线程的粘贴附件：{asset_summary['orphan_attachment_count']} 个（已安全复制到 `assets/`，但不自动插入正文）",
        f"- 外部链接：{link_summary['total']} 条去重链接；检查 {link_summary['checked']} 条；状态：{dict(sorted(link_summary['status_counts'].items()))}",
        f"- 缺失 rollout：{manifest['missing_rollout_count']}；解析错误：{manifest['parse_error_count']}",
        "",
        "## 归档边界",
        "",
        "正文保留用户可见消息和助手可见回复；用户输入图片、工具输出图片、明确引用的本地图片/文档以及可读取的粘贴文本会进入 `assets/`。隐藏推理、系统/开发者指令、工具原始文本、数据库、令牌和凭据文件不进入归档。",
        "",
        "## 链接和资源核对",
        "",
        "内部资源链接已在每个对话 Markdown 中改写为相对 `assets/` 链接。外部链接检查结果只代表本次运行；私有地址、含脱敏查询参数的地址和无法解析的地址会跳过请求。",
        "",
        f"详细资源清单：[`catalog/assets.json`](../catalog/assets.json)；链接清单：[`catalog/link_report.json`](../catalog/link_report.json)。",
    ]
    if missing:
        lines.extend([
            "",
            "## 需要留意的未归档引用",
            "",
            f"共有 {len(missing)} 条资源引用没有生成仓库文件。完整条目见 `catalog/assets.json`，常见原因包括文件已删除、路径位于远程主机、格式未纳入归档范围或超过大小限制。",
        ])
    lines.extend(
        [
            "",
            "## 下一次更新",
            "",
            "```bash",
            "python3 tools/export_codex_chats.py --output . --overwrite",
            "```",
            "",
            "脚本会重新读取当前本机索引；不要把 `~/.codex` 原始目录复制进仓库。",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    args = parse_args()
    codex_home = args.codex_home.expanduser().resolve()
    output = args.output.expanduser().resolve()
    state_path = codex_home / "state_5.sqlite"
    global_state = read_json(codex_home / ".codex-global-state.json", {})
    assignments = global_state.get("thread-project-assignments", {})
    local_projects = global_state.get("local-projects", {})
    display_titles = load_display_titles(codex_home)

    catalog_dir, readable_dir, assets_dir, reports_dir = ensure_output_dirs(output, args.overwrite)
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

    selected_thread_ids = {str(row["id"]) for row in rows}
    history_paths_by_thread = load_history_image_paths(codex_home, selected_thread_ids)
    asset_store = AssetStore(output, assets_dir, codex_home)
    link_collector = LinkCollector()
    index_rows: list[dict[str, Any]] = []
    project_counts: Counter[str] = Counter()
    total_redactions = 0
    missing_rollouts = 0
    parse_error_count = 0

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
        messages, redaction_count, parse_errors = load_visible_messages(
            rollout,
            thread_id=thread_id,
            output=output,
            codex_home=codex_home,
            asset_store=asset_store,
            link_collector=link_collector,
        )
        if not rollout.is_file():
            missing_rollouts += 1
        total_redactions += redaction_count
        parse_error_count += parse_errors

        history_assets, history_unresolved = add_history_assets(
            thread_id=thread_id,
            history_paths=history_paths_by_thread.get(thread_id, []),
            output=output,
            codex_home=codex_home,
            asset_store=asset_store,
        )
        known_asset_ids = {
            asset["asset_id"]
            for message in messages
            for asset in message.get("attachments", [])
        }
        history_assets = [asset for asset in history_assets if asset["asset_id"] not in known_asset_ids]
        if history_assets or history_unresolved:
            messages.append(
                {
                    "role": "assistant",
                    "phase": "history_asset",
                    "timestamp": "",
                    "turn_id": "history",
                    "text": "_历史投影中的图片引用（用于补全本地对话资源）。_",
                    "attachments": history_assets,
                    "unresolved": history_unresolved,
                }
            )

        content = markdown_for_thread(
            thread_id=thread_id,
            title=title,
            project_name=project_name,
            created_at=created_at,
            updated_at=updated_at,
            archived=bool(row["archived"]),
            messages=messages,
            output=output,
            target=target,
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
                "asset_count": sum(len(message.get("attachments", [])) for message in messages),
                "link_count": sum(len(extract_external_urls(message.get("text", ""))) for message in messages),
                "sha256": digest,
                "file": relative,
            }
        )

    orphan_attachment_paths = add_unassociated_attachment_mentions(
        codex_home=codex_home,
        selected_thread_ids=selected_thread_ids,
        asset_store=asset_store,
    )
    visualization_assets = add_visualization_assets(
        codex_home=codex_home,
        asset_store=asset_store,
        link_collector=link_collector,
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
        "asset_count",
        "link_count",
        "sha256",
        "file",
    ]
    with (catalog_dir / "threads.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(index_rows)

    assets = asset_store.finalize()
    for asset_id, text in asset_store.text_sources.items():
        record = asset_store.records.get(asset_id)
        if not record:
            continue
        for asset_thread_id in record["thread_ids"]:
            link_collector.add_text(text, thread_id=asset_thread_id, turn_id=f"asset:{asset_id}", role="asset")

    link_collector.check_all(enabled=not args.skip_link_check)
    links = link_collector.finalize()
    link_status_counts = Counter(str(item.get("status") or "unknown") for item in links)
    link_summary = {
        "total": len(links),
        "checked": sum(1 for item in links if item.get("status") not in {"not_checked", "skipped"}),
        "status_counts": dict(sorted(link_status_counts.items())),
    }
    asset_summary = {
        "asset_count": len(assets),
        "bytes": sum(int(item["size_bytes"]) for item in assets),
        "mention_count": len(asset_store.mentions),
        "archived_mentions": sum(1 for item in asset_store.mentions if item.get("status") == "archived"),
        "visualization_count": len(visualization_assets),
        "orphan_attachment_count": len(orphan_attachment_paths),
        "status_counts": dict(sorted(Counter(str(item.get("status") or "unknown") for item in asset_store.mentions).items())),
    }
    generated_at = datetime.now(tz=LOCAL_TIMEZONE).isoformat()
    write_json(
        catalog_dir / "assets.json",
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "assets": assets,
            "mentions": asset_store.mentions,
            "summary": asset_summary,
        },
    )
    write_json(
        catalog_dir / "link_report.json",
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "links": links,
            "summary": link_summary,
        },
    )
    write_json(
        catalog_dir / "visualizations.json",
        {
            "schema_version": 1,
            "generated_at": generated_at,
            "assets": [
                {
                    "source": item["path"],
                    "asset_id": item["asset_id"],
                    "path": item["asset"]["path"],
                    "filename": item["asset"]["filename"],
                }
                for item in visualization_assets
            ],
            "unassociated_pasted_attachment_count": len(orphan_attachment_paths),
        },
    )

    manifest = {
        "export_version": EXPORT_VERSION,
        "generated_at": generated_at,
        "thread_scope": "all" if args.include_subagents else "user",
        "thread_count": len(index_rows),
        "archived_count": sum(1 for row in index_rows if row["archived"] == "yes"),
        "message_count": sum(int(row["message_count"]) for row in index_rows),
        "redaction_count": total_redactions,
        "missing_rollout_count": missing_rollouts,
        "parse_error_count": parse_error_count,
        "attachments_exported": bool(assets),
        "asset_count": asset_summary["asset_count"],
        "asset_bytes": asset_summary["bytes"],
        "asset_reference_count": asset_summary["mention_count"],
        "unresolved_reference_count": sum(1 for item in asset_store.mentions if item.get("status") != "archived"),
        "visualization_count": asset_summary["visualization_count"],
        "orphan_attachment_count": asset_summary["orphan_attachment_count"],
        "link_count": link_summary["total"],
        "link_checked_count": link_summary["checked"],
        "link_status_counts": link_summary["status_counts"],
        "excluded_record_types": [
            "session_meta",
            "turn_context",
            "world_state",
            "reasoning",
            "tool calls and raw text outputs",
            "subagent activity",
        ],
        "project_counts": dict(sorted(project_counts.items())),
    }
    (catalog_dir / "export_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    write_sync_report(
        reports_dir / "sync_report.md",
        manifest=manifest,
        asset_summary=asset_summary,
        link_summary=link_summary,
        mentions=asset_store.mentions,
    )

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
