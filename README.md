# Hcode

[![CI](https://github.com/PooooLish/Hcode/actions/workflows/ci.yml/badge.svg)](https://github.com/PooooLish/Hcode/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Hcode 是一个使用 Python 和 Textual 构建的终端编码 Agent。它可以读取与修改代码、执行命令、调用 MCP 工具，并通过权限模式、上下文压缩、会话恢复和子 Agent 协作完成仓库级开发任务。

> 当前版本：`0.2.0` 开发预览版。项目尚未完成安全加固，不应在无人监督的生产环境中执行不受信任的任务。

## 核心能力

- Textual Terminal UI，支持文件引用、命令补全、状态展示和响应取消。
- Anthropic、OpenAI 及 OpenAI-compatible 模型协议。
- 读取、搜索、编辑、命令执行、差异查看和工作树工具。
- Default、Accept Edits、Plan、Bypass Permissions 四种权限模式。
- MCP、Hooks、Skills、Memory、Session 和 Remote 扩展机制。
- 子 Agent、团队任务、消息传递和验证 Agent。
- 长上下文预算、自动压缩、工具结果清理和会话恢复。

## 快速开始

要求 Python 3.11 或更高版本。推荐为项目创建独立环境：

```powershell
conda create -n hcode python=3.11 -y
conda activate hcode
python -m pip install -e .
```

创建本地配置。配置目录已被 Git 忽略：

```powershell
New-Item -ItemType Directory -Force .hcode
Copy-Item config.example.yaml .hcode/config.yaml
```

编辑 `.hcode/config.yaml`，填写实际的服务地址和模型名。密钥只通过环境变量注入，不要写入配置文件：

```powershell
$env:OPENAI_API_KEY = '<your-api-key>'
python -B -m hcode
```

协议与默认环境变量：

| 协议 | 环境变量 |
| --- | --- |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `OPENAI_API_KEY` |
| `openai-compat` | `OPENAI_API_KEY` |

## 常用操作

| 输入或快捷键 | 操作 |
| --- | --- |
| `@` | 引用项目文件 |
| `/` | 打开命令补全 |
| Enter | 发送消息 |
| Shift+Enter / Ctrl+J | 插入换行 |
| Shift+Tab | 切换权限模式 |
| Ctrl+O | 展开或折叠工具详情 |
| Escape | 关闭弹层或取消当前工作 |
| F1 | 显示快捷键帮助 |

## 测试

```powershell
python -m pip install "pytest>=9.0.3" "pytest-asyncio>=1.3.0" "pytest-timeout==2.4.0"
python -B -m pytest -q tests
```

最近一次 Windows/Python 3.11 本地验证结果为 `740 passed, 2 skipped`，GitHub Actions 的 Ubuntu 和 Windows 任务也已通过。这些测试证明当前实现的回归状态，不等同于 Agent 任务成功率；能力评测方案见 [`docs/evaluation-plan.md`](docs/evaluation-plan.md)。

## 文档

- [代码全流程解析](docs/code-flow-walkthrough.md)：按实际调用顺序理解入口、Agent 循环、模型、工具、权限、上下文和扩展系统。
- [只读代码分析](docs/read-only-code-analysis.md)：架构、依赖、风险和建议整改顺序。
- [环境与测试](docs/environment-setup.md)：本地环境、配置和测试注意事项。
- [能力评测计划](docs/evaluation-plan.md)：任务集、指标和对比实验规范。
- [贡献指南](CONTRIBUTING.md)：开发流程和提交要求。
- [安全策略](SECURITY.md)：安全边界、已知限制和报告方式。

## 项目结构

```text
hcode/                 主程序包
  agents/              内置 Agent 与任务管理
  context/             上下文预算和压缩
  memory/              会话与长期记忆
  permissions/         权限规则和危险操作检查
  tools/               Agent 可调用工具
  teams/               多 Agent 协作
  worktree/            Git worktree 工作流
tests/                 自动化测试
docs/                  架构、分析和操作文档
scripts/               可重复执行的辅助脚本
```

## 安全与许可证

Hcode 能够执行命令和修改文件。首次使用时请保持 `default` 权限模式，并只在受版本控制、可恢复的测试仓库中运行。Windows 当前没有操作系统级沙箱实现，详细限制见 [SECURITY.md](SECURITY.md)。

项目采用 [MIT License](LICENSE)。
