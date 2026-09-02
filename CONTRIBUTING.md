# Contributing to Hcode

## 开始之前

1. 阅读 `AGENTS.md`、`README.md` 和 `project.md`。
2. 不要读取、提交或在测试输出中打印真实密钥和私有数据。
3. 将改动限制在一个清晰目标内；涉及行为变更时先补充失败测试。

## 开发环境

```powershell
conda create -n hcode python=3.11 -y
conda activate hcode
python -m pip install -e .
python -m pip install "pytest>=9.0.3" "pytest-asyncio>=1.3.0" "pytest-timeout==2.4.0"
```

## 验证

先运行与修改相关的聚焦测试，再运行完整活动测试集：

```powershell
python -B -m pytest -q tests/test_<area>.py
python -B -m pytest -q tests
python -m pip check
python -B -m hcode --help
```

涉及真实模型或外部服务的测试必须使用专用测试账号和最小权限凭据，并在提交说明中明确费用、范围和脱敏方式。

## 提交与 Pull Request

- commit message 使用英文、祈使语气并保持单一职责，例如 `fix: emit StreamEnd after usage-only chunk`。
- Pull Request 描述必须包含目的、行为影响、验证命令、结果和剩余风险。
- 不提交 `.hcode/`、`.env*`、日志、缓存、测试输出或生成文件。
- 新增第三方依赖或 GitHub Action 时，记录来源、许可证、安全信息、版本固定方式和回滚路径。
