# CI 依赖与供应链审查

审查日期：2026-09-02

## 决策

为验证 Windows 和 Linux 上的安装、CLI 与测试行为，批准两个 GitHub 官方 Action，并固定到不可变 commit SHA。工作流仅授予 `contents: read`，checkout 不持久化仓库凭据。

| 项目 | actions/checkout | actions/setup-python |
| --- | --- | --- |
| 来源 | `github.com/actions/checkout` | `github.com/actions/setup-python` |
| 发布者 | GitHub `actions` 组织 | GitHub `actions` 组织 |
| 版本 | 7.0.1 | 7.0.0 |
| 固定 SHA | `3d3c42e5aac5ba805825da76410c181273ba90b1` | `5fda3b95a4ea91299a34e894583c3862153e4b97` |
| 许可证 | MIT | MIT |
| 运行时 | Node 24 Action | Node 24 Action |
| 仓库状态 | 活跃、未归档 | 活跃、未归档 |
| GitHub security advisories | 查询结果为空 | 查询结果为空 |

## 运行边界

- `checkout` 读取当前仓库内容；`persist-credentials: false`，不为后续步骤保留 GitHub token。
- `setup-python` 从 GitHub 托管工具缓存配置 Python；缓存缺失时可能下载运行时。
- 后续 `pip install` 会访问 Python 包索引并执行标准 Python 构建流程。
- 工作流不使用发布 token，不写 GitHub Packages，不创建 release，也不上传测试数据。

## 条件与回滚

- 决策：`approve-with-conditions`。
- 更新 Action 前重新检查上游 release、许可证、advisory 和完整 SHA。
- Python 依赖仍以 `uv.lock` 为解析基线，但当前 CI 使用 pip 安装；因此 CI 不能宣称完全锁定复现。
- 回滚方式：删除 `.github/workflows/ci.yml`；不会影响 Hcode 运行时代码。
