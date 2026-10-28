# 模块地图

本页是按修改范围选择源码与契约的索引。当前任务从 [AGENT_HANDOFF](../AGENT_HANDOFF.md) 进入；验收和交付状态在任务/证据中，包版本在各自 `pyproject.toml`，不由目录存在或本页描述推出通过。

| 范围 | 职责与入口 | 修改前按需读取 |
| --- | --- | --- |
| `dev.py`、`tooling/`、`.github/` | 开发检查、来源/边界、构建与验收工具；不含实验算法 | [开发命令](runbooks/development.md)、[规则回执](runbooks/rule-enforcement.md)、[发行入口](runbooks/release.md)；相关工具锁与测试 |
| `apps/desktop/` | 异步存储、运行/取消/关闭、WB 宿主、网页桥接及本机入口 | [模块 README](../apps/desktop/README.md)、[工作台修订](contracts/wb-workbench-revision-v1.md)、[安装诊断](contracts/wb-installed-diagnostics-v1.md) |
| `tools/wb/` | `wb_tool.api`；WB 数值、用例、输入/输出适配及可选 Qt 视图 | [模块 README](../tools/wb/README.md)、下方当前流程契约；外部不得导入内部实现 |
| `packages/tool_contracts/` | `tool_contracts.api`；文件资产、修订、运行/退出与恢复消息 | [模块 README](../packages/tool_contracts/README.md) 和公开 `api.py` |
| `packages/platform_runtime/` | `platform_runtime.api.Workspace`；输入快照、草稿 CAS、结果事务、恢复与备份 | [模块 README](../packages/platform_runtime/README.md)、[架构](architecture.md)；不含 WB 实验特判 |
| `tests/`、各包 `tests/` | 行为、类型/导入边界、隔离 wheel 与真实 UI 回归 | 受影响用例和反向依赖；已有全门禁仍执行 |
| `p0_probe.py`、`tooling/p0/` | T-002 可丢弃合成技术探针，不是产品 API 或产品验收替代 | [探针 README](../tooling/p0/README.md)、原任务的未验事项 |
| `.agents/skills/` | 固定来源的第三方工作说明 | `tooling/skills-lock.json` 及适用 SKILL；升级独立审查 |

当前日常入口为 `python -m bioimage_app` → `desktop_entry.py` → `WebWorkbenchWindow`。历史 `--figure-project` / `--platform` 同样进入工作台；旧 `PlatformWindow` / `FigureProjectWindow` / `WBWindow` 保留显式兼容入口，不替代当前产品验收。Windows `Start-BioImage.ps1` 固定自身检出目录；门禁默认离屏，不能把旧测试窗口当产品演示。

## WB 当前流程与契约

- 定量与输入：`domain/lanes.py` / `quantify.py`、`application/fig_quant.py`、`adapters/tiff_input.py`；[Fig 定量](contracts/wb-fig-quant-v1.md)、[TIFF 资源准入](contracts/wb-tiff-resource-admission-v1.md)。原图与显示副本分离，科学定义和失败语义不得因界面重构改变。
- 仪器导入与分组：`instrument_intake`、`intake_grouping`、`intake_revision`；[导入清单](contracts/wb-instrument-intake-v1.md)、[采集分组](contracts/wb-intake-grouping-v1.md)、[执行后分组修订](contracts/wb-intake-group-revision-v1.md)。保留原始来源及人工确认，不从名称推断实验对应。
- 执行与裁图：`intake_workflow`、`intake_crop`、`prominent_band_geometry`；[全批裁剪门槛 @5](contracts/wb-intake-workflow-v5.md)、[明显主行裁图 @5](contracts/wb-prominent-band-crop-v5.md)。旧版本只能按明确继续/重试路径迁移，历史不静默重写。
- 成图、测量与输出：`intake_figure`、`intake_output`、`intake_supervision`、`intake_delivery`；[完整 Fig](contracts/wb-intake-figure-v1.md)、[身份输出](contracts/wb-intake-output-v1.md)、[批次复核/schema15](contracts/wb-intake-supervision-v1.md)、[完整交付](contracts/wb-intake-delivery-v1.md)。schema1–15 兼容与继续执行边界由对应契约和回归约束，已提交结果不得重算冒充旧证据。
- 元信息/OCR/归一化/导出：`project_metadata`、`project_ocr`、`project_normalization`、`workbench_revision`；[工作台修订](contracts/wb-workbench-revision-v1.md)、[归档](contracts/wb-project-archive-v2.md)、[恢复](contracts/wb-project-restore-v1.md)、[原位置回存](contracts/wb-crop-return-v1.md)。网页只消费桥接投影，持久化沿用宿主 CAS。

成员采用 `pyproject.toml + src/<import_name>/ + tests/`，公开 `api.py` 无初始化副作用。工具内 `domain/` 为纯数值与身份，`application/` 为用例与端口，`adapters/` 为 I/O，`ui/` 为视图与交互。新增产品包必须补 workspace members、本地图、`tooling/boundaries.py`、import-linter 和独立 wheel 安装测试，不能只添目录。

`desktop_sdk`、`imaging_core`、`imaging_ui`、IF/IHC 等旧规划不表示已实现或当前授权；只有真实复用需求和明确任务才创建。逐阶段演进与旧版本描述完整保留在 [整理前模块地图](archive/module-map-before-T082.md)，查历史兼容原因时再读。
