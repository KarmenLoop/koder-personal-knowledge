# Koder Personal Knowledge：从下载到第一次保存与检索

[English](tutorial.en.md) | 简体中文 · [项目首页](../README.zh-CN.md)

本教程对应 **v1.0.0**，把 README 中的练习路径抽成「安装 → 第一次任务 → 渠道与文件 → 排查 → 升级/卸载」。命令参考、宿主接入、架构与隐私等技术正文目前以英文为准；本页覆盖完整中文操作与边界。

## 1. 下载与安装

要求：**Python 3.9+**（含标准 `sqlite3`），无第三方包。

1. 从[发行页](https://github.com/KarmenLoop/koder-personal-knowledge/releases)下载完整技能 ZIP，或克隆 / Download ZIP 取得源码与测试。
2. 保持整个 `koder-personal-knowledge/` 目录完整（脚本 + 参考文档）。
3. 用宿主安装器导入完整目录，或放到宿主配置的技能目录。
4. 通过**受控的本地工具**提供随包 Python 脚本。
5. 每次调用由宿主提供固定库根目录、**已验证**身份与空间。
6. 启用宿主技能选择；若需每轮学习，还要在消息流程接入检索与保存。

本仓库不含桌面安装器、模型包或消息账号登录服务。导入 Markdown 技能不会创建后台进程，也不会登录消息账号。

## 2. 第一次任务（可不经宿主，直接跑本地工具）

练习使用隔离目录与合成所有者；生产宿主应提供稳定、已验证的真实身份。Windows 可用 `python` 替换 `python3`。

```sh
# 查看平台默认位置（不创建任何内容）
python3 koder-personal-knowledge/scripts/knowledge.py path

# 为本教程创建单独库
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge init --owner local-owner

# 带来源保存一条样例偏好
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  remember --record examples/preference.json

# 在较小篇幅预算内检索
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  search "summary" --max-chars 2000

# 归档选中的文本文件及内容
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  import-file --file examples/field-notes.txt --source examples/file-source.json

# 重建本地视图并打印位置
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner render
```

浏览器打开 `demo-knowledge/views/index.html`。离线可用，但包含完整库，应留在所有者电脑上。

**PowerShell：**

```powershell
$Script = ".\koder-personal-knowledge\scripts\knowledge.py"
python $Script --root .\demo-knowledge init --owner local-owner
python $Script --root .\demo-knowledge --principal local-owner remember --record .\examples\preference.json
python $Script --root .\demo-knowledge --principal local-owner search "summary" --max-chars 2000
python $Script --root .\demo-knowledge --principal local-owner import-file --file .\examples\field-notes.txt --source .\examples\file-source.json
python $Script --root .\demo-knowledge --principal local-owner render
```

只统计可访问记录、不返回笔记正文：

```sh
python3 koder-personal-knowledge/scripts/knowledge.py --root ./demo-knowledge --principal local-owner stats
```

查看共享空间时在 `stats` 前加 `--space SPACE_ID`。更正、共享、默认值与错误见[命令参考](../koder-personal-knowledge/references/commands.md)。

### 默认根目录

| 系统 | 默认 |
| --- | --- |
| 有 D: 的 Windows | `D:\KoderKnowledge` |
| 无 D: 的 Windows | 用户资料目录内 `KoderKnowledge` |
| macOS / Linux | `~/KoderKnowledge` |

`--root` 或 `KODER_KNOWLEDGE_ROOT` 可另选位置。初始化后应保存绝对路径。换路径不迁移；D: 不可写会报错，不会偷偷另建库。

## 3. 渠道、共享与文件

- 宿主必须认证入站消息，并将已关联账号映射到验证身份。
- 所有者可向已验证群组身份共享空间（`reader` / `writer`）。仅所有者能改授权、删除、替代事实或渲染完整库。
- 知识访问 ≠ 执行电脑任务或给新收件人发文件。
- UTF-8 / GB18030 可直接索引。PDF/Office/图片可归档；可搜索文本需宿主解析或 OCR。`attachment_only` ≠ 正文可检索。
- 默认限制：每原文件 32 MiB、每条记录 256K 字符。关键词 / 中文片段检索；无向量搜索。
- 连接托管模型或共享渠道前：读[隐私](privacy.md)。接入输入见[宿主接入](../koder-personal-knowledge/references/host-integration.md)。

### 隐私要点（中文摘要）

- 存储工具本身无遥测、云账号或后台全盘扫描。
- 宿主可能把消息与摘录发给模型——本地存储 ≠ 整段对话离线。
- 完整 HTML/JSON/Markdown 视图是所有者视图，不要公开发布或提交到 Git。
- 更正会保留被替代历史直至删除；`forget` 不能保证物理擦除，也不能删除应用消息、备份或提供方日志。

## 4. 排查问题

- **命令 JSON 错误 / 退出码异常：** 检查根目录、是否已 init、身份是否验证、空间是否授权（[命令参考](../koder-personal-knowledge/references/commands.md)）。
- **PDF 导入了但搜不到正文：** 多半是 `attachment_only`——需宿主解析/OCR 并提供摘出文本。
- **原文件变成 `.bin`：** 受管副本用惰性扩展名；元数据保留原名。
- **手机看不到库：** 宿主须在运行且渠道已接通；本仓库不是中继服务。
- **群里看到私聊事实：** 复查显式空间授权；撤销后停止后续工具访问（[faq](faq.md)）。
- **权限 / 锁 / 磁盘错误：** 检查系统权限、剩余空间与并发写入。

## 5. 升级、回退与卸载

1. 升级前做**完整**库备份（SQLite 感知方式 + 引用文件）——不要只复制正在写入的主库文件。
2. 阅读目标版本的 [CHANGELOG.md](../CHANGELOG.md)。
3. 先在**副本**上验证升级或回退。改 `--root` 不能代替迁移。
4. 用新版本技能目录替换旧目录；除非有意迁移，否则保持库路径稳定。
5. 移除技能**不会**自动删除外部知识库。需要遗忘内容时，按命令参考中的删除流程操作，再核对生成视图与保留的备份。

## 6. 开发自检

```sh
python3 -B -m unittest discover -s tests -v
```

测试使用临时目录与合成数据，不会打开个人库、连接消息账号或调用付费 API。macOS 本地通过不能单独证明 Windows/Linux 原生或托管 CI（[validation](validation.md)）。

[项目首页](../README.zh-CN.md) · [English tutorial](tutorial.en.md)
