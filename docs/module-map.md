# 模块地图

标记“规划”的模块当前不存在；只有真实消费者和就绪任务出现时创建。

| 位置 | 职责与入口 | 状态 / 验证 |
|---|---|---|
| `dev.py`, `tooling/` | 开发检查与来源核验，不含业务算法 | 已建；`dev.py check --all` |
| `.agents/skills/` | 固定提交的第三方工作技能 | 已建；`tooling/skills-lock.json` |
| `tests/test_boundaries.py` | 边界检查的正反例 | 已建；pytest |
| `apps/` | 一个应用包的 desktop / worker 两入口，显式装配 | 规划；P0 决定打包方式 |
| `packages/tool_contracts/` | 请求、结果、资产、错误与窄端口，`tool_contracts.api` | 规划；契约/兼容测试 |
| `packages/platform_runtime/` | 状态机、文件资产、SQLite 元数据、配置和日志 | 规划；故障注入/集成 |
| `packages/desktop_sdk/` | ToolView、Qt 生命周期、宿主 UI 端口 | 规划；pytest-qt |
| `packages/imaging_core/` | 原始图像、坐标和纯技术运算 | 规划；位深/几何/性质 |
| `packages/imaging_ui/` | 真实复用需求出现后的画布适配 | 规划，不预建 |
| `tools/wb/` | WB 自有领域、用例、适配和 UI | 规划；解析积分和参考集 |
| `tools/if_intensity/` | 第二工具验证平台边界 | 规划，WB 最小闭环后 |
| `tools/if_count/`, `tools/ihc_area/` | 各自独立的实验语义 | 后续规划 |

成员采用 `pyproject.toml + src/<import_name>/ + tests/`。公开入口 `api.py` 无初始化副作用。创建新成员须同时更新 workspace members、本地图、`tooling/boundaries.py`、import-linter 合约及 CI 的已安装包测试。不能只添加目录就宣布边界完整。

工具内部：`domain/` 纯数值与身份；`application/` 用例与端口；`adapters/` 文件/执行/导出；`ui/` view、presenter、view_state。模块 README 只记自己的 API、语义、输入输出、失败行为和命令。
