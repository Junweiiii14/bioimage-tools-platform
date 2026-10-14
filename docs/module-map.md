# 模块地图

标记“规划”的模块当前不存在；只有真实消费者和就绪任务出现时创建。

| 位置 | 职责与入口 | 状态 / 验证 |
|---|---|---|
| `dev.py`, `tooling/` | 开发检查与来源核验，不含业务算法 | 已建；`dev.py check --all` |
| `p0_probe.py`, `tooling/p0/` | T-002 可丢弃技术探针：Qt、进程、合成图和 standalone；不作为产品 API | 本机验证中；`tooling/p0/README.md` |
| `.agents/skills/` | 固定提交的第三方工作技能 | 已建；`tooling/skills-lock.json` |
| `tests/test_boundaries.py` | 边界检查的正反例 | 已建；pytest |
| `apps/desktop/` | `bioimage_app.api` 的 Qt 异步存储队列，显式宿主装配 | 已建 0.1.0；真实事件循环和隔离 wheel；进程/UI 入口待建 |
| `packages/tool_contracts/` | `tool_contracts.api` 的文件资产、修订、运行/退出与恢复契约 | 已建 v1；schema 漂移和隔离 wheel |
| `packages/platform_runtime/` | `platform_runtime.api.Workspace` 输入快照、草稿 CAS、结果事务、恢复与备份 | 已建 v1；真实文件/SQLite、崩溃/取消/损坏负例、独立 wheel |
| `packages/desktop_sdk/` | ToolView、Qt 生命周期、宿主 UI 端口 | 规划；pytest-qt |
| `packages/imaging_core/` | 原始图像、坐标和纯技术运算 | 规划；位深/几何/性质 |
| `packages/imaging_ui/` | 真实复用需求出现后的画布适配 | 规划，不预建 |
| `tools/wb/` | `wb_tool.api` 的积分/TIFF/分析/严格协议，`wb_tool.worker` 后台入口；宿主/UI 待实现 | 解析/协议/真实进程、4 import-linter、隔离 wheel |
| `tools/if_intensity/` | 第二工具验证平台边界 | 规划，WB 最小闭环后 |
| `tools/if_count/`, `tools/ihc_area/` | 各自独立的实验语义 | 后续规划 |

成员采用 `pyproject.toml + src/<import_name>/ + tests/`。公开入口 `api.py` 无初始化副作用。创建新成员须同时更新 workspace members、本地图、`tooling/boundaries.py`、import-linter 合约及 CI 的已安装包测试。不能只添加目录就宣布边界完整。

工具内部：`domain/` 纯数值与身份；`application/` 用例与端口；`adapters/` 文件/执行/导出；`ui/` view、presenter、view_state。模块 README 只记自己的 API、语义、输入输出、失败行为和命令。
