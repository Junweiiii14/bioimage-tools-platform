# 可选工具装配与重启设置

普通入口仍为 `python -m bioimage_app`。首页“工具启用设置”显示 WB、核分割、BCA 的本次启动状态；更改复选框后退出并重新启动生效。运行中的工具不会卸载或中断。未安装工具保留准备说明，已停用工具明确标注；核分割工具已启用但没有独立运行环境/模型时，仍进入原有准备说明。

维护者在**单独环境**安装同一候选的 wheel 与锁定依赖：`bioimage-app` 只包含平台和桌面依赖，`bioimage-app[wb]`、`bioimage-app[nuclei]`、`bioimage-app[bca]` 分别选择实验包；三工具用 `bioimage-app[wb,nuclei,bca]`。仓库开发命令 `uv sync --locked --all-groups` 保持当前三工具装配。具体 wheel 必须来自同一已验证候选，本项目没有在线工具市场或自动安装器。

本仓库可复验的隔离安装方式见 `tooling/installed_wheels.py`：用新 venv、`UV_PROJECT_ENVIRONMENT=<新环境>`、`uv sync --locked --package bioimage-app --no-dev --no-install-workspace`（按需添加 `--extra wb` / `--extra nuclei` / `--extra bca`），再 `uv pip install --python <新环境python> --no-deps <本次构建的contracts/runtime/app及所选工具wheel>`。依赖版本沿 `uv.lock`，没有升级。

停用只控制桌面本次会话装配，不是操作系统安全隔离，也不禁止维护者直接调用已安装工具的 CLI。仅注册代码中已知的三个工具，不从项目、模板或工作区读取 Python 模块名执行。安装/移除由维护者在隔离环境使用既有包管理；这里不卸载用户在用安装。

缺失或停用的工具不能新建、执行或通过编排入口运行其历史项目，界面解释具体原因；其原始文件、草稿资产和已提交结果保留。恢复同一受支持工具并重启后可再次打开。研究工具的固定方法、参数、数据格式和结果校验不变；没有热插拔、跨实验任意串联或 Agent。

桌面自身仍需要 PySide6/QtWebEngine；核分割的 TensorFlow/StarDist 与模型继续放在既有固定隔离 worker 中。真实磁盘/时间、实际矩阵和未验范围见 [P022证据](../../work/evidence/P-022/README.md)，不能以源码行数推断轻量。科学、真人、物理 DPI、目标机和用户安装更新不由装配验收代替。
