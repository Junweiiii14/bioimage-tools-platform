# P-016 单图核分割研究用户流程

<!-- PROGRAM_TASK_META {"id": "P-016", "status": "in_progress", "work_package": "W07", "depends_on": ["P-015"], "execution_root": "C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync", "owner": "Codex nuclei GUI", "base_commit": "a7612843e5216f0471b51be93bd3687f0b8dbc82", "head_commit": null} -->

## 授权与边界

2026-11-06 上游在验收 P015 后明确派发；用户授权连续执行、只读独审和验收后回传上游自动接续。P015 收尾 2b1447a 保留，仅在 bioimage-plan-sync 活动树实施。旧 dirty 树、原图、历史结果、GUI 和安装不碰。无新增发布、私有上传、外联或花费授权。

## 完成条件

1. 当前桌面工作台提供单图核分割研究入口，沿用现有设计和组件，选择一张受支持原图、运行、查看原图与原坐标实例轮廓/核数、导出、重开同一正式结果。
2. 复用 nuclei_tool.api、P015 固定方法和 WorkflowSession/Workspace；不重写算法或新增执行/存储引擎。只接受单页单通道 unsigned uint8、BlackIsZero、TopLeft TIFF，不静默转换、猜通道，不扩16bit/IF强度/全细胞/批处理。
3. 研究状态简短可见；依赖缺失提供设置入口和明确操作说明。复用设置保存环境/模型路径，不自动安装下载，正常分析无需命令。
4. 图像切换/缩放仅显示，整型标签保留可取用；导出核数/来源表与可视化图，显示图不冒充分析资产。关闭重开不重新推理，不覆盖原始输入或历史。
5. 只有完整提交才显示正式成果；新来源不被旧回复覆盖；真实零核为0，失败不为0；运行/取消/失败/重试准确，GUI不阻塞。
6. 先完成一条真实GUI公开样例流程，再据实际问题修复。核对P015已见图冻结标签/核数/来源、原图SHA、导出及重开同run。小规模回归覆盖正常、零核、缺模型、不支持输入、取消及历史保护。开发者走查不冒充学生试用；科学独立性、8bit、Linux实际模型和旧环境缺项保留。
7. 短导航和最小练习；准确提交独审、适当本地检查、正常PR和必需CI集成，不削弱门禁。回传上游实际入口/截图/检查/独审/PR/main/边界及下一最小建议，小收据随下一任务带入。

## 当前状态

已核对干净分支 codex/p016-nuclei-single-image-flow、HEAD 2b1447a；P016无重复，新goal实际已建立（无预算）。已登记任务/registry、生成并读取跨范围规则与integration回执。已接入工作台核分割入口、设置、后台原图/结果I/O、WorkflowSession、轮廓/缩放、唯一目录导出和结果重开。产品仍未完成最终验收。

## 首条真实GUI走查（2026-11-06）

在当前未提交候选上，通过 Computer Use 实际点击工作台入口、原生文件选择、开始分析、导出，退出候选进程后新进程重开。已见公开 Ganglioneuroblastoma_10.tif 得46核；标签与P014逐像素/ID一致，原图摘要不变。导出整型标签、provenance、PNG和CSV核对通过；重开同run且工作区仍只有一次run。证据见 work/evidence/P-016/first-gui-run.json；实际结果/导出在文件内记录的本机外部目录。候选窗口72364和44488均正常exit0；旧P012窗口未动。

已读/应用 Impeccable（context成功，继承当前视觉）、karpathy-guidelines、Computer Use 与 agent-handoff。首次首页入口偏低已缩为首屏可见入口；未全站改版。工具包增加只读显示适配API，算法/方法参数未改，implementation fingerprint相应变化；P015隔离worker已安装本轮实际wheel，P014历史环境未改。新增显示图不进入计算。

检查：相关Python pyright exit0；Ruff相关文件exit0；既有 nuclei/host 21 passed/3.35s，不能代替新增GUI行为验收。既有GLES/shared-context日志仍出现，未宣称根因解决。新增异常/取消/旧结果保护测试、完整门禁、独审、PR/main、短导航和最终回传均未完成。截图 .local/p016-gui-result.png（需最终证据整理），GUI事件 .local/p016-gui-events.jsonl。

## 下一步

- 针对零核、缺模型、16bit拒绝、取消、源切换/文件变化、关闭与旧成果保护补小规模回归；基于已跑通GUI继续，不重启算法调研。
- 核对网页设置/复制路径/小窗口交互及短导航；对新显示/导出API做身份/损坏反例。完成后机械design detector一次、候选独审、必需CI/正常PR集成。
- 完整验收后向上游自动回传并由上游派发下一任务；本阶段仅进度，goal保持active。
