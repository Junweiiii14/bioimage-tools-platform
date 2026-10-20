# 开发环境重建与诊断

## 安装与入口

Windows 原生 PowerShell＋Git；无需 Docker/WSL。安装 [uv 官方 WinGet 包](https://github.com/astral-sh/uv)：

```powershell
winget install --id astral-sh.uv --version 0.13.0 --exact --source winget --scope user
```

重新打开终端，使用户 PATH 生效。根 `.python-version` 固定 3.12.14，`uv.lock` 固定依赖。项目不依赖 Codex 自带 Python，系统 `python` 商店别名也不会用于本项目。

```powershell
uv sync --locked --all-groups
uv run --locked --no-sync python dev.py doctor
uv run --locked --no-sync python dev.py check --all
uv run --locked --no-sync python dev.py smoke-env
uv run --locked --no-sync pre-commit install
```

默认 dev 组用于检查。desktop 组安装 Qt、图像/科学计算和 pytest-qt；build 组准备 Nuitka。`uv run` 默认会同步默认组；要保持额外组，显式加 `--group desktop` 或使用已完整同步环境的 `uv run --no-sync`。不要以运行检查后额外依赖被移除误判为损坏。

## 命令职责

本地 `check --all` 的 pytest 与隔离 wheel Qt 验证强制使用 `offscreen`，与 CI 的
Qt 平台一致；未跳过兼容界面或改变测试断言。直接 pytest 也默认离屏，只有显式设置
`QT_QPA_PLATFORM=windows` 才用于可见的交互诊断。测试期间不得把遗留窗口当作当前产品
工作台展示。日常产品入口为 `Start-BioImage.ps1` 或 `python -m bioimage_app`，两者均进入
当前绿色工作台；保留旧检出目录时不要在其中启动日常产品。

| 命令 | 已实现范围 |
|---|---|
| `doctor` | Python 精确版本、基本检查工具版本 |
| `policy` | PDF 摘要、AGENTS 大小、技能来源树摘要、已有产品路径的直接导入边界 |
| `check --all` | policy＋Ruff＋format＋Pyright strict＋当前所有 pytest；任一非零即失败 |
| `smoke-env` | Qt offscreen 控件、QProcess、中文路径 uint16 TIFF 原值往返和科学库导入 |
| `audit` | pip-audit 查询当前环境已知漏洞；网络失败不等价于通过 |
| `context --task <ID> --scope <目录> --record` | 输出适用规则并记录版本与范围；PR 的 rules-context 独立检查回执 |

没有产品包时不运行虚构的产品检查。当前 `context --scope` 只选择规则范围；测试范围选择、契约生成、Nuitka 产品构建和安装包冒烟在真实实现后引入。

## 首个产品包进入前

为成员建立 src、pyproject 和测试；注册 workspace 依赖与公开入口；启用 import-linter 合约、构建 wheel、隔离安装后测试。修改 root Pyright/pytest 配置以覆盖新成员，不能只在当前基础设施目录里报告全量。给 CI 增加反向依赖和包安装用例。

## 升级与恢复

在短分支更改明确版本并运行 `uv lock`、`uv sync --locked --all-groups`；提交锁文件差异，执行检查和环境烟测。主环境不能直接 `pip install -U`。锁文件必须可从干净 checkout 重建，缓存只加速、不成为隐藏依赖。

损坏的虚拟环境可在确认路径属于本仓库后移到隔离目录，再按锁重建；不要广泛删除用户目录或全局缓存。缓存/网络故障先保存诊断，检查代理、磁盘、证书与失败包，不重复盲目安装。

## GitHub

用户登录使用 `gh auth login -h github.com --git-protocol https --web`。更新 Actions 文件需要 workflow scope。只通过凭据管理器使用令牌，不写到仓库/日志。

用户已要求公开，main-quality ruleset 25008972 active；`tooling/github-ruleset.json` 为对应配置。main 必须经 PR 和四项指定 GitHub Actions 检查，禁止删除/强推，无 bypass actor。实际失败/成功验证见 F-002 证据，不以模板存在代替生效证明。

工作分支只在 PR 跑一次 CI，main 合并后再验证；删除了此前 chore 分支 push 与 PR 的重复执行。本地完整同步后使用 `--no-sync`，避免普通检查移除 desktop/build 依赖再反复安装；修改锁文件或缺包时先明确同步。

## 编译器环境探针

`uv run --locked --all-groups python -m tooling.compiler_probe` 会按 Nuitka 支持的下载方式准备 MinGW64/GCC、用两个编译任务编译一个打印字符串的探针并通过生成的启动器运行。第一次需要下载编译器；产物在 `.local/compiler-probe`，缓存默认 `~/.cache/bioimage-nuitka`。脚本只对 Windows x64 定义，不修改全局环境。

本机 gcc 15.2.0 已实际通过。源码、编译器缓存和 Python DLL 仍在开发机上，因此这不能替代 standalone Qt 和干净机验收。未来产品打包命令须另外实现。

pre-commit 使用 `--no-sync`，提交期间只检查，不改变正在使用的依赖环境；首次提交前仍需按锁文件同步。
