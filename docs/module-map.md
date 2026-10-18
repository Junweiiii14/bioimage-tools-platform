# 模块地图

T045增量：`tools/wb/application/{standalone_quant,manual_groups,fig_quant}.py`负责明确
泳道/组/版本9证据；`domain/fig_partition.py`只给几何建议；`adapters/fig_quant.py`
本地OCR与原图规划；桌面`web_manual_quant.py`绑定当前项目身份，`web_ui/manual_lanes.js`
只维护交互草稿。worker/存储沿用原闭环。状态与验收见T045，不外推完整科学验收。

标记“规划”的模块当前不存在；只有真实消费者和就绪任务出现时创建。

| 位置 | 职责与入口 | 状态 / 验证 |
|---|---|---|
| `dev.py`, `tooling/` | 开发检查与来源核验，不含业务算法 | 已建；`dev.py check --all` |
| `p0_probe.py`, `tooling/p0/` | T-002 可丢弃技术探针：Qt、进程、合成图和 standalone；不作为产品 API | 本机验证中；`tooling/p0/README.md` |
| `.agents/skills/` | 固定提交的第三方工作技能 | 已建；`tooling/skills-lock.json` |
| `tests/test_boundaries.py` | 边界检查的正反例 | 已建；pytest |
| `apps/desktop/` | 异步存储/进程、RunSession、WB窗口装配；`python -m bioimage_app`与静态wb/wb_ocr worker | 已建0.14.0；实验室分段版式、模板后台保存/导入与跨工作区字体；TIFF/PNG/OCR/ZIP恢复、定量/归一化与CSV |
| `packages/tool_contracts/` | `tool_contracts.api` 的文件资产、修订、运行/退出与恢复契约 | 已建 v1；schema 漂移和隔离 wheel |
| `packages/platform_runtime/` | `platform_runtime.api.Workspace` 输入快照、草稿 CAS、结果事务、恢复与备份 | 已建0.2.0/格式v1；新空工作区初始外来修订导入，不导入run；普通CAS与真实文件/SQLite、独立wheel |
| `packages/desktop_sdk/` | ToolView、Qt 生命周期、宿主 UI 端口 | 规划；pytest-qt |
| `packages/imaging_core/` | 原始图像、坐标和纯技术运算 | 规划；位深/几何/性质 |
| `packages/imaging_ui/` | 真实复用需求出现后的画布适配 | 规划，不预建 |
| `tools/wb/` | `wb_tool.api` 数值/单图文档v1/v2/严格协议、Qt画布/曲线/工作表、本地OCR与表格 | 已建0.19.0；schema7明确分段/原ROI逐行高度、逐源一次解码；独立模板/字体；有界ZIP历史；旧schema1–6读取及原渲染兼容 |
| `tools/if_intensity/` | 第二工具验证平台边界 | 规划，WB 最小闭环后 |
| `tools/if_count/`, `tools/ihc_area/` | 各自独立的实验语义 | 后续规划 |

成员采用 `pyproject.toml + src/<import_name>/ + tests/`。公开入口 `api.py` 无初始化副作用。创建新成员须同时更新 workspace members、本地图、`tooling/boundaries.py`、import-linter 合约及 CI 的已安装包测试。不能只添加目录就宣布边界完整。

工具内部：`domain/` 纯数值与身份；`application/` 用例与端口；`adapters/` 文件/执行/导出；`ui/` view、presenter、view_state。模块 README 只记自己的 API、语义、输入输出、失败行为和命令。

T-024 历史集成：工具平台静态注册 WB；目录导入→自动泳道/裁剪/边界→后台测量→新结果目录与可恢复ZIP。WB schema8保留机器建议来源、失败及原始积分；源图三栏和图上调整。契约见 `contracts/wb-automatic-v1.md`，状态见 `../work/tasks/T-024-platform-automation.md`。现阶段未宣称完整科学验收或第二工具完成。

当前日常桌面入口（T-043）：`python -m bioimage_app` 经 `desktop_entry.py` 打开绿色 `WebWorkbenchWindow`；历史 `--figure-project` / `--platform` 同样进入该工作台。旧 `PlatformWindow` / `FigureProjectWindow` / `WBWindow` 仅显式兼容参数使用，不能作为当前产品验收入口。Windows 的 `Start-BioImage.ps1` 固定自身检出目录；普通门禁默认离屏，不能弹出旧测试窗口作为产品演示。
