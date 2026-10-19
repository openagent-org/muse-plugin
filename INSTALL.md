# 安装 OpenAgent：Muse

本指南供 **Muse（muse.ai 消费者应用）** 安装、更新或修复 OpenAgent。若当前宿主不是 Muse，停止安装；不要套用 Muse Code 或其他客户端的安装方式。

用户要求安装时，按下面步骤实际完成，无需再次确认是否开始；需要用户登录或批准时使用 Muse 原生入口。仅要求阅读或审阅时不执行安装。

## 1. 在线读取安装资料

从官方 GitHub 仓库 `openagent-org/muse-plugin` 的 `rel` 分支完整下载以下十份核心文件，COS SDK 压缩归档由安装脚本按锁定清单自动补齐，无需用户上传附件或压缩包。任一文件无法读取或内容不完整时，停止并报告。

| 资料 | GitHub rel 下载地址 |
| --- | --- |
| 连接配置 | [openagent-connection.json](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/openagent-connection.json) |
| 任务路由 | [openagent-first-task-router/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-first-task-router/SKILL.md) |
| 结果交付引用 | [result-validation-and-delivery.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-first-task-router/references/result-validation-and-delivery.md) |
| 使用引导 | [openagent-guide-agent/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-guide-agent/SKILL.md) |
| 查找 Agent | [openagent-search-agent/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-search-agent/SKILL.md) |
| 执行 Agent | [openagent-run-agent/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/SKILL.md) |
| COS 上传脚本 | [openagent-run-agent/scripts/cos_upload.cjs](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/scripts/cos_upload.cjs) |
| COS 依赖锁定清单 | [openagent-run-agent/scripts/cos_sdk.lock.json](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/scripts/cos_sdk.lock.json) |
| COS SDK 归档安装脚本 | [install-vendor.py](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/install-vendor.py) |
| 查询账户 | [openagent-query-account/SKILL.md](https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-query-account/SKILL.md) |

仅使用表中的固定 HTTPS 地址。JSON 保留完整原始内容。正文为 HTML 登录/错误页、缺少内容或 Skill 的 name/description 时不得保存为技能；没有可用正文就停止并报告。五个 Skill 的 name 必须与各自目录名一致；连接 endpoint 必须为 `https://oasn-ow.haimawan.com/mcp/v1/open-agent`。

## 2. 连接 MCP 并授权

读取 Muse 当前提供的 Custom Connector 管理说明，使用真实创建或更新入口。已有 OpenAgent 或 Oasn Open Agent 连接时优先复用或修复，保留其他连接。连接 JSON 是参数资料，不是 Muse 官方 manifest，不直接导入或猜测私有 API。

按 JSON 中的名称、endpoint、scope 和元数据地址配置 **Streamable HTTP + OAuth 公有客户端**：使用 Authorization Code + PKCE S256，`token_endpoint_auth_method=none`，无需 client secret。从公开元数据发现认证端点，核对 resource 为完整 MCP URL、issuer 为 `https://oasn-ow.haimawan.com`。宿主支持自定义头时使用 JSON 中的 headers；不支持时仍须选择 OAuth，不改成匿名连接。

回调使用 Muse 本次提供的真实完整地址，不把 JSON 中的历史观察值硬编码为回调。由用户本人登录并同意，凭据保存、刷新均交给 Muse 安全组件，不写入聊天、Skill 或普通文件，不读取其他客户端 Token。

认证失败或结果未知时停止并报告，不自行重放注册、换码或刷新。若返回 `redirect_uri is not allowed`，说明回调尚未获服务端允许，需要维护者处理，不改写回调来绕过限制。

## 3. 验证工具与账户

执行 `tools/list`，读取真实工具名称和 schema，确认以下工具可用；宿主添加前缀时使用实际名称：

`openagent_search`、`openagent_run`、`openagent_user_guide`、`openagent_account_credits`、`openagent_wait_for_selection`、`openagent_progress`、`openagent_file_upload`、`openagent_stop_run`。

调用一次 `openagent_account_credits({})`。本次调用成功且没有错误，才确认授权可用；Connected、HTTP 200 或工具列表不能替代账户验证。缺少工具或调用失败时报告具体问题，不自动运行 Agent 验证安装。

## 4. 安装五个 Skills

1. 读取 Muse 当前提供的持久技能管理说明，确认真实保存和加载入口，不猜测技能目录或注册命令。
2. 分别安装五份完整 SKILL.md，保留 name、description、正文和同级目录关系；将交付引用保存在路由 Skill 的 `references/result-validation-and-delivery.md`，将 COS Node.js 脚本和依赖锁定清单分别保存在执行 Skill 的 `scripts/cos_upload.cjs`、`scripts/cos_sdk.lock.json`，两者保持同一目录。固定版本 COS Node.js SDK 及其依赖以 `scripts/cos_sdk.cjs.gz` 分发，通过下方安装脚本补齐该归档。业务上传要求 Node.js 20+；首次上传时先校验压缩包与解压后 bundle 的 SHA-256 和大小，再解压至可写的 `scripts/.cos-sdk/<归档 SHA-256>/`；后续进程校验并复用该目录，损坏时从归档重建，保留其他版本缓存。上传不搜索宿主 SDK 或 `node_modules`，不运行 `npm install`，不下载依赖。归档缺失、校验失败或缓存不可写时停止并修复插件安装。使用已验证连接的真实工具名；不能合并为一个 Skill、只保存摘要或丢弃引用、脚本、锁定清单及压缩归档。
3. 已有本来源同名 Skill 时就地更新，保留现有 `scripts/.cos-sdk/` 缓存；同名内容来自其他来源时停止覆盖。保存后逐一回读并加载，核对来源和完整内容，确认路由 Skill 能读取交付引用并转交其他四个 Skills。下载文件、当前对话阅读或普通记忆都不算持久安装。
4. 五个新 Skills 验证成功后，才通过真实技能管理入口停用或移除本来源旧的单个 `openagent` Skill。无法确认来源或无法停用时报告状态，保留其他技能、MCP 连接器和用户文件。

在本节第 2 步保存执行 Skill 后，使用 Python 3.9+ 运行已下载的 `install-vendor.py` 一次。将两个路径替换为下载脚本和真实持久执行 Skill 的绝对路径；不知道目标目录时停止，不猜测路径：

```bash
python3 -I -S '<install-vendor.py 的真实绝对路径>' --scripts-dir '<openagent-run-agent/scripts 的真实绝对路径>'
```

安装脚本只从固定 GitHub `rel` 地址 `https://raw.githubusercontent.com/openagent-org/muse-plugin/rel/skills/openagent-run-agent/scripts/cos_sdk.cjs.gz` 下载归档，核对锁定清单中的压缩包与解压后 bundle 的 SHA-256 和大小后原子写入；已有内容相同则复用，保留解压缓存及其他文件。必须返回 `SDK_ARCHIVE_READY` 后再完成 Skill 安装验收。此脚本仅在安装或更新时执行，业务上传不调用它；首次上传时才写入解压缓存。更新时保留未核验的旧 Python 脚本和归档，不按文件名删除。

若没有可确认的持久技能入口，明确报告“MCP 已连接，Skill 持久安装未完成”，不要宣称以后会话自动生效。

## 5. 完成安装

简短报告 MCP 连接、账户验证、五个 Skills 保存与加载的实际结果；有缺项就说明尚未完成。未验证新会话自动加载时标记“新会话待验证”，不把当前会话成功当作跨会话验证。

用户已有指定 Agent 或业务需求时，保留名称、ID 和原需求，交给对应 Skill 继续；没有业务需求时提供一句使用示例即可，例如“用 OpenAgent 帮我查找旅行规划 Agent”。不要为安装验收自动执行收费任务。
