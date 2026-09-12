# Codex 对话归档同步报告

- 归档截止/生成时间：2026-09-12T09:59:21.942656+08:00
- 对话：124 条；可见消息：3596 条
- 图片与附件：366 个去重资源，共 103973305 bytes；可视化文件 11 个
- 资源引用：2405 条；状态：{'archived': 648, 'excluded_sensitive': 60, 'missing': 43, 'orphan_unassociated': 17, 'outside_allowed_root': 587, 'too_large': 1, 'unsupported_type': 1049}
- 无法关联到用户线程的粘贴附件：17 个（已安全复制到 `assets/`，但不自动插入正文）
- 外部链接：237 条去重链接；检查 214 条；状态：{'http_error': 13, 'network_error': 4, 'ok': 131, 'redirected': 66, 'skipped': 23}
- 缺失 rollout：0；解析错误：0

## 归档边界

正文保留用户可见消息和助手可见回复；用户输入图片、工具输出图片、明确引用的本地图片/文档以及可读取的粘贴文本会进入 `assets/`。隐藏推理、系统/开发者指令、工具原始文本、数据库、令牌和凭据文件不进入归档。

## 链接和资源核对

内部资源链接已在每个对话 Markdown 中改写为相对 `assets/` 链接。外部链接检查结果只代表本次运行；私有地址、含脱敏查询参数的地址和无法解析的地址会跳过请求。

详细资源清单：[`catalog/assets.json`](../catalog/assets.json)；链接清单：[`catalog/link_report.json`](../catalog/link_report.json)。

## 需要留意的未归档引用

共有 61 条资源引用没有生成仓库文件。完整条目见 `catalog/assets.json`，常见原因包括文件已删除、路径位于远程主机、格式未纳入归档范围或超过大小限制。

## 下一次更新

```bash
python3 tools/export_codex_chats.py --output . --overwrite
```

脚本会重新读取当前本机索引；不要把 `~/.codex` 原始目录复制进仓库。
