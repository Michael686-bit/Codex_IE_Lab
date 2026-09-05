# Codex IE Lab 对话归档

这是从本机 Codex 历史记录导出的可检索文本归档，用于在其他电脑上浏览、搜索并为新的 Codex 对话提供上下文。

## 内容

- `catalog/threads.csv`：对话索引，包括标题、项目、时间、归档状态和文件位置。
- `catalog/export_manifest.json`：本次导出的统计与格式版本。
- `readable/`：按项目整理的 Markdown 对话文本。
- `tools/export_codex_chats.py`：只读导出工具。

导出内容仅包含用户可见的消息和助手可见回复。系统/开发者指令、隐藏推理、工具调用、终端原始输出、数据库、登录凭据和附件均未纳入归档。导出器还会遮盖常见 API Key、访问令牌、私钥和密码赋值。

## 在另一台电脑上使用

克隆仓库后，可直接在 GitHub 或本地编辑器中搜索 `readable/`。也可以将本仓库作为 Codex 项目打开，然后让 Codex根据 `catalog/threads.csv` 和相关 Markdown 对话恢复项目背景。

这些 Markdown 文件是知识归档，不会自动恢复成 Codex 侧边栏里的原生可续聊线程。

## 重新导出

在保存有本地 Codex 历史的电脑上执行：

```bash
python3 tools/export_codex_chats.py --output .
```

如果目标目录已有上一次生成的 `catalog/` 和 `readable/`，需要显式加入 `--overwrite`。导出前请先检查工作区，避免覆盖手工修改。

## 安全边界

不要把整个 `~/.codex` 复制进本仓库。该目录可能包含 `auth.json`、访问令牌、数据库、终端快照、日志、附件以及其他敏感状态。完整原始备份应在仓库外制作并使用独立密钥进行客户端加密。
