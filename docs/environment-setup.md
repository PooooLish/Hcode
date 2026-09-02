# 项目运行与测试环境

## 支持范围

- Python：3.11 或更高版本
- 本地验证基线：Windows、Python 3.11
- 依赖定义：`pyproject.toml`
- 解析锁文件：`uv.lock`
- 项目文件不得保存真实密钥、token 或外部服务账号

Linux 代码路径存在，但完整跨平台行为需要由 GitHub Actions 和后续人工测试确认。Windows 当前没有操作系统级沙箱实现。

## 创建环境

使用 Conda：

```powershell
conda create -n hcode python=3.11 -y
conda activate hcode
python -m pip install -e .
```

安装测试工具：

```powershell
python -m pip install "pytest>=9.0.3" "pytest-asyncio>=1.3.0" "pytest-timeout==2.4.0"
```

如果本机已经安装 uv，也可以依据现有锁文件同步环境：

```powershell
uv sync --frozen --dev
```

## Provider 配置

复制不含密钥的示例：

```powershell
New-Item -ItemType Directory -Force .hcode
Copy-Item config.example.yaml .hcode/config.yaml
```

`.hcode/` 已被 Git 忽略。修改示例中的 `base_url`、`model` 和可选的 `context_window`，不要增加真实 `api_key` 字段。

Hcode 按协议读取环境变量：

| 协议 | 环境变量 |
| --- | --- |
| `anthropic` | `ANTHROPIC_API_KEY` |
| `openai` | `OPENAI_API_KEY` |
| `openai-compat` | `OPENAI_API_KEY` |

只在当前 PowerShell 进程注入：

```powershell
$env:OPENAI_API_KEY = '<your-api-key>'
```

检查变量是否存在但不输出变量内容：

```powershell
if ([string]::IsNullOrWhiteSpace($env:OPENAI_API_KEY)) {
    throw 'OPENAI_API_KEY 未加载'
}
```

## 启动

```powershell
python -B -m hcode
```

基础检查：

```powershell
python -m pip check
python -B -m hcode --help
```

## 测试

项目指令加载逻辑会向上查找 Git 根目录和 `AGENTS.md`。请明确运行活动测试目录，并将 pytest 临时目录放在系统临时位置：

```powershell
$testRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("hcode-pytest-" + [guid]::NewGuid().ToString('N'))
$env:PYTHONDONTWRITEBYTECODE = '1'
python -B -m pytest -q tests --basetemp $testRoot
```

涉及真实模型或远程服务的测试必须获得单独授权，使用专用测试账号和最小权限凭据，并将脱敏结果写入可再生成的运行目录，而不是提交到仓库。

## 已知本地证据

- `pip check`：无损坏或缺失的依赖关系。
- CLI 帮助和核心包导入：通过。
- Windows/Python 3.11 完整活动测试集：`739 passed, 3 skipped`。
- DeepSeek 最小计费测试：返回预期文本并收到 `StreamEnd`；脱敏结果未进入仓库。

这些结果是历史本地证据。任何发布或完成声明都应重新运行对应命令。

## 测试补充依赖

`tests/test_consolidation.py` 使用 `pytest.mark.timeout(120)`，因此测试环境需要 `pytest-timeout==2.4.0`。它只用于测试，不是 Hcode 的运行时依赖。
