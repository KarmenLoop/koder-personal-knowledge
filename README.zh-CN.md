# Koder Personal Knowledge

[English](README.md) | 简体中文

把智能体的笔记与参考文件放进本地资料库：查找偏好、定位原文或更正旧事实，无须把所有历史对话塞进模型上下文。

项目由 [KarmenLoop](https://github.com/KarmenLoop) 为 Koder 开发，包含可移植技能和一个小型 Python 工具，其他宿主也可接入。[下载](https://github.com/KarmenLoop/koder-personal-knowledge/releases) · [许可](LICENSE) · [支持（英文）](SUPPORT.md)

## 资料如何保存

库里保存带来源的小记录，以及用户主动加入的文件副本。搜索只返回少量相关摘录；可以浏览、更正、归档或删除。宿主若已连接多个消息渠道，可让它们在同一台电脑访问已验证空间，但账号绑定和消息投递由宿主负责。

存储工具不发网络请求。宿主可能把检索内容发给自己配置的模型，请先阅读[隐私与数据处理（英文）](docs/privacy.md)。

## 功能

| 能力 | 行为 |
| --- | --- |
| 日常记录 | 保存明确、长期有用的偏好与事实，无需先完成长问卷 |
| 个人上下文 | 分类保存资料、习惯、关系、工具、工作、行业和生活内容 |
| 参考文件 | 管理所选文件副本，保留原名、来源与 SHA-256 |
| 有限检索 | 返回本地文本的限定摘录，不默认发送整个库 |
| 事实与推断 | 行为推断在用户确认前保持未确认 |
| 更正历史 | 新事实替代旧记录，同时保留来源与被替代状态 |
| 可检查视图 | 本地 HTML、逐条 Markdown 与完整 JSON 目录 |
| 共享空间 | 所有者向已验证用户或群组授予读取或贡献权限 |
| 本地写入 | SQLite 事务、原子替换、事件去重与有界锁等待 |
| 遗忘 | 删除记录与不再引用的文件，刷新视图并拦截已删事件重试 |

八类分别是个人资料、习惯偏好、人物关系、工具、工作职业、行业知识、日常生活、参考资料。空库即可使用，无须先“填满”。

## 宿主与身份边界

每条记录保留来源、可用的说话者信息、时间与状态。宿主决定对话属于哪个身份和空间，同名账号不能直接合并。

技能规定何时检索与保存，自动触发取决于宿主的技能选择和消息流程。导入 Markdown 不会创建后台进程或登录消息账号。

## 下载与安装

从[发行页](https://github.com/KarmenLoop/koder-personal-knowledge/releases)取得完整技能 ZIP；要源码和测试，可选择 **Code → Download ZIP** 或：

```sh
git clone https://github.com/KarmenLoop/koder-personal-knowledge.git
cd koder-personal-knowledge
```

保持整个 `koder-personal-knowledge/` 技能目录完整，其中的脚本和参考文档都需要保留。

1. 用宿主安装器导入完整目录，或放到宿主配置的技能目录。
2. 通过受控的本地工具提供随包 Python 脚本。
3. 每次调用由宿主提供固定库根目录、已验证身份和空间。
4. 启用宿主技能选择；若需每轮学习，还要在消息流程接入检索和保存。

运行时只需 Python 标准库，不包含桌面安装器、模型包或消息账号登录服务。

## 第一次保存与检索

要求 **Python 3.9+** 及其标准 `sqlite3`。在仓库根目录运行，Windows 可用 `python` 替换 `python3`。例子使用隔离目录和合成所有者 `local-owner`；生产宿主应提供稳定、已验证的真实身份。

```sh
# Inspect the platform's default location without creating anything.
python3 koder-personal-knowledge/scripts/knowledge.py path

# Create a separate library for this walkthrough.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge init --owner local-owner

# Save an example preference with its source.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  remember --record examples/preference.json

# Retrieve the preference within a small response budget.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  search "summary" --max-chars 2000

# Archive a selected text file and its contents.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner \
  import-file --file examples/field-notes.txt --source examples/file-source.json

# Rebuild the local views and print their location.
python3 koder-personal-knowledge/scripts/knowledge.py \
  --root ./demo-knowledge --principal local-owner render
```

浏览器打开 `demo-knowledge/views/index.html`。它离线可用，但包含完整库，应留在所有者电脑上。

PowerShell 使用单行命令：

```powershell
$Script = ".\koder-personal-knowledge\scripts\knowledge.py"
python $Script --root .\demo-knowledge init --owner local-owner
python $Script --root .\demo-knowledge --principal local-owner remember --record .\examples\preference.json
python $Script --root .\demo-knowledge --principal local-owner search "summary" --max-chars 2000
python $Script --root .\demo-knowledge --principal local-owner import-file --file .\examples\field-notes.txt --source .\examples\file-source.json
python $Script --root .\demo-knowledge --principal local-owner render
```

更正、共享、默认值与错误处理见[命令参考（英文）](koder-personal-knowledge/references/commands.md)。

### 查看规模

只统计可访问记录，不返回笔记正文：

```sh
python3 koder-personal-knowledge/scripts/knowledge.py --root ./demo-knowledge --principal local-owner stats
```

结果按类别与状态分组，并统计附件。`stats` 前加 `--space SPACE_ID` 查看共享空间，仍按相同身份和空间权限限制。

### 默认位置

| 系统 | 默认根目录 |
| --- | --- |
| 有 D: 盘的 Windows | `D:\KoderKnowledge` |
| 无 D: 的 Windows | C: 用户资料目录内的 `KoderKnowledge`；资料目录重定向时为 `C:\Users\<username>\KoderKnowledge` |
| macOS/Linux | `~/KoderKnowledge` |

`--root` 或 `KODER_KNOWLEDGE_ROOT` 可指定其他位置。初始化后宿主应保存绝对路径；切换路径不迁移旧库，D: 不可写会报错而不偷偷另建库。

## 渠道与群组

一个运行中的宿主可以让多个已连接应用访问同一个本地库。宿主必须认证入站消息，将已关联账号映射到验证身份；所有者可共享空间给已验证的群组身份，其他私人空间保持独立。

`reader` 可检索，`writer` 还可新增记录和导入文件。只有所有者能改授权、删除、替代事实或渲染完整库。知识访问不授予执行任务或给新收件人发文件的权限。

[宿主接入契约（英文）](koder-personal-knowledge/references/host-integration.md)列出输入与检查。本项目没有微信、企业微信或飞书登录适配器，远程请求还要求电脑和宿主运行且可达。

## 文件与搜索

UTF-8、GB18030 文字可直接索引，含 Markdown、CSV、JSON、日志、YAML、XML、HTML。原文件以不执行的 `.bin` 保存，原名保留在元数据和下载链接中。

PDF、Office、图片等可归档，但可搜索文本需由宿主解析或 OCR 提供。`attachment_only` 表示只存了原文件，不代表正文可检索。默认每个原文件 32 MiB、每条记录 256K 字符，较大材料需拆分或由宿主管理。检索使用关键词与中文片段，不含向量搜索。

## 文档与验证

- [技能规则](koder-personal-knowledge/SKILL.md) · [命令参考](koder-personal-knowledge/references/commands.md) · [宿主接入](koder-personal-knowledge/references/host-integration.md)
- [架构](docs/architecture.md) · [隐私](docs/privacy.md) · [常见问题](docs/faq.md) · [验证](docs/validation.md)

以上技术参考保留英文原文。完整中文入门流程见本页，英文对应流程见[英文首页](README.md)。

```sh
python3 -B -m unittest discover -s tests -v
```

测试使用临时目录和合成数据，包含多语种检索；不会打开个人库、连接消息账号或调用付费 API。现有记录为 macOS 27 项本地测试通过，含并发子进程写入，不能据此声称 Windows/Linux 原生或托管 CI 已验收。真实渠道、自动宿主触发、PDF/Office/OCR、云同步和多电脑写入协议需分别验证，本版没有后两种同步层。

## 更新、回退与移除

更新前保留库的完整备份，并核对 [CHANGELOG.md](CHANGELOG.md) 与对应版本说明；不要只复制运行中的 SQLite 主文件。升级或回退先在副本验证，改变 `--root` 不能代替迁移。移除技能不会自动删除外部知识库；需要遗忘内容时由所有者使用命令参考中的删除流程，再核对生成视图和保留的备份。

## 贡献、许可与归属

贡献见 [CONTRIBUTING.md](CONTRIBUTING.md) 与 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)，求助见 [SUPPORT.md](SUPPORT.md)，敏感报告见 [SECURITY.md](SECURITY.md)。私人资料和凭据不要提交到公开问题。

采用 [MIT](LICENSE)，可按原条款使用、修改、再分发与商业使用，保留 [NOTICE](NOTICE)。项目依赖 Python 标准库及 SQLite，沿用完整 `SKILL.md` 目录模式，知识库与宿主身份/执行系统分开。例子中的人物、事件、消息和文件均为合成数据。
