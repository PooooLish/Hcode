# Hcode Python 只读代码分析报告

## 1. 结论摘要

Hcode 0.2.0 是一个功能面已经相当完整的终端 AI 编码助手，而不是简单的
“Hello World Agent”。它包含 Textual TUI、Anthropic/OpenAI 客户端、工具调用、
权限规则、MCP、Skill、Hook、记忆/会话、子 Agent、团队协作、worktree 和远程
WebSocket UI。代码模块化程度尚可，锁文件完整，测试数量也不低。

但当前版本不适合直接暴露到不可信网络，也不建议在包含敏感文件的主机上启用
自动权限或无人值守团队模式。静态审阅确认 1 个 P0、4 个 P1 和若干 P2 问题；
其中远程模式无鉴权、`Glob/Grep` 路径沙箱绕过、只读命令误判和 Plan 模式路径
绕过都能直接削弱安全边界。

本报告只分析代码和配置，没有执行项目源码、测试或依赖安装。结论适合作为整改
基线，不等同于运行时验收或完整安全审计。

## 2. 引入与完整性

| 项目 | 结果 |
| --- | --- |
| 来源 | 用户提供的原始项目压缩包 |
| 源归档 SHA-256 | `ED54E9287BA55491C1E44017BA5C0BB24DDBFCD9D72E2FA377E88FCC52F5306F` |
| 源归档大小 | 546,843 bytes |
| ZIP 条目 | 233 |
| 解压文件 | 205 |
| 解压后原始体积 | 1,672,132 bytes |
| 路径穿越条目 | 0 |
| 符号链接条目 | 0 |
| 大小写冲突 | 0 |
| 初始逐文件哈希差异 | 0 |

引入后新增了工作区要求的 `AGENTS.md`、`project.md`、`README.md` 和 `docs/`。
原项目 `.gitignore` 仅补充了工作区生成目录及环境文件规则；`hcode/`、
`tests/`、`pyproject.toml` 和 `uv.lock` 未被修改。

## 3. 项目概况

| 维度 | 静态结果 |
| --- | --- |
| 包版本 | `0.2.0` |
| Python 要求 | `>=3.11` |
| 主包 Python 文件 | 141 |
| 测试目录 Python 文件 | 34（其中 `test_*.py` 32 个） |
| 内置 Skill Python 文件 | 10 |
| Python 文件总计 | 185 |
| AST 语法错误 | 0 |
| 静态识别测试函数 | 659（含 125 个 async 测试） |
| 锁定包记录 | 55 |
| 构建后端 | Hatchling |

直接依赖包括 Textual、Anthropic SDK、OpenAI SDK、PyYAML、Pydantic、MCP、
HTTPX 和 websockets；`uv.lock` 为制品记录了来源、哈希和平台 wheel，重现性基础
较好。

## 4. 架构梳理

### 4.1 入口与交互面

- `hcode/__main__.py`：CLI 总入口，支持 TUI、`-p` 非交互模式、远程模式和
  teammate worker 模式。
- `hcode/app.py`：Textual TUI、命令分发、权限交互、会话展示和主要组装逻辑。
- `hcode/remote.py`：HTTP + WebSocket 远程 UI 桥接。

### 4.2 Agent 主循环

- `hcode/agent.py`：流式响应、工具批处理、权限询问、Hook 事件、压缩和重试。
- `hcode/client.py`：Anthropic、OpenAI、OpenAI-compatible 三类协议适配。
- `hcode/conversation.py` 与 `hcode/context/manager.py`：消息配对、token 估算、
  上下文压缩与大工具结果落盘。

### 4.3 工具与权限

- `hcode/tools/`：读写文件、编辑、Shell、Glob/Grep、MCP、Skill、worktree、
  子任务和团队工具。
- `hcode/permissions/`：危险命令检测、规则文件、权限模式和路径沙箱。
- `hcode/sandbox/`：Linux bubblewrap 与 macOS Seatbelt；Windows 无 OS 沙箱后端。

### 4.4 扩展与持久化

- `hcode/mcp/`：stdio 与 Streamable HTTP MCP 客户端、工具包装和延迟加载。
- `hcode/skills/`：Skill 发现、解析、加载和从 GitHub 安装。
- `hcode/hooks/`：生命周期 Hook、条件和 command/http/prompt/agent action。
- `hcode/memory/`：自动记忆、召回、会话和压缩归档。
- `hcode/agents/`、`hcode/teams/`：子 Agent、团队邮箱、共享任务和多后端启动。
- `hcode/worktree/`：工作树创建、集成、清理和会话切换。

## 5. 优先发现

### P0 — 远程模式监听全部网卡且没有鉴权

证据：

- `hcode/remote.py:79-80` 默认监听 `0.0.0.0:18888`。
- `hcode/remote.py:135-140` 直接启动 WebSocket 服务，没有认证、Origin 校验或 TLS。
- `hcode/remote.py:171-215` 任意连接可发送用户消息、取消操作和权限响应。
- `hcode/remote.py:489-500` 权限请求向所有连接广播。
- `hcode/remote.py:735-749` 仅凭可预测/已广播的 `perm_id` 接受权限决定。
- `hcode/remote.py:769-779` 会话、工具参数和结果向所有连接广播。

影响：同一局域网或可达网络上的客户端可以读取会话与工具输出、注入 Agent 提示、
抢答权限请求并触发本机文件/命令工具。由于这是编码 Agent，影响可达到主机代码执行
和敏感信息泄露。

建议：默认仅绑定 `127.0.0.1`；增加启动时生成的高熵 bearer token、WebSocket
鉴权和严格 Origin 检查；权限响应绑定到发起连接；非本机访问要求 TLS/反向代理；
在鉴权完成前不要发送 cwd、命令列表或会话事件。为未授权 HTTP/WS、跨连接权限
抢答和广播隔离添加测试。

### P1 — `Glob/Grep` 用 pattern 代替 path 做沙箱检查

证据：

- `hcode/permissions/rules.py:19-26` 将 `Glob`/`Grep` 的权限内容映射为 `pattern`。
- `hcode/permissions/checker.py:115-124` 把该内容当作路径交给 `PathSandbox`。
- `hcode/tools/glob.py:15-17,27-35` 和 `hcode/tools/grep.py:16-19,29-50`
  实际使用独立的 `path` 参数决定搜索根目录。

影响：例如 `Grep(pattern="password", path="C:\\Users\\...")` 检查的是项目内名为
`password` 的伪路径，而工具会读取外部目录。默认模式下 read 类工具最终自动放行，
因此可绕过项目路径边界读取任意可访问文本。

建议：把规则匹配内容和资源访问目标分开；`Glob/Grep` 的路径沙箱必须检查
`arguments["path"]`，规则仍可单独匹配 pattern。工具实现层也应接收并强制项目根，
避免权限调度层被绕过时直接访问任意路径。补充绝对路径、`..`、symlink 和不存在
父目录的回归测试。

### P1 — “安全只读命令”白名单可执行写操作

证据：

- `hcode/permissions/dangerous.py:22-33` 把 `find`、`sed`、`tee`、`xargs`、
  `npx`、`git branch/tag/remote` 等列为安全命令。
- `hcode/permissions/dangerous.py:37-46` 只按字符串前缀判定，未检查危险选项。
- `hcode/permissions/checker.py:84-86` 在危险命令与用户规则之前直接放行。

可绕过示例包括 `sed -i`、`find . -delete`、`tee FILE`、`xargs rm`、`npx <package>`、
`git branch -D`、`git tag -d` 和 `git remote add`。即使不含管道或重定向，这些命令
也会写文件、删数据、执行程序或触发网络下载。

建议：删除 `npx`、`tee`、`xargs` 等无法可靠证明只读的入口；对 Git 和少数系统
命令采用 argv 级子命令/选项白名单；解析失败时 fail closed；规则与危险检测必须在
自动放行之前生效。为每个白名单命令添加“安全正例 + 变异写操作反例”测试。

### P1 — Plan 模式写入例外可按文件名绕过路径边界

证据：

- `hcode/permissions/checker.py:76-82` 在路径沙箱和受保护路径检查前直接放行计划
  文件写入。
- `hcode/permissions/checker.py:146-158` 除精确绝对路径外，还接受相同 basename，
  或任意包含 `.hcode/plans/` 的字符串。

影响：若真实计划文件名为 `plan.md`，任意位置的另一个 `plan.md` 都可在 Plan 模式
被写入；该提前返回还跳过 `.hcode/config.yaml` 等保护逻辑和项目路径沙箱。

建议：先执行 deny-write 与路径沙箱，再判断 Plan 例外；只允许规范化后与唯一计划
路径完全相等的目标；删除 basename 与子串兜底。增加同名外部文件、路径穿越、
Windows 分隔符和 symlink 测试。

### P1 — 无人值守入口会弱化或绕过人工权限

证据：

- `hcode/__main__.py:383-385` 的 `-p` 模式对所有 `PermissionRequest` 自动返回
  `ALLOW`，即使配置仍显示 `default`。
- `hcode/__main__.py:602-611` teammate worker 固定使用 `BYPASS`。
- `hcode/permissions/modes.py:24-28` 中 BYPASS 对 read/write/command 全部放行。

影响：脚本调用者可能误以为 default 模式仍会阻止写入；子 Agent/teammate 在没有
人类确认时可写出项目目录或执行绝大多数未命中有限黑名单的命令。Windows 上没有
可作为第二道边界的 OS 沙箱后端。

建议：`-p` 在需要询问时默认失败，并要求显式 `--yes`/危险标志才自动批准；teammate
继承或收紧 lead 的权限和路径边界，不应硬编码 BYPASS；远程、非交互和团队模式都
应显示最终生效策略并写入审计日志。

## 6. 其他重要发现

### P2 — Hook command 模板存在命令注入面

`hcode/hooks/models.py:74-82` 将 `$MESSAGE`、`$FILE_PATH` 和工具参数原样替换进
模板；`hcode/hooks/executors.py:17-24` 随后把结果交给 shell。只要 Hook 配置在
command 中引用模型可控字段，字段里的 shell 元字符就会变成命令。

建议优先支持 argv 数组和显式环境变量传参；若保留 shell 模板，必须提供可靠转义
函数并把“不可信占位符直接拼接”标为危险配置。

### P2 — Bash 非零退出码始终报告非错误

`hcode/tools/bash.py:67-81` 定义了 `_interpret_exit_code()`，但执行路径没有调用；
`hcode/tools/bash.py:168-181` 对任意非零退出码仅追加文本，最终固定
`is_error=False`。构建失败、测试失败和普通命令失败因此可能被上层当成成功工具调用。

建议对已知特殊命令保留 exit-code 语义，其余非零状态设置 `is_error=True`；增加普通
失败、grep 无匹配和 pipeline 失败测试。

### P2 — Hook agent action 是返回成功的占位实现

`hcode/hooks/executors.py:78-83` 对 agent action 返回 “not yet implemented”，但
`success=True`。配置和用户界面会认为动作成功，掩盖功能缺失。

建议在实现前返回明确错误，或从允许的 Hook action 类型中移除。

### P2 — 示例配置鼓励把 API key 写入文件

`.hcode/config.yaml.example:5,13` 使用 `"your-api-key-here"` 占位，而项目实际支持
环境变量解析。虽然 `.gitignore` 忽略真实 `config.yaml`，复制后填入密钥仍增加泄露
风险。

建议示例默认写 `${ANTHROPIC_API_KEY}` / `${OPENAI_API_KEY}`，并在启动时拒绝明显
占位符。此次只报文件名的常见凭据特征扫描未发现明显真实私钥或长 token。

### P3 — 发布与维护元数据不足

- `pyproject.toml` 没有项目许可证、作者、主页、分类器或 README 元数据。
- 导入时源文件普遍带有重复来源/推广网站注释；这些纯注释广告头已于
  2026-08-31 从 `hcode/` 和 `tests/` 清除。项目根仍没有 LICENSE；内置 Skill
  各自有许可证，不代表主项目源码可再分发。
- 原 `HCODE.md` 内容很短，缺少安装、配置、安全模型、平台差异和运行示例。
- `hcode/app.py` 约 2,042 行、`hcode/agent.py` 约 1,400 行，组装、UI 和业务状态
  耦合度较高，后续改动的回归面大。

在对外发布、复制或二次分发前，应先确认源码授权和第三方归属，补齐项目许可证与
NOTICE；授权不明确时不能假定可复制或发布。

## 7. 测试与工程质量评价

积极方面：

- 测试规模较大，覆盖权限、Agent 循环、上下文、记忆、MCP、Hook、团队、worktree、
  序列化和工具行为。
- 有 `uv.lock` 和制品哈希，依赖解析可重现。
- 工具参数普遍使用 Pydantic，消息和事件多用 dataclass，边界模型清晰。
- 已实现 read-before-write 缓存、规则优先级、symlink 路径解析、工具结果溢写和上下文
  压缩等实用机制。

缺口：

- `tests/` 中没有针对 `RemoteServer`、WebSocket 鉴权或多客户端权限竞争的测试。
- 现有权限测试验证了 `Glob/Grep` 提取 pattern，却没有验证它们的 `path` 越界。
- 安全命令测试集中在少数危险正则，没有覆盖白名单命令的写入选项。
- 没有看到 CI 配置、ruff/black/mypy/coverage 配置或最低覆盖率门槛。
- 本轮未执行 pytest，因此不能声称 659 个测试通过；它们只是 AST 识别到的测试函数。

## 8. 建议整改顺序

1. 立即禁用或仅本机绑定远程模式，完成鉴权和连接隔离。
2. 修复 `Glob/Grep` 真实路径检查，并把路径限制下沉到工具实现。
3. 重做安全命令判定，删除无法证明只读的白名单项。
4. 修复 Plan 文件精确匹配和检查顺序。
5. 让 `-p` 与 teammate 采用 fail-closed 权限策略，特别是在 Windows 上。
6. 修复 Hook 参数传递与 Bash 退出码语义。
7. 为以上每项先添加回归测试，再在经批准的隔离环境中安装锁定依赖并运行 pytest。
8. 补齐 LICENSE、README、安全模型、平台支持和 CI/静态检查。

## 9. 本轮验证与限制

已执行：

- ZIP 路径穿越、符号链接、大小写碰撞和解压体积审计。
- 源归档 SHA-256 与 205 个解压文件的逐文件哈希核对。
- 185 个 Python 文件的 `ast.parse` 静态语法检查：0 个错误。
- 结构、敏感 API、权限边界、测试覆盖和明显凭据模式的只读检索。
- 工作区项目交接结构检查。

未执行：

- 未安装依赖，未 import `hcode`，未运行 CLI/TUI/远程服务器或 pytest。
- 未对 PyPI/GitHub 发起网络请求，未做 CVE、维护状态和许可证在线核验。
- 未做动态模糊测试、竞争条件测试、性能测试或跨平台运行验证。

因此，报告中的“确认问题”来自可直接追踪的代码路径；依赖安全性、测试通过率和
真实运行兼容性仍需在获得相应授权后验证。
