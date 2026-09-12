# Codex IE Lab 对话归档

这是从本机 Codex 历史记录导出的可检索归档，用于在其他电脑上浏览、搜索并为新的 Codex 对话提供上下文。归档不是 Codex 侧边栏线程的备份，也不会让云端 GPT 自动读取整个仓库。

## 内容

- `catalog/threads.csv`：对话索引，包括标题、项目、时间、归档状态和文件位置。
- `catalog/export_manifest.json`：本次导出的统计、范围和格式版本。
- `catalog/assets.json`：图片、粘贴文本、办公文件和本地交付物的哈希、来源、关联线程与处理状态。
- `catalog/link_report.json`：对话中外部链接的去重检查结果；结果只代表本次导出时刻。
- `catalog/visualizations.json`：本机生成的 HTML/图片可视化资源清单。
- `readable/`：按项目整理的 Markdown 对话文本。
- `assets/`：按 SHA-256 去重的图片和附件。对话中的已归档资源引用已改写为相对链接。
- `reports/sync_report.md`：本次同步的可读完整性报告。
- `tools/export_codex_chats.py`：只读读取 Codex 状态并生成归档的工具。

导出内容包含用户可见消息、助手可见回复、用户输入图片、工具输出图片、历史投影中仍可读取的图片引用，以及对话明确引用且可安全读取的本地资源。系统/开发者指令、隐藏推理、工具原始文本、数据库、登录凭据和凭据目录不会进入归档。文本消息和文本附件会遮盖常见 API Key、访问令牌、私钥和密码赋值；图片和二进制文件不会被宣称已经完成内容级敏感信息识别。

图片可能来自 JSONL 中的内嵌 data URL，粘贴内容来自 `~/.codex/attachments/`。历史临时截图如果已经从内嵌数据恢复，会保存内嵌副本；已删除的临时路径会在资源清单中标为缺失。无法确认属于用户线程的粘贴附件只登记为 orphan，不会混入正文。外部 HTTP/HTTPS 链接只记录原网址（敏感查询参数会脱敏）并做一次性可达性检查，不会把网页全文下载进仓库。

## 在另一台电脑上使用

克隆仓库后，可直接在 GitHub 或本地编辑器中搜索 `readable/`，并从对话中的相对链接打开 `assets/` 文件。也可以将本仓库作为 Codex 项目打开，然后让 Codex 根据 `catalog/threads.csv`、`catalog/assets.json` 和相关 Markdown 对话恢复项目背景。

这些 Markdown 文件是知识归档，不会自动恢复成 Codex 侧边栏里的原生可续聊线程。

## 重新导出

在保存有本地 Codex 历史的电脑上执行：

```bash
python3 tools/export_codex_chats.py --output . --overwrite
```

如果目标目录已有上一次生成的 `catalog/`、`readable/`、`assets/` 或 `reports/`，需要显式加入 `--overwrite`。该选项只删除这四个由导出器生成的目录，不会删除其他文件；导出前仍请先检查工作区，避免覆盖手工修改。

默认会对去重后的外部链接做只读检查。网络受限或不想请求外部站点时，可以使用：

```bash
python3 tools/export_codex_chats.py --output . --overwrite --skip-link-check
```

默认范围是本机索引中的用户线程（当前版本会包含已归档线程），不包含内部子代理线程；如确实需要内部线程，再显式加入 `--include-subagents`。

## 安全边界

不要把整个 `~/.codex` 复制进本仓库。该目录可能包含 `auth.json`、访问令牌、数据库、终端快照、日志、附件以及其他敏感状态。完整原始备份应在仓库外制作并使用独立密钥进行客户端加密。即使归档中的 Markdown 资源链接可点击，也只能保证仓库内已保存的文件可访问；远程主机路径、已删除文件和需要认证的外部链接仍会在报告中标记。