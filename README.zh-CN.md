# Koder Personal Knowledge

[English](README.md) | 简体中文 · **v1.0.0**

![Python 3.9 or later](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![MIT license](https://img.shields.io/badge/License-MIT-2D7D46)
![Storage: local SQLite](https://img.shields.io/badge/Storage-Local%20SQLite-59636E)

**把智能体的笔记与参考文件放进本地资料库：查找偏好、定位原文或更正旧事实，无须把所有历史对话塞进模型上下文。**

由 [KarmenLoop](https://github.com/KarmenLoop) 为 [Koder](https://karmenloop.com) 开发，包含可移植技能和一个小型 Python 工具，其他宿主也可接入。存储工具**不发网络请求**；宿主仍可能把检索摘录发给自己配置的模型。

[下载](https://github.com/KarmenLoop/koder-personal-knowledge/releases) · [中文教程](docs/tutorial.zh-CN.md) · [English tutorial](docs/tutorial.en.md) · [许可](LICENSE) · [支持](SUPPORT.md)

---

## 为什么做这个

长对话会埋掉偏好、模糊来源。智能体要么忘掉长期事实，要么把整段历史塞进模型窗口。Personal Knowledge 用**可检查的本地记录**保存来源、做有限检索、带历史的更正，以及可选的共享空间——同时不声称云同步或内置消息登录。

---

## 一览

| | |
| --- | --- |
| **安装内容** | 完整 `koder-personal-knowledge/` 技能目录 + 随包 `knowledge.py` |
| **版本** | **1.0.0**（`VERSION`） |
| **运行时** | Python **3.9+** 与标准 `sqlite3`；无第三方包 |
| **存储** | 本地 SQLite + 受管文件副本 + 离线 HTML/Markdown/JSON 视图 |
| **工具网络** | 存储脚本：**无** |
| **许可** | [MIT](LICENSE) |
| **本版不含** | 云同步、多电脑写入协议、内置 PDF/OCR、微信/飞书登录适配器 |

---

## 是 / 不是

| 是 | 不是 |
| --- | --- |
| 面向智能体的本地个人知识库 | 托管聊天机器人或模型微调 |
| 对笔记与所选文件的有限检索 | 每次把整个库塞进提示 |
| 带被替代历史的更正；带墓碑的遗忘 | 对 SSD 或云厂商日志的物理安全擦除 |
| 经宿主、面向已验证身份的共享空间 | 用各应用显示名直接当身份 |
| 离线 HTML / Markdown / JSON 检查 | 面向公开传播的完整导出 |
| 可移植技能 + 标准库 Python 工具 | 桌面安装器、渠道登录服务或向量搜索 |

---

## 功能

| 能力 | 行为 |
| --- | --- |
| 日常记录 | 保存明确、长期有用的偏好与事实，无需先填长问卷 |
| 个人上下文 | 资料、习惯、关系、工具、工作、行业、生活 |
| 参考文件 | 管理所选文件副本，保留原名、来源与 SHA-256 |
| 有限检索 | 返回限定摘录，不默认发送整个库 |
| 事实与推断 | 行为推断在用户确认前保持未确认 |
| 更正历史 | 新事实替代旧记录，保留来源与被替代状态 |
| 可检查视图 | 本地 HTML、逐条 Markdown、完整 JSON 目录 |
| 共享空间 | 所有者向已验证用户或群组授予读取或贡献权限 |
| 本地写入 | SQLite 事务、原子替换、事件去重、有界锁等待 |
| 遗忘 | 删除记录与不再引用的文件，拦截已删事件重试 |

八类合一库：个人资料、习惯偏好、人物关系、工具、工作职业、行业知识、日常生活、参考资料。空库即可使用。

---

## 快速开始

要求 **Python 3.9+**。从[发行页](https://github.com/KarmenLoop/koder-personal-knowledge/releases)取得完整技能 ZIP，或：

```sh
git clone https://github.com/KarmenLoop/koder-personal-knowledge.git
cd koder-personal-knowledge
```

保持整个 `koder-personal-knowledge/` 目录完整。示例（隔离演示目录；生产请用已验证的真实身份）：

```sh
python3 koder-personal-knowledge/scripts/knowledge.py path
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge init --owner local-owner
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  remember --record examples/preference.json
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  search "summary" --max-chars 2000
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  import-file --file examples/field-notes.txt --source examples/file-source.json
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner render
```

浏览器打开 `demo-knowledge/views/index.html`（离线可用，含完整库，应留在所有者电脑）。安装、宿主接入、渠道、升级与卸载见[中文教程](docs/tutorial.zh-CN.md)。

### 默认位置

| 系统 | 默认根目录 |
| --- | --- |
| 有 D: 的 Windows | `D:\KoderKnowledge` |
| 无 D: 的 Windows | 用户资料目录内 `KoderKnowledge`（重定向时为 `C:\Users\<username>\KoderKnowledge`） |
| macOS / Linux | `~/KoderKnowledge` |

`--root` 或 `KODER_KNOWLEDGE_ROOT` 可改路径；换路径不迁移旧库。

---

## 渠道与文件（简述）

运行中的宿主可让多个已连接应用访问同一本地库。宿主须认证入站消息并将已关联账号映射到验证身份。`reader` 可检索，`writer` 可新增与导入；仅所有者能改授权、删除、替代事实或渲染完整库。知识访问不授予执行电脑任务或给新收件人发文件的权限。

UTF-8 / GB18030 文字可直接索引。PDF、Office、图片可归档，可搜索文本需宿主解析或 OCR。`attachment_only` 表示只存了原文件。默认每文件 32 MiB、每条 256K 字符。检索用关键词与中文片段——**不含向量搜索**。

连接托管模型或共享渠道前请读[隐私说明](docs/privacy.md)（英文正文；教程含中文要点）。

---

## 文档

| 文档 | 用途 |
| --- | --- |
| [中文教程](docs/tutorial.zh-CN.md) · [English](docs/tutorial.en.md) | 下载、第一次保存/检索、排查、升级、卸载 |
| [技能规则](koder-personal-knowledge/SKILL.md) · [命令参考](koder-personal-knowledge/references/commands.md) · [宿主接入](koder-personal-knowledge/references/host-integration.md) | 技能与工具 |
| [架构](docs/architecture.md) · [隐私](docs/privacy.md) · [FAQ](docs/faq.md) · [验证](docs/validation.md) | 边界与证据 |

技术参考目前以英文为主；中文产品、练习路径与限制以本页和中文教程为准。

---

## 项目状态

本地存储与检索已实现。本地套件在 **macOS 上 27 项测试通过**（含并发子进程写入），见[验证](docs/validation.md)。Windows/Linux 原生、真实渠道往返、自动宿主触发、外部 PDF/Office/OCR 需另行验收。本版**没有**云同步层或多电脑写入协议。

```sh
python3 -B -m unittest discover -s tests -v
```

---

## 常见问题

### 这是聊天机器人或模型吗？

不是。这是可移植技能加本地知识工具；模型、界面、身份与消息连接由宿主提供。

### 会改模型权重吗？

不会。这里的「学习」指可检查记录与事后检索。

### 手机能用电脑上的知识吗？

在宿主**正在运行**且渠道适配器已接通时可以。本仓库本身不提供远程访问或应用登录。

### 多台电脑同步吗？

本版没有。不要用普通云盘同步正在多机写入的 SQLite。

### 软可发现性

与仓库实质相符的检索表述：**智能体本地个人知识库**、**SQLite 笔记与参考资料库**、**有限检索替代整段聊天历史**、**带来源的可更正记忆**、**已验证身份的共享知识空间**。避免堆砌关键词。

---

## 许可与联系

[MIT](LICENSE)，保留 [NOTICE](NOTICE)。例子与测试中的人物、事件、消息和文件均为合成数据。

[GitHub Issues](https://github.com/KarmenLoop/koder-personal-knowledge/issues) · [SUPPORT.md](SUPPORT.md) · [SECURITY.md](SECURITY.md)。私人资料和凭据不要提交到公开问题。
