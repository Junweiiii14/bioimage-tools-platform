# 开发环境验收记录

日期：2026-10-13；范围：代码治理与依赖环境，产品开发尚未启动。

## 主机与 Codex

| 项目 | 实际结果 |
|---|---|
| OS | Windows 11 家庭版中文版，10.0.26200，x64 |
| CPU / RAM | Intel Core Ultra 7 255HX，20 逻辑处理器；约 15.4 GiB RAM |
| 初始可用磁盘 | C 盘约 181 GiB；安装后实际以系统为准 |
| PowerShell | 7.6.5 |
| Git / gh | 2.55.0.windows.2 / 2.96.0 |
| Node | 26.7.0，已有，仅供工具使用，不是产品运行依赖 |
| Codex 桌面 | 26.1007.21434，build 13901，prod；内置更新检查 up_to_date |
| Codex CLI | 应用随附 0.162.0-alpha.17.2；ChatGPT 登录有效 |
| Codex 项目配置 | medium 推理默认；TOML/CLI 读取成功，未改用户选定模型或权限 |
| GitHub | Junweiiii14 身份重新授权；repo/workflow scopes；私有库创建与推送成功 |
| GitHub rulesets | API 403：当前套餐不支持私有仓库 rulesets；未强制生效 |

## 安装与锁定

uv 0.13.0 通过 WinGet 用户级安装；安装包 SHA256 校验成功，来源 Astral 官方 release。Python 3.12.14 的 uv 管理安装已存在并被实际验证，不是系统 Windows Store 别名。仓库 `.venv` 隔离环境由锁文件同步。

核心版本：Ruff 0.17.0、Pyright 1.1.414、pytest 9.1.1、import-linter 2.15、Hypothesis 6.169.0、pre-commit 4.7.0、pip-audit 2.10.1、pytest-qt 4.5.0、PySide6 6.12.0、NumPy 2.5.4、SciPy 1.18.1、Pillow 12.3.0、tifffile 2026.9.20、Pydantic 2.14.1、Nuitka 4.3。完整传递依赖和哈希见 uv.lock。

PySide6 元包当前会安装额外 Qt 组件（包括 WebEngine），这不代表产品采用 Web UI。P0 按实际模块裁剪发布包并验证许可/插件，不把开发环境全部打进产品。

5 个新增技能安装在项目 `.agents/skills`；名称/描述/frontmatter 解析通过，2 个附带 Python 脚本语法解析通过，全部树摘要核验通过；业务工作流尚无真实 PR/产品代码可做完整测试。

## 已执行检查

| 检查 | 结果 | 意义与限制 |
|---|---|---|
| `dev.py doctor` | 通过 | 精确 Python 与基本工具版本可用 |
| `dev.py check --all` | 通过 | Ruff、格式、Pyright strict 0 错误、13 个 pytest 成功 |
| 直接依赖违规反例 | 9 个拒绝案例通过 | 含 Qt、跨 API、相对导入、平台依赖工具与动态导入 |
| 合法依赖正例 | 4 个通过 | 不把所有导入一律拒绝 |
| 原始 PDF SHA256 | 一致 | `b1d20b1f9ecc08ca6d7531a1ca35cce33f8fec5f4a982f61d207ab3d0010de49` |
| Qt offscreen 控件 | 通过 | 不证明真实桌面 DPI、交互响应或打包 |
| QProcess 启动子 Python | 通过 | 不证明产品 IPC、取消竞态或进程树清理 |
| 中文路径 uint16 TIFF 往返 | 通过 | 64×64 合成数组、dtype 与全部像素相同 |
| pip-audit | 67 个包，0 已知漏洞 | 此时数据库结果；不是安全认证 |
| TOML/YAML | 解析通过 | YAML 语法检查不等于 GitHub 服务端接受，需 CI 实测 |
| pre-commit | hook 已安装 | 本地可绕过，不替代服务器分支保护 |
| C/C++ 编译器 | 正在环境探针中安装/验证 | 结果在收尾证据中更新 |
| GitHub CI | 配置已准备，待首次分支推送执行 | 不提前标记远程成功 |

## 已发现并处理的问题

- GitHub 旧凭据失效：用户完成设备授权，已恢复；Actions 的 workflow scope 另行补齐。
- Skills 目录 API 返回 403：改用公开 Git 克隆读取目录及固定 SHA 安装。
- 最初 PDF 提取使用系统编码失败：明确 UTF-8 重新读取；没有修改 PDF。
- 首轮 Ruff/类型检查发现真实问题：修正嵌套判断与 AST 行号类型，未降低规则，复跑通过。
- Nuitka/SCons 在 Codex 精简环境缺少 `PROCESSOR_ARCHITECTURE`：仅对已验证 x64 编译探针补齐进程环境，不修改全局变量。直接 MSVC 未发现，使用 Nuitka 支持的 MinGW64 下载。

## 仍未证明的能力

原方案 P0：真实 DPI、ROI 拖动、交互 p95、4096² 样本/20 图批次内存、业务 worker 取消/崩溃恢复、Qt standalone 目录包以及无 Python 干净机。这些仍需就绪产品任务，不能由本次环境烟测代替。

独立审查、冷启动会话验收、全部历史 schema 兼容、科学参考样本正确性与长期无故障没有完成或无法由单次检查保证。公开文档和工具可用也不证明当前账户拥有所有模型/服务额度。
