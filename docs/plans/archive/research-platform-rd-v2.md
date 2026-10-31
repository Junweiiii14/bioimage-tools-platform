# 科研数据平台完整研发总方案

版本 2.0 · 2026-10-31 · B-006 · 产品研发设计与实施依据

本方案把现有 WB 软件发展为一个可持续扩展的科研数据处理产品：实验室人员导入数据，选择实验目的和实验设计，系统自动组织处理步骤，展示图像、曲线和计算状态，最终交付可复查的表格、统计图、拼图和分析记录。后续 Agent 使用同一套模块和执行接口来理解需求、搭建和运行工作流；开发新算法属于独立的实验研发流程，验证通过后才进入正式分析。

**核心实施决定：保留已经完成的 WB 能力、Qt 桌面宿主和工作区存储；渐进拆出计算用例，增加科学资产、模块契约和串行工作流执行层，再用第二、第三个实验场景验证复用。现在不整体重写，不先做任意节点编辑器，也不先把大模型接到现有窗口上。**

这份文档的对象是“要做出来的产品及其实现方法”。每一阶段都应增加一个用户能实际操作的能力；只有目录、接口空壳、任务卡或检查报告，不能算该阶段交付。文中明确区分现有事实、新设计和待实测标准；所有新路径、协议和版本都是待实现设计，不能据此声称产品已具备。

## 1. 最终产品具体是什么

### 1.1 用户的一次完整工作

以 WB 为例：选择一个包含多张原图和样本信息的文件夹 → 选择实验模板 → 软件自动识别图像、寻找膜和条带、估计并应用旋转、定位 ROI、计算曲线和定量、关联内参和对照、组装图表 → 在成果页查看表格与拼图 → 导出结果包。模板记录实验目的和方法；不能从图像凭空推断蛋白名称、样本分组或生物重复身份，缺少这些信息时仅提示补一次批次信息，已有模板可复用。

旋转默认完全自动。工作人员不用手动旋转一次，也不用分别做“排版旋转”和“定量旋转”：系统自动产生一份保精度的校正分析图，预览、ROI 和定量共享它的几何结果。屏幕为了显示所做的缩放、伪彩和 8 位压缩另有显示副本，不作为定量输入。用户看到的内容与计算使用的坐标一致；计算保留采集强度单位、范围和重采样后的浮点值，插值误差另行验证，不承诺旋转无损。

全过程允许三类可选接管：运行前修改模板和参数；运行中暂停、修改某步后继续；运行后调整结果对应的分析或排版并生成新版本。普通样本不逐步弹窗等待确认。遇到无法可靠识别的样本，明确标为待处理并继续其他独立样本；不能用猜测的数据完成一份看似成功的表格。

### 1.2 产品边界与扩展顺序

| 产品层 | 用户得到什么 | 工程完成标准 |
|---|---|---|
| WB 首发闭环 | 自动分析、归一化表、曲线、带来源的拼图和结果包 | 用真实受授权样本走完导入到导出；异常有解释；旧项目可恢复 |
| 多实验工作台 | IF 强度、细胞/核计数，随后克隆与划痕；qPCR、ELISA 走表格路径 | 每种场景都有输入模板、计算方法、质控、结果和验收集，不只是增加一个菜单 |
| 工作流平台 | 模块可组合、复算只影响下游、运行可观察和恢复 | 第二工具无需给 runtime 增加实验特判；数据接口可拒绝不兼容连线 |
| 科研 Agent | 描述目的后生成可解释流程，使用已验证方法执行 | 计划经过确定性校验；操作与普通 UI 共用同一个运行服务 |
| 算法研发助手 | 生成候选方法、运行试验、比较结果、产出版本包 | 隔离执行、独立验证、版本准入；正式任务只选择已准入版本 |

第一版卖点应是完成具体实验任务的可靠性和节省的操作时间。通用平台和 Agent 是后续扩展机制。公开市场数据、融资论证和价格假设沿用 B-004 独立研究；本方案不把潜在用户数量写成已有客户，也不以技术路线代替商业验证。

### 1.3 哪些是已知，哪些仍需产品验证

代码核对基于较新工作树 `codex/t082-reliability-remediation`，HEAD `dfc48ed7c2c944dc8f03c3931bc7985452a31393`，2026-10-31 只读检查为 clean。该树冻结产品提交为 `ed830e1d3bab3d0c8c57f3766a898991e8a0f431`；在用 T-081 R2 为 `f1e6142`，不能把 T-082 候选写成已经替换了在用软件。

本方案编写目录是保留旧改动的 `feat/T-021-laboratory-figure-layout`，HEAD `bb5601addda64fa96fa007612ceda0a0e1ed9b74`。后文代码路径以较新产品树为参照；接续开发先选对基线，不把这里的旧产品文件覆盖过去。历史的 1503 项测试、4 个 wheel 检查等仅为当时工程证据；不等于独立科学准确性、任意客户电脑或本方案新功能已通过。

本轮交付研发设计和可读 HTML，不更改产品代码。阶段、模块、默认候选参数和性能预算是实施目标。真实性能、真实样本的误差范围和方法准入须按后文协议测得。

## 2. 现有代码如何改造

### 基线与阅读方式

本章是待实施设计，不表示新接口或算法已经存在。2026-10-31只读核对的产品根为 `<原调研工作区；以记录的分支和HEAD定位>`，分支 `codex/t082-reliability-remediation`，HEAD `dfc48ed7c2c944dc8f03c3931bc7985452a31393`，工作区干净。产品代码冻结提交为 `ed830e1d3bab3d0c8c57f3766a898991e8a0f431`，到HEAD的差异是文档及证据。历史测试记录不能替代本方案实施后的验证；本次没有运行产品测试，也没有修改产品代码。

主目录保留旧产品与未提交研究文件，不能把本章所在目录直接当开发基线。实施时从上述实际代码提交建立开发分支，单独搬入并审查本设计及需要的规则文件；不得整目录覆盖较新产品，也不得把研究目录的context回执当成开发树回执。若HEAD已有变化，先重新核对下表符号及相关任务。

以下路径均相对上述产品根：`D`=`apps/desktop/src/bioimage_app`；`W`=`tools/wb/src/wb_tool`；`C`=`packages/tool_contracts/src/tool_contracts`；`R`=`packages/platform_runtime/src/platform_runtime`。标记“拟新增”的路径、协议和符号当前不存在。

### 现有真实调用链及可以保留的能力

| 层次 | 现有文件、符号、定位 | 当前行为与改造含义 |
|---|---|---|
| 启动 | `D/__main__.py:15 main`、`:35 run_wb_worker`；`D/web_window.py:142 AdvancedHost`、`:190 QWebChannel` | UI与`wb`/`wb_ocr`静态worker分流；保留明确注册，不允许Agent指定任意导入路径。 |
| 桌面装配 | `D/figure_window.py:107 AsyncStorage`、`:145 IntakeWorkflowSession`；`D/web_bridge.py:69 WorkbenchBridge` | Web工作台包在现有Qt宿主之上，不能把整个窗口类搬进平台运行时。 |
| 批次执行 | `D/intake_workflow.py:494 _advance`、`:541 _execute`、`:1041 _measure`；`W/application/intake_workflow.py:303 claim_intake_workflow_step` | 已有crop/compose/measure/export票据、保存和恢复，但这是WB专用状态机。`intake_workflow@5`要求全批裁剪完成再进入下游；“失败Fig不阻塞独立Fig”需要新策略版本。 |
| 进程生命周期 | `D/project_measurements.py:174 _launch`、`:187 RunSession`；`D/run_session.py:53 start`、`:135 _try_terminal`；`D/process.py:119 ProcessRunner` | 冻结请求、真实PID保存后放行请求、实际退出后提交结果，取消先记账；这是保留的可靠性基础。 |
| 数值入口 | `W/adapters/worker.py:111 load_tiff`、`:112 analyze_annotations`；`W/application/analysis.py:198 analyze_annotations`；`W/domain/lanes.py:44 compute_lane_profiles` | 原值uint8/uint16→半开整数ROI→float64均值剖面→积分。现有严格输入不能直接接旋转后的浮点数组。 |
| 显示几何 | `W/adapters/laboratory_figure.py:189 render_display_segment`、`:208 uint16//257`；`W/domain/fixed_lane_frame.py:42` | 显示图经过RGB8及重采样，定量仍取原坐标矩形；当前预览不是目标统一分析资产。 |
| 输出与修订 | `W/adapters/intake_output.py:131 export_intake_outputs`；`W/application/intake_revision.py:218 revise_completed_intake_crop`；`W/application/project_normalization.py:257 fill_project_normalization` | 已有新目录导出、身份填表、显式配对归一化、所属Fig重算；保留领域语义，不移入通用平台。 |
| 持久化 | `C/api.py:55 AssetRef`；`R/workspace.py:366 save_draft`、`:468 prepare_run`、`:566 start_run`、`:618 commit_result` | AssetRef已是严格物理文件引用；Workspace拥有不可变文件、CAS、单活动进程、退出凭据和结果提交。不是需要重写的空壳。 |

现有工具覆盖导入清单、原值裁剪、固定槽位、几何建议、OCR复核、拼图、灰度剖面与积分、归一化、表格和归档恢复。需要较大改动的是跨步骤数据表示、执行编排和宿主装配，数值核心、原图准入、存储可靠性与历史读取可以逐段保留。

### 目标依赖与拆分粒度

首版继续使用现有四个包。`tool_contracts`只容纳不依赖Qt、NumPy、SQLite的信封与结构描述；`platform_runtime`处理通用资产、状态、依赖与恢复；`wb_tool`拥有WB定位、极性、基线、条带和归一化；`bioimage_app`静态装配工具、进程、存储与界面。跨包只走各自`api.py`。平台不得出现蛋白、Ct、内参或阳性面积等实验分支。

先把WB封装为少量有科学意义的粗模块，再按真实复用和暂停需求拆细。V0粗模块只包装成熟旧计算；V1候选粗模块可包含“自动校正—生成ROI—测量—成果生成”，内部发阶段事件，但不能宣称每个内部函数都已是可恢复节点。后续拆成校正资产、ROI与测量、统计与导出三个边界，必须先把每个边界的输入、提交物和失败恢复做完整。第二工具真正接入后，才评估把共同几何或图像I/O抽到`imaging_core`；不预建大量空公共包。

现有`AssetRef@1`保持不变。拟新增`ScientificAsset@1`组合它，记录语义类型、坐标、单位、来源与方法；设计中的`FileRef`只表示该物理引用角色，不是悄悄替换现有模型。拟新增`ModuleSpec@1`、`ExecutionRequest@1`、`ExecutionEvent@1`、`OutputManifest@1`与物理存储格式分别版本化。图像、表格、曲线、对象和统计结果均通过资产引用传递，不能把数组嵌进Qt桥接消息。

### 文件级改造矩阵

下表“新增”均为拟新增；旧API先保留，入口切换须有对照证据。

| # | 现有职责 | 目标职责与修改/新增路径 | 兼容验证 |
|---|---|---|---|
| 1 | `C/api.py AssetRef`描述文件 | 保留模型；新增`C/scientific_assets.py`描述科学资产并由`api.py`导出 | v1序列化字节、严格字段、旧schema快照不变；错误单位/坐标连接拒绝。 |
| 2 | WB协议与GUI动作各自建模 | 新增`C/modules.py`、`execution.py`、`events.py`、`outputs.py`及`workflows.py`，承载通用信封/流程描述；WB参数schema留在W | 公共包无实验枚举、无数值或GUI依赖；未知主版本明确拒绝。 |
| 3 | `W/api.py`暴露大量专用用例 | 新增`W/application/module_catalog.py`声明受控模块、方法版本和端口，旧函数继续可用 | 注册描述与真实调用绑定；不能靠字符串任意import；隔离wheel可导入。 |
| 4 | `W/domain/lanes.py`仅原生整数输入 | 新增`W/domain/analysis_pixels.py`和浮点剖面入口；复用经验证的积分内核 | 原生整数算法不变；派生float不得转回uint8/16；有限值、范围、极性和mask单独测。 |
| 5 | `W/adapters/tiff_input.py`读取原图 | 保留原图准入；新增`W/adapters/analysis_asset_io.py`读取受控浮点数据、有效区mask及清单 | 原图仍拒绝不支持类型；派生文件独立资源预算、shape/dtype/hash校验。 |
| 6 | 几何候选直接服务显示 | 新增`W/application/corrected_analysis.py`，组合现有候选器与一次原图重采样 | 区分estimated、validated_zero、unknown；启发式score不冒充置信概率。 |
| 7 | 原图ROI与显示旋转分离 | 新增`W/domain/analysis_geometry.py`，保存原图→分析图变换、像素中心约定、mask与ROI坐标系 | 0°、已知角、边缘、空区参考；不能用旋转ROI的原图外接矩形代替分析ROI。 |
| 8 | `W/adapters/laboratory_figure.py`自行显示重采样 | 增加分析资产渲染入口；旧入口继续解释历史display_angle | 新预览、测量、拼图记录同一analysis_asset_id；样式调整只使渲染过期。 |
| 9 | `W/application/intake_workflow.py`专用账本 | 新增`W/application/workflow_template.py`构建WB流程；旧@5继续可读，新策略允许独立Fig继续 | 失败内参阻断依赖它的比值；不制造有效零；明确区分旧整批屏障与新策略。 |
| 10 | 无通用图执行器 | 新增`R/workflow_engine.py`，纯状态转移、依赖就绪、缓存判定与重试；执行器由宿主注入 | DAG环、缺失输入、版本不兼容拒绝；平台不得导入wb_tool或Qt。 |
| 11 | `R/workspace.py`只理解通用文档和进程run | 新增`R/workflow_store.py`，首版用既有opaque文档CAS保存host-owned账本 | workflow_run_id与process_run_id分开；崩溃窗口可对账，不伪造PID或成功退出。 |
| 12 | `D/run_session.py`提交worker结果字节 | 增加可选的结果准备策略：验证候选清单、导入成果资产、再提交manifest；旧默认保持 | 导入失败、取消、退出非零都不得成功；发布孤儿保留并报告。 |
| 13 | `D/process.py`与旧WB有限帧协议 | 新增受限v2 codec/limits配置；`D/__main__.py`静态注册新worker；旧路由不改 | 不全局放宽旧帧限制；洪泛、乱序、晚到、重复终态与退出竞争测试。 |
| 14 | `D/intake_workflow.py`紧耦合FigureProjectWindow | 新增`D/workflow_session.py`装配引擎/存储/执行；`workflow_controller.py`接用户命令，旧Session保留 | 一次仅一个活动进程；关闭排空、重开中断、旧修订结果不得覆盖新草稿。 |
| 15 | `D/web_bridge.py`聚合快照、动作、图片 | 新增`D/workflow_bridge.py`、`workflow_projection.py`和`asset_queries.py`，分离状态投影、命令与按需预览 | 重复事件幂等；旧snapshot合同不变；大图不嵌入周期状态包。 |
| 16 | `D/web_ui/`依赖WB专用状态 | 新增`D/web_ui/run_state.js`，按run/node/attempt/seq更新；复用现有预览与motion工具 | 选中旧结果时新事件不抢焦点；未知进度不造百分比；减少动效与键盘操作可用。 |
| 17 | `W/application/intake_revision.py`按Fig失效 | 新增`R/workflow_dependencies.py`维护技术依赖；W声明哪些参数影响哪些输出 | 改角度重建分析资产及下游；改标签只重做标注/输出；方法版本变化不错误命中缓存。 |
| 18 | `W/adapters/intake_output.py`导出既有结果 | 增加新manifest输入适配，继续使用无覆盖发布与身份映射 | 表、曲线、拼图、方法与来源一致；缺项有状态，不把失败填零；历史目录hash保持。 |

### V0到V1的首条垂直切片：一组WB得到可追溯成果

切片范围是一个Fig、明确目标/内参配对、固定样本槽位的灰度TIFF输入；身份映射通过导入模板一次提供，不依赖文件名猜测。默认路径为导入→自动估计倾斜→生成保精度分析资产→自动ROI/积分→表格与拼图。无需工作人员旋转一次，更不能要求两次旋转。首先作为带清晰方法标签的候选入口运行，完成科学验证后才成为正式默认路径。

1. **冻结输入和旧答案。** 用不含私有数据的小型uint8/uint16固定样本，保存原图hash、既有分析结果及输出hash。加入已知平坦、饱和、空槽、0°和已知几何的独立参考。旧数值作为兼容对照；新插值方法的正确性不能只拿旧矩形答案判断。误差指标与容差须先写方法契约，不能从运行结果反推通过线。
2. **先跑通薄适配。** 实现矩阵1–3和一个粗模块，用旧`analyze_annotations`完成冻结输入到旧结果的等价调用；新信封只负责引用与版本，不在此时偷偷改变公式。为`api.py`导出、模块注册和独立wheel补齐检查。
3. **实现统一分析资产。** 候选角度经适用域检查后，从不可变原图一次重采样，产出float64分析数组、有效区mask及JSON描述。首版可用已有NumPy的受限NPY格式，关闭pickle；预检shape、dtype、字节预算，禁止对象数组。描述保存源hash、角度、变换矩阵、插值/边界策略、采样格点、方法版本与软件版本。float64是明确编码选择，不是“插值无损”的承诺。
4. **在分析图上建立ROI并计算。** 自动定位输出绑定分析资产的ROI；人工修改是可选接管。无可靠角度输出unknown，进入该Fig待处理状态，不把0°当检测成功。mask覆盖不足或区域超界必须有失败/待处理理由，不能把填充值用于积分。初版不把任意历史矩形自动转成新ROI；选择旧记录重算时重新定位，必要时由用户处理明确异常。
5. **用真实worker接宿主。** 拟新增静态路由`--worker wb_analysis_v2`及`W/adapters/analysis_worker.py`，复用ProcessRunner/RunSession退出与取消链。该粗模块内部阶段可报告进度和预览，但首版只在整个模块提交后形成可恢复节点。worker只写宿主为本次attempt分配的暂存目录；宿主校验清单、导入不可变资产，实际退出成功后提交结果清单。
6. **交付可观察的一次运行。** 新工作台入口展示当前步骤、已提交/候选标识、曲线与图；worker忙时仍可浏览其他结果。CSV/XLSX及拼图引用同一分析资产和参数修订；与内参的配对由明确样本身份决定。先按单进程序列执行，不以并行度换取状态复杂度。新策略中的独立Fig允许继续，最终批次状态清楚列出缺项。
7. **用真实操作验收。** 从导入走到打开表与拼图；运行中切换页面和查看曲线；取消后重开；修改角度候选/ROI后重算；只改字体后重新导出。核对旧原图/历史hash不变、当前修订不被晚到结果覆盖、图和数值共源。界面“成功”只对应完整结果提交。UI可操作与科学方法准入分别验收，候选结果不自动进入正式汇总。

### 工作流、worker与存储迁移的具体边界

**首版不升级SQLite。** Workspace现有数据库格式v1含五表，并允许保存opaque JSON。将定义、工作流运行账本保存为新的版本化文档；每个计算attempt仍对应真实RunRecord。账本先保存attempt身份与冻结输入，再启动进程；进程结果成功提交后，账本CAS关联结果引用，最后通知UI。若崩溃发生在结果已提交而账本未关联之间，恢复按attempt/process_run_id核对已提交结果并补关联；不得直接重跑或编造成功。没有确定提交结果的attempt为interrupted，由重试生成新attempt。

资产导入、结果文件发布与账本更新不是一个跨文件/SQLite原子事务。未关联资产或结果保留为待恢复/孤儿证据；只有清单引用、摘要校验与结果提交均满足后才可供正式下游消费。存储线程仍独占Workspace；worker、Web前端和Agent都不能直接写库。图级run不是OS进程，不能把图ID或伪PID塞进现有RunRecord。

**协议双轨。** 旧worker协议的ResultFrame仅接受8/16位及相应范围（`W/application/worker_protocol.py:78`），不能把派生float伪装为16位图。新增协议使用ScientificAsset引用、明确量程与数值方法，保留旧命令/帧模型。新事件有run/node/attempt、单调seq和冻结修订；状态/终态可靠处理，预览允许合并或丢弃。容量策略分路由配置，限制单帧、队列、频率和预览尺寸，不是把旧最大8帧简单放大成无限流。丢弃过期UI事件不等于丢弃进程退出、清理和持久化责任。

**历史与新语义并行。** `W/application/crop_suggestions.py:125 read_figure_project`继续读取既有schema1–15；新工作流使用独立文档类型。旧display_angle只按旧显示含义读取，不能静默解释为定量校正。用户选择新方法后创建新分析资产、ROI与运行，旧结果和方法版本仍可打开。规则“显示变换不进入定量”继续适用于字号、排版和显示色阶；新的自动几何校正是显式版本化分析步骤，预览与定量共同消费其输出。

**确需数据库v2时再迁移。** 当事件查询、节点规模或并发需求证实opaque文档不足，再增加workflow_runs/node_attempts/artifact_links等表，给出DDL、索引和回填程序。关闭活动任务、独占锁、调用现有`Workspace.backup`创建一致备份，在新目录副本迁移；带迁移未完成标记的目录拒绝正常打开。数据库事务、资产核对、格式头写入全部成功后才发布新目录；失败保留旧工作区与待诊断副本，不假称文件和SQLite整体原子。禁止直接复制活动DB主文件或原地覆盖历史；旧客户端应拒绝新格式。并发及云执行需要新增资源租约/远程终止凭据等协议，不能冒充本地exit receipt，均不进入首切片。

### 垂直切片后的实际改造顺序

先完成矩阵1–8及12–13的单Fig候选闭环，保持旧入口可用；随后实现9–11、14、17，把粗模块拆为已提交资产边界，补齐可选A运行前参数、B节点后审核、C事后修订重算。暂停请求只在声明的检查点生效：运行中先显示pausing，当前节点完成提交并确认进程退出后进入工作流paused；首版不提供节点内部暂停；取消等待真实退出；进程崩溃的“恢复”明确是读取已提交节点并重试中断节点，不承诺恢复任意CPU指令位置。

再落实15–16的桥接分流与按需预览，实测主线程、事件队列、首图时间和大批次内存，最后切换新默认流程。缓存键至少包括输入资产内容、参数、方法/实现版本、坐标和关键环境；审核决定与展示状态不能被缓存命中自动伪造。只有已提交、准入状态匹配的结果可复用。

第二场景先接IF强度作为独立工具消费者，以它验证图像/对象/表格端口，再用板式数据验证非图像端口。此后Agent先调用同一受控模块目录生成可验证工作流，再执行已准入方法；算法生成只进入候选隔离路径。Agent不能获得另一条绕过状态、资产、方法准入与结果提交的执行通道。

改造验证应扩展现有`tests/test_workspace.py`、`tests/test_run_session.py`、`tests/test_process_runner.py`和`tools/wb/tests/test_analysis.py`，新增对应协议/工作流/几何测试；每个改动只运行适用检查，再在集成点运行既有完整门禁及独立wheel验证。先前T082工程通过不证明新旋转定量科学成立，科学保留集及真实实验室验收须独立完成。

## 3. 统一接口：数据如何从一个模块交给下一个模块

### 3.1 接口先满足真实的 WB 与 IF，避免万能字典

已有 `tool_contracts.api.AssetRef` 是严格的物理文件引用，只有资产 ID、相对路径、SHA-256、大小和 schema。保留这个 v1，不向它直接追加科学字段。新增版本化 `ScientificAsset`，组合一个或多个旧 `AssetRef`；大数组在文件里，消息只传引用和小型元信息。以下为待实现契约，公开入口仍为 `tool_contracts.api`，内部按职责拆文件。

| 契约/拟新增内部文件 | 必填内容 | 宿主必须检查 |
|---|---|---|
| `scientific_assets.py / ScientificAsset` | asset ID、kind、schema、payload 文件引用、元信息、父资产、生产方法和参数摘要 | 文件哈希、kind、轴/单位/坐标、父子引用完整，不凭扩展名认定数据类型 |
| `modules.py / ModuleSpec` | module ID、模块/方法版本、implementation_digest、输入输出端口、参数 schema、能力、资源估算、适用域 | 固定注册表存在；方法准入绑定精确实现摘要并适用当前输入；不能由工作区指定 Python import 路径 |
| `workflows.py / WorkflowSpec` | template ID/version、节点/边、输入绑定、参数、预期成果、失败策略 | 无环、端口可赋值、必填参数齐全、样本关联合法、每个必需结果可达 |
| `execution.py / ExecutionRequest` | workflow run/node/attempt、document/revision、模块版本、implementation_digest、输入引用、冻结参数、环境摘要 | 请求不可变；包/模型/依赖摘要与准入记录一致；引用固定资产而非“最新”；计算开始后不偷偷读取新草稿 |
| `events.py / ExecutionEvent` | protocol、run/node/attempt、sequence、source revision、kind、payload | 事件属于当前尝试；序号去重；版本/帧长度验证；不以完成消息直接宣布成功 |
| `outputs.py / OutputManifest` | 输出端口→资产、质量状态、统计摘要、方法 provenance | 必需输出存在、文件关闭可读、数值与关系检查、真实进程成功退出和持久提交 |

`schema_version` 管数据布局；`module_version` 管接口实现；`method_version` 管会影响科学结果的公式、阈值、预处理与模型；`workflow_version` 管串联、失败与输出策略。它们不能用一个应用版本替代。示例名均为设计标识，正式创建时冻结 schema 与兼容测试样本。

### 3.2 统一资产的最小类型系统

| kind | 元信息与有效载荷 | 可以去哪里 |
|---|---|---|
| `raw_image` | axes、shape、dtype、采集位深、通道、像素尺寸及其来源、采集强度范围；原文件引用 | 解码/质控/几何预处理，原件不可覆盖 |
| `analysis_image` | float/int 数组、采集强度单位、valid mask、坐标 frame、原图到分析图变换、质量标记 | ROI、剖面、强度测量、分割；只有方法声明接受的 dtype 可连 |
| `display_image` | 8 位缩略图、伪彩/窗口/缩放、来源 analysis ID、显示坐标映射 | 画布和排版；类型系统拒绝连接强度定量端口 |
| `geometry` / `mask` | polygon/rectangle 或标签数组、frame ID、像素中心约定、label ID、对象身份 | 测量时必须与图像 frame/shape 对齐；不自动把多边形包围框当 ROI |
| `object_set` | object ID、label ID、所属 sample/field、面积/质心/边界标记 | 计数、每对象强度、汇总和可审查叠图 |
| `typed_table` | 列名/type/unit/nullability、行实体、sample/replicate关系、数值状态 | 归一化、统计、图表；“灰度”和“浓度”不能因都是数字而互连 |
| `series` | x/y 数组引用、单位、series ID、来源 ROI/对象与状态 | 剖面曲线、拟合、时序；显示下采样不替换正式完整曲线 |
| `statistics` | 分析单位、分组、方法、有效 n、估计值/区间、排除原因 | 结果图与报告；不同视野不自动变为独立生物重复 |
| `figure_report` | 图版配置、素材引用、表格引用、导出规格、provenance | 预览与导出；排版文字更改不使强度结果失效 |

第一版图像分析载荷采用无 pickle 的 `.npy` 数组与 JSON 元信息，valid mask 使用布尔 `.npy`；原 TIFF 保留。表格内部先用带列 schema 的 JSON，结果另导 CSV/XLSX；大体量列式存储在实测触发后替换适配器。禁止模块借“灵活数据”把整个项目对象 pickle 后交给下游。

坐标统一：数组索引为 `[y,x]`；像素中心在整数位置，左上首像素中心 `(0,0)`；外边界位于 `-0.5`，尺寸为 H×W 时右/下边界为 `W-0.5/H-0.5`；图像切片使用半开区间，转换到几何边界显式执行。变换存 3×3 齐次矩阵、方向 `source_to_analysis`、插值/扩边策略和版本。ROI 沿变换成为多边形；需要矩形剖面的 WB 模块在分析 frame 重定位，记录规则与来源。

强度不由分析 dtype 推断。首版 WB 的 16 位采集图旋转成为 float64，强度范围仍来自采集定义；反相上界显式绑定 acquisition range，而不是 `float64` 最大值或每张图自己的峰值。采集位深和量程来源未知时记 unknown；若方法使用容器名义范围，必须明确它不是已核验的仪器有效量程。float32 作为后续独立验证的存储/计算变体。插值产生的边缘空区用 mask 表达；真实零像素与无效像素不同。饱和证据继承原像素质控，不能因插值后的数值变小就消除警告。

### 3.3 一个可连接的 WB 工作流实例

以下是**单图分析子流程的设计示例**，不是现有 API 调用。它只负责一张图的校正、ROI、原始定量和拼图素材，不在缺少跨图内参时做归一化。真实执行前宿主把外部名称解析为内容寻址资产，补入参数默认值、方法/实现摘要并生成完整请求；示例不用伪造哈希冒充实际产物。

```json
{
  "schema_version": 1,
  "workflow_id": "wb_image_v2",
  "workflow_version": "2.0.0",
  "failure_policy": "isolate_independent_sample",
  "external_inputs": {
    "image": {"kind": "raw_image"},
    "sample_sheet": {"kind": "typed_table", "schema_id": "wb_samples_v1"}
  },
  "nodes": [
    {"id": "qc", "module": "wb.source_qc", "version": "1.0.0", "inputs": {"image": "$input.image"}},
    {"id": "angle", "module": "wb.estimate_geometry", "version": "1.0.0", "inputs": {"image": "$input.image", "qc": "qc.quality"}},
    {"id": "correct", "module": "wb.apply_geometry", "version": "1.0.0", "inputs": {"image": "$input.image", "geometry": "angle.geometry"}},
    {"id": "roi", "module": "wb.locate_bands", "version": "1.0.0", "inputs": {"image": "correct.analysis", "samples": "$input.sample_sheet"}},
    {"id": "measure", "module": "wb.measure_float", "version": "1.0.0", "inputs": {"image": "correct.analysis", "rois": "roi.geometry"}},
    {"id": "compose", "module": "wb.compose", "version": "1.0.0", "inputs": {"image": "correct.analysis", "rois": "roi.geometry", "samples": "$input.sample_sheet"}}
  ],
  "required_outputs": ["measure.values", "measure.curves", "compose.figure"]
}
```

这张图表达的是稳定后的拆分目标。V0 先把成熟 WB 计算封装成一个粗模块；V1 引入校正分析链；V2 才逐步按上例展开。每拆一个节点都要证明它有独立参数、可观察产物或可复算价值，不能为了画出很多节点而拆函数。模板由实验包提供，runtime 不认识 target、内参或条带。

外层由 `wb_tool.application.workflow_template` 根据样本表显式展开有限 DAG；第一版无需 runtime 实现动态 map/reduce 语言。每张图生成 `img_A01_qc/.../measure/compose` 这样的稳定节点 ID。输入行至少包含 image_id、sample_id、biological_replicate_id、technical_replicate_id（允许显式 unknown）、target_id、lane_id、reference_measurement_id、control_group；多目标/内参可以来自不同图，不按行顺序猜配对。

聚合模块 `wb.collect_measurements` 接收每图已完成的表以及逐图失败状态，输出保留 image_id/measurement_id 的长表；`wb.normalize` 按明确 reference_measurement_id 连接目标和内参，按模板控制组计算。身份连接不自动证明科学可比：WB模板还须校验膜/批次/曝光/校准、蛋白角色和方法适用条件，源QC失败或已撤销方法不得经join混入有效比值；这些规则属于WB模块，不放进runtime。一个内参失败，只阻断依赖该内参的比值，不阻断独立样本。汇总器声明可接受成功/失败混合的完成记录，等待所有必需子图终态，不把失败表当空成功；批次导出 exceptions 表并标 partial。若单图数值已完成而拼图失败，可保留数值成果，但完整交付仍未完成。

解析连接例：图A测得样本S1目标值120，图B内参60，图C对照样本目标90、内参90；显式配对后的比值为2和1，S1相对对照为2。图B失败时S1归一化为missing_reference、值null，图C独立结果仍为1。两行只有相同名称而无唯一配对时拒绝自动关联。`wb.export_bundle` 最后合并归一化表、完整曲线、各图素材和缺项记录。预览由各步结果派生，因此看到某一步不要求重新运行整条链。

### 3.4 一个模块的实现形状和连接校验

拟新增 `tools/wb/src/wb_tool/application/module_adapter.py` 将旧公开用例适配成以下语义。这里给的是接口草图，不是本轮产品实现：

```python
class ModuleExecutor(Protocol):
    def describe(self) -> ModuleSpec: ...
    def validate(self, inputs: InputMetadata, params: FrozenParams) -> ValidationReport: ...
    def execute(self, request: ExecutionRequest, context: ExecutionContext) -> OutputManifest: ...


# context 仅提供受限资产读写、取消检查、进度/预览发布。
# execute 的纯计算交给 domain；worker 适配器负责 I/O。
# domain 不获取 Workspace、Qt、任意文件系统或网络客户端。
```

`wb.measure_float` 的 image 端口要求 `analysis_image`、二维单通道、首版 float64、采集强度单位和有效 mask；rois 要求 `geometry` 且 frame ID 相同。输出 `wb_band_values_v2` 与完整 `series`。它包装新方法 `wb.measure.profile_integral_analysis@1`，与模块 `wb.measure_float@1.0.0` 的接口版本分开。新分析方法从旧算法数学定义迁移，但不用旧整数入口偷偷截断浮点；旧 `wb.measure_integer` 包装原有方法语义，继续读取旧历史样例。

连线判定分四层：schema 与端口 kind → 元信息 axes/dtype/unit/frame → 样本/配对/行身份 → 方法适用域与准入。geometry/mask还绑定依附的analysis_asset_id及revision；恰好同shape/frame的另一原图不能借用ROI。跨通道复用要求显式配准或共享frame的来源证据。首版WB要求量化ROI内valid_mask全真；插值后一个像素只有全部非零权重的源像素均有效才有效，部分无效ROI拒绝定量，不静默排除后更换分母。预期负例必须包括 display→measure、不同 frame/资产的 ROI、缺内参配对、未知 schema、包含环和未注册模块。转换只能通过显式节点发生，例如单位换算或坐标映射，不允许 runtime 猜测。

### 3.5 运行与重算的实际语义

工作流实例、节点尝试、底层进程是三个身份：`workflow_run_id` 统领一个冻结草稿；`node_id + attempt_id` 区分重试；现有 `RunRecord.run_id` 只表示真实 worker 运行。映射保存在宿主账本。V2 使用串行拓扑调度，复用 `Workspace.start_run` 当前一个活动进程的限制，绝不伪造 PID 或放宽成功提交规则。每节点先用独立 worker，只有实测启动成本值得优化时再设计长驻 worker；不能先假设一个进程可提交多个旧 RunRecord。

| 用户动作/事件 | 后端动作 | 界面行为与结果保护 |
|---|---|---|
| 开始 | 校验模板、冻结 revision、建立 workflow；逐个启动就绪节点 | 显示待运行/正在运行/质控异常/完成，选中当前节点即可看产物 |
| 暂停 | 首版仅节点边界：`running → pausing`；停止派发；当前节点完成提交或失败并确认进程退出后，工作流进入 paused | 立即显示“正在暂停，当前步骤结束后暂停”；界面仍可操作；暂停完成后才显示 paused；底层 RunRecord 不新增伪 paused 终态 |
| 修改后继续 | 在新 revision 保存改动、确定受影响子图；等待旧活动节点退出；创建新的 workflow run/attempt | 保留旧成果，对比旧/新；只重算被影响节点，旧消息不能覆盖新草稿 |
| 取消 | 宿主先记录 cancelling，向进程发取消；超时终止进程树并确认退出 | “正在取消”与“已取消”分开；已提交上游可复用，未提交输出隔离 |
| 程序崩溃/重启 | 活动尝试标 interrupted；验证已提交节点资产；从下一个未完成节点重算 | 显示“上次运行中断”；不伪装为正常暂停，也不声称恢复某 C 函数的内存现场 |
| 单个样本失败 | 依赖它的节点 blocked；无依赖样本继续；汇总带失败明细 | 批次 partial，显示成功/待处理数量；必需样本缺失不能以绿色完整成功结尾 |

节点级重启是第一版恢复能力。模块若声称支持节点内部 checkpoint，还必须声明 checkpoint schema、算法/输入版本匹配和安全点，证明恢复结果与从头运行在预定容差内等价。没有这项证据就从节点头重算，不标记“断点续算”。

缓存键由规范化 JSON 计算 SHA-256：模块/方法/模型版本、implementation_digest（源码发布包+锁定依赖+模型摘要）、输入**科学资产描述摘要及全部载荷摘要**、冻结参数、相关环境指纹、种子。采用项目规定的键序/数值规范，拒绝 NaN/Inf，不使用 Python `hash()`。显示缩放、面板展开不进入分析缓存。运行准入与权限在复用缓存时仍重新检查；被撤销的方法不能靠旧缓存进入新的正式结果。

具体失效例：改导出字体，仅重做 compose/export；改内参配对，重做 normalize/export，若图版显示配对标签也重做 compose；改 ROI，重做 measure/normalize/compose/export；改角度，重做 correct 及所有下游；只放大画布，零分析节点失效。模板必须声明各节点读取哪些参数；不允许拿整个项目 JSON 当缓存键造成所有编辑全量重算。

### 3.6 保存、提交和迁移不能留在口号上

继续使用现有 Workspace 的文件保护、revision/CAS 和提交路径，不新增第二套并行“工程文件”。在 `platform_runtime` 内新增版本化工作流账本（拟 `workflow_store.py`）。**首版不做 SQLite DDL 迁移**：以下逻辑关系用既有 opaque 文档与 CAS 保存，事件采用有界批次资产和索引，避免每个进度点重写巨大文档。规模/查询实测证明不足时，再按第2章副本迁移方案落为数据库表。以下不是当前已有表名。

| 逻辑表 | 键/主要字段 | 用途 |
|---|---|---|
| workflow_runs | workflow_run_id、document_id、revision、spec_asset、状态/原因 | 指向一次冻结任务 |
| node_attempts | workflow_run_id/node_id/attempt_id、process_run_id、cache_key、状态 | 关联既有真实进程记录；唯一活动尝试约束 |
| node_outputs | attempt_id/port、scientific_asset_id、manifest摘要 | 仅已提交产物可被依赖 |
| workflow_events | workflow_run_id、递增序号、事件引用/简短摘要 | 重连与重开；进度采样持久化，关键状态无损 |
| method_admissions | method_id/version/domain、implementation_digest、验证证据摘要、状态 | 宿主控制准入，模块无权给自己盖章；同版本换包摘要不得沿用准入 |

提交次序：worker 写当前尝试 staging → 关闭文件 → 输出 manifest → 宿主观察真实退出码 → 校验引用/哈希/输出必需项 → 沿既有结果提交路径发布不可变结果 → 在账本登记节点输出 → 标记节点完成并触发下游。现有提交与新账本不能假设天然原子；增加幂等 commit intent，将底层 process run ID 作为对账键。

故障注入覆盖四个窗口：文件已写但无 manifest；已收到 manifest 但进程非零退出；底层结果已提交但工作流账本未记；账本已记但 UI 未收到通知。重启对账：前两种不提交；第三种验证底层成功产物后补记一次；第四种从账本重放。发现同一 attempt 对应不同摘要则隔离并报错。不能删掉失败记录后重跑冒充第一次成功。

迁移在副本和一致性备份中进行，成功校验后切换；原工程只读保留。旧 WB schema≤15 保持原显示角与整数定量语义；新自动校正用新的分析分支/方法版本，不能直接修改旧 angle 字段使历史数值悄然改变。旧工程首次选择“按新流程重新分析”时生成新 revision，结果页并排说明方法变更及差异。未知高版本工程拒绝可写打开并给出恢复路径。

## 4. 交互过程：实时可见、可操作、可接管

### 4.1 改动数据通道，动效才能反映真实工作

目前宿主 QTimer 每 180 ms 检查状态变化并经 WebChannel 推送 `stateChanged`，worker 协议只有少量终态型事件且总帧数有界；这支持现有任务，不足以表达多节点连续预览。新协议必须独立握手版本。旧 worker 继续旧路径，新 workflow worker 使用流式事件；不能只把原有 8 帧上限改成无限。

流式事件拟含 `node_started`、`progress`、`preview_available`、`quality_issue`、`node_output_ready`、`node_failed`；`checkpoint_ready` 保留给后续验证过的内部检查点能力。终态由宿主提交后产生 `node_committed`/`workflow_completed`。心跳只证明进程活着，不代表完成百分比。worker 在各 attempt 内生成 `worker_seq` 去重；宿主接收后生成工作流全局递增 `event_seq`，跨节点重连使用后者。每条事件包含 workflow/run/node/attempt/revision，前端忽略过期 attempt，但宿主仍完成退出/清理记录。

| 消息级别 | 通道策略 | UI 策略 |
|---|---|---|
| 生命周期/错误/提交 | 宿主持久记录、按序传达，不合并丢弃 | 更新状态与历史；断开后补齐 |
| 进度数字 | 生产端节流，同节点只保留最新；记录 done/total/单位 | total 未知显示步骤与耗时；不得编造平滑递增百分比 |
| 图像预览 | 文件引用、限大小/分辨率、同节点合并；旧预览可丢 | 屏幕用代理图；点击看原分辨率时按需加载局部 |
| 曲线 | 先小型摘要/可视化点列，完整数据作为资产 | 当前步骤可实时看；最终导出仍用完整曲线 |
| stderr 日志 | 独立限额与截断记录，协议解析不依赖日志文本 | 默认中文问题摘要，展开才显示技术详情 |

建议初始协议预算为单控制帧 ≤64 KiB、预览引用载荷 ≤16 KiB、每节点预览推送上限 4 次/秒；这是工程初值，须以实际样本测量调整。消费者慢时先合并进度/预览，关键事件转持久账本并按序补读；worker 写队列有界，不能无限占内存。对无进度回调的第三方算子显示“正在执行该步骤”，算子返回后显示结果；不伪称每个内部迭代都可见。

### 4.2 三个页面和一个贯穿全程的状态栏

批次页负责文件、样本关系、模板和启动；过程页负责步骤轨道、选中步骤的图像/曲线以及参数接管；成果页负责表图核对、版本差异和导出。它们共享 workflow read model，不各自启动独立计算。状态栏显示当前批次、运行数、异常数和暂停/取消，不因切换页面丢失任务。

拟新增 `apps/desktop/src/bioimage_app/workflow_controller.py` 管用户意图和异步命令，`workflow_projection.py` 把事件投影为 UI 小快照；Web UI 增加流程视图组件与桥接命令。WB UI 保留 ROI/条带等专用编辑器，首版通过宿主内部窄端口挂载；第二工具证明复用后再抽 `desktop_sdk`，不把实验控件放入 runtime。

参数调整用草稿，不在滑动过程中逐次启动正式计算。快速预览请求带 generation，采用最新请求胜出；正式“继续”冻结参数一次。旧任务完成后可以进入历史，但必须带旧 revision，不能改写当前表或把用户刚改的 ROI 弹回去。后端完成前按钮显示接收命令/等待安全点，禁止用禁用整个窗口避免竞态。

### 4.3 动效、性能与验收脚本

动效用于解释状态：新预览完成后交叉淡入、当前步骤短暂高亮、行状态更新时保持滚动位置；首次出现不隐藏内容等动画。可选 120–180 ms 过渡，尊重减少动态效果设置。进度依据真实计数；节点切换不跑虚构加载条。缩略图缓存、列表虚拟化、分片加载和增量消息优先于视觉润色。

初始产品预算：常规点击获得视觉反馈 p95≤100 ms；运行中切换页/选节点 p95≤200 ms；取消/暂停命令确认 p95≤200 ms；新预览从宿主可用到 UI 呈现 p95≤500 ms。它们是待验收目标，不是已实现成绩；记录测试主机/屏幕缩放/样本大小/冷暖启动，任务完成耗时另报。取消完成时间受当前算法安全点限制，单独测量，不能混作按钮响应。

固定体验样例包包括：20 张典型 WB、200 张压力批次、一张超大图、损坏图混入批次、计算中连续改参数和切换样本。所有数据是获授权或合成，典型规格按真实客户样本登记。历史 R09 上限合成场景曾出现 15–27 MB 快照和约 0.5–1.2 s 点击派发；这说明应减少快照载荷，不代表普通客户实际延迟。

用户体验验收：运行时拖动窗口、查看上一张图和完整曲线，软件继续响应；暂停后改一个 ROI，继续后只有该样本及依赖汇总改变；取消先于最终提交生效时不得再冒出成功，提交已先完成时取消返回“已完成”并保留真实历史；关闭重开后能看到上次完成的步骤和中断原因。工程验收同时记录事件序号、revision、延迟和进程退出，不能只靠录屏看起来顺滑。

## 5. 后续实验场景与算法模块

本章给出可实施的候选v1，不宣称这些新模块已经存在或已获科学准入。正常链是“导入已支持数据及保存模板 → 自动质控和计算 → 表格、证据图和报告”；只有身份缺失、超适用范围或人员主动接管才进入待处理。算法失败不能自动切到一个未经验证的新方法来凑成功。

默认顺序为WB自动分析链、二维IF区域强度、核计数/细胞计数、克隆面积与划痕闭合。qPCR、ELISA使用独立表格路线；先交付一个有真实导出格式和SOP的完整场景，不把两者合并成“通用归一化”。IHC和流式只定义后置切片。

### 共用资产、文件结构和交付约定

所有新算法通过`ScientificAsset`组合既有严格`AssetRef`物理引用，不改变旧`AssetRef`的含义。图像链使用`AnalysisImageAsset`：首版WB采用float64载荷和float64累计；IF首切片沿同一策略，float32仅作为后续单独验证的方法变体。资产记录原强度单位、独立`acquisition_bit_depth`、`valid_mask`、质量来源、`transform`和`coordinate_frame`。`DisplayAsset`只供查看，不能接测量端口。下列路径和标识是本轮明确拟定的目标接口；正式编码先在正确产品树检查冲突并冻结契约，不是新增文件清单已经落地。

方法版本和模块版本分开：本章`...@1`表示公式/算法方法v1，同名非WB执行模块以`module_version=1.0.0`登记并显式绑定该方法；WB采用下一表与接口章一致的模块名。静态模块描述同时保存`module_id/module_version`、`method_id/method_version`与绑定源码/依赖/模型的`implementation_digest`，不能由字符串同名推定准入。

```text
tools/<tool>/src/<tool_package>/
  api.py                         # 唯一对外入口及静态模块描述
  domain/<method>.py             # 数值、状态、单位；不读文件、不含Qt
  application/run_<scene>.py     # 组合用例、样本身份和方法规则
  adapters/read_<format>.py      # 有界读取及格式检查
  adapters/export_results.py     # 表、证据图和结果包
  ui/<scene>_presenter.py        # 预览、接管和来源跳转
tools/<tool>/tests/
  test_<method>_analytic.py      # 独立解析预期
  test_<scene>_workflow.py       # 完整成果/取消/恢复/旧版本反例
```

各结果行统一有`sample_id`、`biological_unit_id`、`acquisition_id`、`run_id`、`method_id/version`、`input_scientific_asset_ids`、`status`、`qc_flags`及来源引用；图像结果另带`analysis_asset_id`、适用时带`roi_or_object_id`，表格场景不伪造图像/ROI身份。数值字段另带单位。`failed/unknown/excluded/not_detected`不填有效0。对象属于视野，视野属于实验样本，技术重复属于生物重复；统计的n按方法声明，不能默认把像素、对象、孔或视野都当独立生物学样本。

每条模板均输出：可在Excel等软件打开的CSV/XLSX、PNG/TIFF证据图、可追溯结果清单及可恢复项目。报告列出支持范围、实际成功/待处理/排除数和方法版本；不把部分成功呈现为全部完成。没有图像的表格场景输出曲线/板图，而非强行生成拼图。

参数分三类：格式/单位/边界等确定性参数由契约固定；检测参数在开发集上有限比较后写入模板；科学容差、错误放行上限和支持范围由独立参考与方法负责人预先冻结。后两类未确定时允许候选研发运行，不允许正式科学通过。以下数字算例是独立代数/几何预期，不是伪造的真实样本准确率。

### WB 自动校正与定量 v1 候选链

#### 输入、模块及代码落点

输入首先支持二维uint8/uint16原值TIFF及经过既有读取器认可的原值格式；相机JPEG、截图、RGB伪彩图不能因“能打开”就成为强度原图。样本结构保留实验/膜、Fig、蛋白、泳道、组和生物重复，以及目标/参照配对。现有`domain/lanes.py::compute_lane_profiles`读取整数原图、计算逐行均值；`domain/quantify.py::integrate_profile`实现`profile_integral@1`，线性基线以上的非负采样超额做梯形积分，单位`intensity*pixel`，不乘泳道宽度。这些旧语义保持。[L01]

| 执行模块及绑定方法 | 拟实现位置（`tools/wb/src/wb_tool/`下） | 输入→输出 |
| --- | --- | --- |
| `wb.estimate_geometry@1.0.0`绑定`wb.angle.projection_search@1` | `domain/auto_angle.py` | 原始强度描述、检测副本、范围→校正角/score曲线/不确定原因 |
| `wb.apply_geometry@1.0.0`绑定`wb.analysis.rotate_bilinear@1` | `domain/analysis_transform.py`、`adapters/analysis_asset_io.py` | 原图、冻结矩阵→float64分析图、有效/质量mask |
| `wb.locate_bands@1.0.0`绑定`wb.roi.corrected_lanes@1` | `domain/analysis_lanes.py` | 校正分析图、样本N、支持策略→分析坐标ROI及边界 |
| `wb.measure_float@1.0.0`绑定`wb.measure.profile_integral_analysis@1` | `domain/analysis_quantify.py` | 分析图、ROI、极性/上限→剖面、基线、积分、状态 |
| `wb.normalize`、`wb.compose`、`wb.export_bundle`的1.0.0版本，分别绑定明确配对方法/成图及导出规则 | `application/run_analysis_workflow.py`及相应适配器 | 测量与显式配对→归一化表、拼图、曲线及来源包 |

`wb.measure.profile_integral_analysis@1`是新方法ID，不能重用旧ID掩盖重采样；`wb.measure_integer`只是旧`profile_integral@1`的执行包装，不是将旧方法改名。旧worker只接受原有整数契约；新请求版本携带分析图类型、源摘要、mask和方法范围。先做候选入口和对照，再正式接入默认模板。

#### 可实现的估角和重采样选择

首个候选采用“投影集中度角搜索”，支持整体平行、可分辨的条带；不处理局部弯曲或透视矫正。检测副本可降采样；暗条带转为固定上限U减强度，亮条带直接取强度。仅检测副本允许去背景/平滑；最终测量从原图生成的分析图取得。

```text
for correction_angle in frozen_search_grid:
    rotate detection copy; carry valid coverage
    measure row-mean signal in the same eligible support region
    score = variance(row_means)  # 水平条带应集中到较少的行
select the best correction angle
check peak separation, signal support, edge optimum and region agreement
if evidence insufficient: angle_state = unknown; no invented zero
else freeze transform -> resample original once -> new AnalysisImageAsset
```

工程探针可先用±30°、粗网格0.5°、局部细网格0.05°；这是搜索配置，不是已证明的支持角度或估角精度。正式范围、允许的峰间差和区域一致性阈值由开发集及独立角度参考确定。各角度评分须采用可比的有效支持，不能因为补边0或裁掉背景而提高得分。独立的连通条带主轴角可作为一致性检查候选；与主估计冲突则待处理，不按最终蛋白差异大小选角度。已批准的可靠零角度分支可跳过插值；检测失败不能走此分支。

正式分析v1候选为反向映射双线性、float64计算权重并存float64、扩展画布、明确像素中心和原点；float64减少一次窄化，但也不保证插值科学无损。正角定义为屏幕坐标x向右/y向下时顺时针，矩阵保存source到analysis方向；不是只保存一个无约定的角度。0/90°格点情形可用精确重排。最终图仅从原图及累计几何采样一次；拖动临时预览另有generation，不能成为正式输入。所有有非零插值权重的源像素均有效时才标`valid_mask=true`，端点/采集饱和警示按采样足迹保守传播。量化ROI首版必须完全在有效支持内；补边不是实测零。

新测量保留明确的逐行均值、端点线性基线、非负超额及梯形积分定义，同时显式记录分析图单位、行间距和ROI范围；首版只支持单位像素旋转，不默许缩放。物理像素尺度未知时只声明像素坐标与`intensity*pixel`；已知各向异性像素不能将索引空间角度宣称为物理角度，需另定物理坐标采样方法及独立验证。自动定位沿用已声明N及泳道身份，在新分析坐标重新检测；旧矩形映射成多边形时不能用外接矩形代替。不能定位或条带重叠时保留候选/原因，其他独立Fig继续。归一化只使用显式配对和已批准方法，参照为0/缺失时不产生比值。

#### 输出、独立样例与用户验收

输出增加`rotation_deg[degree]`、`angle_state`、`raw_profile[intensity]`、`signal[intensity*pixel]`、`reference_signal`、`normalized_ratio[1]`、`saturation_evidence`；拼图、测量和曲线引用同一分析资产。

| 独立验收例 | 必须得到的结果 |
| --- | --- |
| uint16暗条带某行原值65525，冻结U=65535；转float64后测量 | 信号方向值为10，不能用float最大值或新图最大值反相；全0°变换不改变像素 |
| 2×2像素`[[10,20],[30,40]]`中心双线性采样；另以90°旋转检验位置 | 中心为25；90°仅置换原值并匹配已约定坐标，mask随坐标走 |
| 原图三行均值`[0,10,0]`、端点基线0、单位行间距；同样每行复制成双倍宽度 | 两者积分都是10 intensity*pixel；不是20。校正候选另用独立角度样本检查完整剖面，不能用“总和接近”代替 |

用户导入模板对应批次后直接看到自动转正、ROI、曲线、表和拼图；无需手动旋转。点击表行定位原图及“本次分析版本”，主动覆盖角度后只重算依赖，新旧运行均保留。正式准入还需真实膜上独立角度/测量参考、不同条带宽度与背景、端点/饱和、边缘和无信号反例；软件不能恢复采集饱和或证明抗体特异性。[B004 T01–T05]

### 二维 IF 强度 从结构定位到可解释强度表

#### 输入与候选v1

先支持二维单通道TIFF或明确`CYX`的多通道TIFF/OME-TIFF及样本CSV；后者必须核验轴序、通道和像素尺度，未知轴不猜。v1支持已定义区域或结构通道定位的区域强度，默认不将Z轴投影、不做跨曝光自动比较。层级为实验样本→视野→ROI；ROI联合区域与单对象强度分别声明。目标强度通道不直接用于挑出“更亮区域”后再证明整体增强。

拟包`tools/if_intensity/src/if_intensity_tool/`，链为`if.import.channels@1` → `if.correct.dark_flat@1` → `if.roi.structure_otsu@1` → `if.background.annulus@1` → `if.measure.region_intensity@1` → `if.report.bundle@1`。对应领域文件为`illumination.py`、`region_detection.py`、`background.py`、`intensity.py`，用例为`application/run_if_intensity.py`。最终导出区域表、背景/质量表、目标通道加ROI叠加图、按样本汇总图和来源记录。

1. **校正选择。** 模板声明有匹配dark/flat时，计算`D=I-dark`，`F=(flat-dark_flat)/median(flat-dark_flat)`，`J=D/F`；分母只在已知有效区域内，零/负或不符合校准条件的F无效。无flat时采用明确的`none`校正模板，不从实验组的生物分布猜照明场。保留负的背景校正结果和警示，不截成0美化；不按每图最大值重新缩放。照明校正与后续背景扣除是两个不同步骤。[N03]
2. **自动ROI。** 默认使用独立结构通道：在有效像素上做Otsu二类阈值，亮前景取`I>T`，8连通区域，按冻结面积规则移除碎屑。float阈值直方图bin配置和取样范围写入方法；Otsu仅提供分割候选，不能保证任何图都存在对象。[N01] 不清晰结构转为待处理；已验证固定视野区域模板可作为独立替代方法，不自动切为“全图=细胞”。
3. **背景。** 对ROI外扩形成环带，排除全部结构前景、无效区域和质量异常；以环带中位数B估计局部背景。环带内/外半径、最小可用背景面积从物理对象大小及开发集确定，必须证明环带确实代表背景。背景不足仅在模板已批准时使用预定义背景区，否则输出`background_unavailable`。
4. **测量。** 在未做检测平滑的J上，`mean_raw=sum(J_R)/N`，`mean_corrected=mean_raw-B`，`integrated_corrected=sum(J_R)-N*B`。ROI平均强度单位`a.u.`，像素求和记`a.u.*pixel_count`；物理面积为`N*sx*sy[µm²]`，不能把积分强度直接标µm²。记录所有原值、B、N及两种端点。不得把WB梯形剖面积分当本方法。

#### 输出与验收

字段包括`channel_id`、`region_definition`、`area_px`、`area_um2`、`background_median[a.u.]`、`mean_raw`、`mean_corrected[a.u.]`、`integrated_corrected[a.u.*pixel_count]`、`exposure_ms`、`calibration_id`和`background_valid_fraction`。没有物理尺度时面积只给pixel_count，依赖µm²的指标拒绝。

| 独立验收例 | 预期 |
| --- | --- |
| ROI4像素`110,130,150,170`，背景100，sx=sy=0.5µm | 原均值140，校正均值40，校正总和160，面积1µm²；复制为两个相同ROI不能把生物n变2 |
| I=`[110,210]`，dark=10，归一化flat=`[0.5,1]` | 两个校正像素均为200；F=0时该位置无效，不得除后填0 |
| ROI均值80，合法背景100；另一个ROI环带全被前景占用 | 前者校正均值−20并保留低于背景提示；后者背景未知，不能产出看似有效的校正强度 |

用户自动获得表/叠加图，点表行即可看ROI、背景环带和通道；修改ROI建立新修订，相关量值和汇总更新。正式验证分别覆盖ROI定位误差、背景偏差和量值，而不是只验分割重合；曝光、饱和、串色、非均匀照明及实际生物重复层级需独立证据。

### 核计数与细胞计数 两个有独立对象定义的方法

#### 核计数v1与细胞扩展

核计数输入是二维核标记通道、尺度与视野/样本关系；全细胞计数还需能定义细胞边界的独立胞质/膜通道及该方法的适用细胞类型。没有这些条件，只能报告核数，不能把核外扩固定半径叫细胞。

拟包`tools/if_count/src/if_count_tool/`，模块为`count.nuclei.otsu_watershed@1`、`count.cells.seeded_watershed@1`、`count.objects.qc@1`、`count.report.bundle@1`；文件为`domain/nuclei.py`、`cells.py`、`object_quality.py`和`application/run_count.py`。对象掩膜通过公开端口交给IF测量，两个工具不导入彼此内部代码。

核v1算法：校正检测通道 → Otsu前景 → 按模板去小区域/补小孔 → 欧氏距离变换 → 局部极大值marker → 对负距离做标记控制分水岭。距离按sx/sy计算；无尺度的模板显式使用像素半径。固定marker平局顺序，避免同图不同运行随意改变对象数。分水岭依赖marker；库示例证明算法可实现，不证明它能可靠拆开所有真实核。[N02]

`min_area/max_area`、最小marker间距、孔洞面积和边缘规则通过开发集对象尺寸/争议标注选择后冻结。v1默认不加入未验证去噪；若测试需要高斯检测平滑，sigma及其物理单位另记入方法，测量仍取未平滑分析图。fallback只允许已验证的“稀疏不接触对象→连通域计数”模板分支；密集、无法分开的团块标`cluster_unresolved`，不逐个臆造数量。

细胞候选使用已验证核marker、胞质前景及边界梯度上的受限分水岭，输出核→细胞关联；首切片限定已有证据支持的单核细胞类型，不能承诺该算法自动把多核细胞恢复为一个细胞。多核、无核或弱边界超范围时待处理；未来支持多核须增加独立边界/合并方法及证据。关联与统计模块可接入独立已确认的细胞标签，允许一个细胞关联多个核；该能力不等于自动分割已解决多核问题。各对象保存`object_id`、标签mask、质心、面积、bbox、边缘接触、形状质量、计入/排除原因；ID对固定资产稳定，修订后用parent_object_id映射，不承诺跨分裂合并保持同一生物对象。

#### 成果和验收例

成果为逐视野`count[nucleus或cell]`、对象表、编号轮廓图、排除及未解团块图、样本汇总；`nucleus`与`cell`是不同指标ID。密度仅在有效面积已知时输出`count/mm²`，图像数量不能直接当n。

| 独立验收例 | 预期 |
| --- | --- |
| 人工构造mask有3个分离区域，面积4/4/1像素；fixture冻结最小面积2 | 计入2、排除1，排除理由为面积；不是把检测失败数当0 |
| 一个对称哑铃mask，显式放两个marker；单marker作为对照 | 分水岭分别产生2/1个标签；验证marker依赖，不将2写为真实核数保证。自动marker还需独立核标注验证 |
| 独立标签fixture明确一个细胞包含2个核；另一视野全无有效采集像素 | 关联/统计应输出核数2、细胞数1，不据此声称首版分水岭能自动分割多核细胞；无有效像素的视野count为null及failed，不输出真实0 |

用户可从总数逐个定位对象和排除理由，主动拆分/合并/补漏生成修订并更新统计。科学验收报告计数误差、漏检/误检、团块与边缘分层；像素Dice只作辅助，不能证明计数正确。

### 克隆形成 v1先交付覆盖面积和染色强度

输入为固定成像条件的孔/皿无损图及孔位样本CSV。强度端点首版只接已定义通道、曝光和位深的原值图；一般JPEG照片可作为另行验证的面积输入候选，不能自动获得相同强度意义。板/孔为技术单位，生物重复另有ID。

拟包`tools/colony/src/colony_tool/`；`colony.well.locate@1`、`colony.stain.segment@1`、`colony.measure.coverage_intensity@1`、`colony.report.bundle@1`分别落在`domain/well_geometry.py`、`stain_mask.py`、`coverage.py`与`application/run_colony.py`。

v1先用保存的板型网格与可见板定位点/孔边拟合整体刚性位置，生成内缩后的有效孔区；定位失败拒绝猜孔位。固定灰度通道的暗染色信号为`U-I`，用空白孔背景中位数B及MAD建立候选阈值`B+k*MAD`；k在有限开发候选集中选择并冻结，不按实验组期望面积调阈值。MAD=0时不能随意加一个常数，应使用冻结的噪声下限或已批准绝对阈值，否则待处理。剔除孔边、固定允许的小碎屑；不把相连染色区强拆为克隆计数。

输出`well_id`、`valid_area_px`、`stained_area_px`、`stained_area_mm2`、`coverage_pct=100*stained/valid`、`stain_signal_sum=sum(signal-B)`及质量状态，附孔图/mask和板级汇总。面积测量与染色总和分别命名；孔几何改变必须重算分母。fallback为已验证孔型/阈值模板，不是在失败后改用“最好看”的Otsu结果。克隆数需新增`colony.count@...`及对象定义、融合参考，当前v1不输出。[B004 E02]

| 独立验收例 | 预期 |
| --- | --- |
| 有效孔1000像素，染色200，像素边长0.1mm | 覆盖20%，染色面积2mm²；不能把200称为200个克隆 |
| 上述染色像素信号均100，背景20 | 校正染色总和16000 intensity*pixel_count；覆盖率仍20% |
| 校验合格的空白孔全部低于冻结阈值；另一孔有效区域为0 | 前者覆盖0且valid，后者面积/覆盖为null且failed；两者不可混同 |

用户导入整板自动获得每孔表及板图，点孔看有效区/染色mask，修改孔位或排除后相关表图更新。科学参考覆盖照明变化、孔边、低染色、融合和背景；面积/强度正确不意味着克隆数或存活分数已验证。

### 划痕闭合 v1时间序列到面积曲线

输入是同一视野的二维相差/明场时间图、明确时间单位和像素尺度、样本/孔/视野映射；文件名可提供待核对候选身份，不能独自决定实验配对。拟包`tools/scratch/src/scratch_tool/`，模块`wound.series.validate@1`、`wound.register.translation@1`、`wound.segment.texture@1`、`wound.measure.closure@1`、`wound.report.bundle@1`，分别落在`domain/series.py`、`registration.py`、`wound_mask.py`、`closure.py`和`application/run_scratch.py`。

首个候选限定“划痕低纹理、两侧细胞层高纹理”的相差图。在细胞层稳定参照区用相位相关估计纯平移，不使用非刚性形变去强行对齐生长细胞；算法的亚像素网格不等于真实配准准确度。[N04] 参照区缺失或多峰歧义则待处理。按全序列冻结共同有效观察窗，各时点面积用同一窗；追加导致窗口变化的时间点须开新修订并重算整条曲线。

检测链选择局部方差图`mean(I²)-mean(I)²` → 低纹理类Otsu → 冻结尺度的小孔/小岛处理 → 选择满足模板方向与连通条件的划痕区域。窗口大小、边缘裕量及几何条件由开发集/实际细胞大小选择。无纹理细胞、漂浮碎屑、多个近似候选不强行取最大空白区。其他成像模态必须另建方法；不在正式样本间自动改阈值算法。

`area_px`与`area_um2`来自共同窗内mask；`closure_pct=100*(A0-At)/A0`，A0必须>0。允许负闭合率并标扩展，不强截0；不把面积百分比叫迁移速度。输出各时点面积、闭合率、位移、有效窗、边界图、曲线及排除说明；临时缺时点用缺口显示，不插值成实验值。[B004 E06]

| 独立验收例 | 预期 |
| --- | --- |
| A0=200像素，At=80，sx=sy=0.5µm | 面积50→20µm²，闭合60%；不是60µm/h |
| 同一二值图纯平移(3,−2)像素，回到冻结共同窗 | 对齐后相同区域面积一致，闭合0；测试位移符号及mask，不仅看图像相似 |
| A0=0；另例A0=100、At=120 | 前者拒绝闭合率，后者为−20%；终点已闭合0面积仅在图像/分割质控通过时有效 |

用户导入时间批次自动得到曲线，点曲线可看对应图/边界；错配和缺帧可见，修订起点自动更新全曲线。独立验收需时间身份、真实边界、漂移和不同初始宽度；该软件端点不能排除细胞增殖等生物混杂。

### qPCR v1 指定效率与参照的相对表达

#### 格式、模块和计算

首先支持冻结仪器导出的CSV/XLSX及明确孔表，不从PDF截图/OCR猜正式Cq。原始字段保留`run_id, plate_id, well, sample_id, biological_unit_id, technical_rep_id, assay_id, Cq, instrument_flag`；NTC、未检出、熔解异常及参照角色有独立字段。首版一个目标/一个已验证参照/一个明确校准条件，不自动扩展多参照算法。

拟包`tools/qpcr/src/qpcr_tool/`；`qpcr.import.instrument_table@1`、`qpcr.qc.replicates@1`、`qpcr.efficiency.standard_slope@1`、`qpcr.relative.efficiency_ratio@1`、`qpcr.report.bundle@1`落在`adapters/instrument_table.py`、`domain/replicate_qc.py`、`efficiency.py`、`relative_expression.py`和`application/run_qpcr.py`。

v1先保存每孔Cq，按冻结SOP筛查质量，不自动删除偏离孔。通过质控的技术重复按方法约定汇总Cq，不将重复孔当生物n。每个assay明确每周期扩增因子E：100%效率对应E=2，90%对应E=1.9；不能把90填入指数底数。稀释系列若有效，以`Cq = intercept + slope*log10(input_quantity)`拟合并记录残差及范围，`E=10^(-1/slope)`；负斜率等数学要求与实际可接受效率范围分开。一个实验样本的比值为：

```text
log2(R) = (Cq_target_control - Cq_target_sample) * log2(E_target)
        - (Cq_ref_control    - Cq_ref_sample)    * log2(E_ref)
R = 2 ** log2(R)
```

仅在目标及参照均有支持E=2的依据时，才允许独立的`qpcr.relative.delta_delta_cq@1`模板；不能在效率缺失时自动落入此公式。[N05] 首版不重新拟合原始荧光曲线产生Cq；不同仪器Cq确定方法/阈值及跨板可比性必须记录和验证。输出`mean_cq[cycle]`、`E[factor/cycle]`、`log2_ratio[1]`、`relative_expression[1]`及逐孔来源，保留技术与生物n。组汇总明确是在log2尺度还是线性尺度，不混用算术/几何均值。

#### 独立验收与操作

| 独立验收例 | 预期 |
| --- | --- |
| E_target=E_ref=2；目标control25/sample23，参照均20 | log2R=2，R=4；control对自身R=1 |
| 同样Cq，E_target=1.9、E_ref=2 | R=3.61，而非4；若稀释斜率为−1/log10(2)，反算E=2 |
| 一个目标孔undetermined，一个参照缺失 | 不填Cq=0或最大循环数，不直接出比值；按SOP标待处理/未定量且保留原孔 |

用户导入已支持表后自动得到孔质控、样本表达表和图；点结果回到目标及参照孔，改参照映射生成新版本。缺效率、质量失败、板间标准不匹配时可交付原始/质控表，但不能称完整表达量分析成功。真实验收依MIQE相关证据、参照稳定性、效率范围、独立算例及实验室SOP，不将原论文某实验误差率作为本项目容差。[B004 E03]

### ELISA v1 标曲、回算和浓度必须一同交付

输入先支持板读仪CSV/XLSX，包含原始OD、读数通道/波长、孔位、标准浓度与单位、blank/QC/unknown角色、技术重复及稀释倍数。一个分析批次绑定试剂盒/SOP和板身份。拟包`tools/elisa/src/elisa_tool/`；`elisa.import.plate@1`、`elisa.preprocess.blank@1`、`elisa.calibration.4pl@1`、`elisa.concentration.inverse@1`、`elisa.report.bundle@1`对应`domain/plate_qc.py`、`calibration.py`、`inverse.py`及`application/run_elisa.py`。

首个候选限定单调上升夹心法4PL；竞争法下降曲线、需要5PL的不对称方法另立版本。空白和双波长扣除只按保存SOP做一次，不能对仪器已校正OD再次扣除。采用如下明确参数化：

```text
y(x) = a + (d-a) * x^b / (c^b + x^b), x >= 0
a=下渐近值; d=上渐近值; c>0=半响应浓度; b>0=斜率参数
x(y) = c * ((y-a)/(d-y))^(1/b), a < y < d
```

数值实现候选为SciPy `least_squares(method='trf')`，残差`sqrt(w_i)*(pred_i-observed_i)`。为落实d>a、b/c>0，优化`(a, log_gap, log_c, log_b)`并恢复`d=a+exp(log_gap), c=exp(log_c), b=exp(log_b)`；每个优化变量采用冻结的有限数值边界以防溢出，不将d>a误写成求解器原生支持的任意耦合不等式。用固定多初值（a/d由标准低/高信号初始化，c由正标准浓度中位数，b从预设小集合起步）避免依赖单次初值。保留各次收敛、残差和参数边界命中，限制迭代/时间。[N07] 同一板不能自动在4PL/5PL/直线之间挑最有利结果；模型和权重由开发验证确定后写SOP。

权重候选支持等权与预先拟合的方差模型`w=1/variance_predicted`；不能把某标准两个相同重复的样本方差0当无限权重。等权仅作为研发基线或已有方差证据支持的正式方法。正式范围需独立QC及回算/精密度证据；模型选择不能只看R²。[N06] 标准点数及浓度分布必须足以识别参数，不能因为“4个参数有4个点”就宣告可靠。

浓度只能在已批准的量化范围内给有效数值；`a<y<d`只是可求逆的数学域，不等于LLOQ至ULOQ。超范围给状态和必要重测建议，不外推、不设0。先按SOP逐孔反算再处理技术重复，保留稀释前浓度；原样浓度`c_original=c_well*dilution_factor`，因子必须是显式正数，单位显式换算。

最终输出标准曲线图、每标准观测/预测/回算/回收率、独立QC表、逐孔浓度和状态、样本汇总、板位图及方法包。字段包括`standard_x[ng/mL等]`、`od_raw[absorbance]`、`od_used`、`a,d[absorbance]`、`c[concentration]`、`b[1]`、`concentration_well`、`dilution_factor[1]`、`concentration_original`、`quantification_status`；空白x=0的百分回收无定义，不能除0。

| 独立验收例 | 预期 |
| --- | --- |
| 解析曲线a=0,d=2,c=10,b=1 | x=10→y=1；y=1.5→x=30；稀释因子3→原样90。同式前向反向只验代数，另用外部已知QC验证拟合与量值 |
| 标准`x=[0,2,5,10,20,50]`，独立手算`y=2x/(10+x)` | 作为确定性无噪声拟合fixture；预测应还原该曲线，系数/收敛的数值阈值按实现浮点分析冻结，不能冒充科学容差 |
| y=2或2.1；另有回算9而已知标准10 | 前者无有限合法反算/越数学域，不产伪浓度；后者回收90%、相对偏差−10%，是否科学通过由SOP决定 |

用户导入保存板模板即获得标曲、回算和浓度，不需要手动拟合；点标准看来源/排除依据，改稀释因子只更新相关结果，新旧板报告均保留。拟合失败时可交付原始板图与失败报告，不能切换直线并静默出正式浓度。

### 后置 IHC 与流式的首个可交付切片

以下只冻结最小输入/成果和候选职责，尚未专项核实格式、许可、性能与科学方法，不进入当前首版承诺。

| 场景 | 具体首切片与拟模块 | 输出/独立预期 | 科学及用户验收边界 |
| --- | --- | --- | --- |
| IHC | `tools/ihc_area/src/ihc_area_tool/`；先读取受支持RGB切片及外部已批准组织/阳性mask，`ihc.area_fraction@candidate1`在`domain/area_fraction.py`完成固定层级/尺度聚合。染色解混、自动组织和细胞分类另立候选，不从IF复制公式 | 区域表、阳性/组织面积、切片定位图。fixture组织200像素、阳性60→30%；无组织→null；分块统计须去重重叠，两个各100组织/30阳性的不重叠块合并仍30% | 用户点表行回到对应切片区域。区域、细胞计数及强度评分分别定义；需要独立组织/染色参考与扫描条件验证。只支持面积时不自动产细胞评分 |
| 流式 | `tools/flow/src/flow_tool/`；先做指定FCS版本的只读事件导入及已批准门控模板回放，`flow.gate.apply_template@candidate1`在`domain/gates.py`；新补偿/变换及自动找群另行核验。模板记录轴通道、已用补偿/变换、父门和边界规则，不能重复补偿 | 门控树、散点图、群体事件数/父门百分比及来源。fixture父门4事件、子门2→50%；父门0→百分比null；边界点按冻结规则判定且同一子门内一个事件只计一次；只有声明互斥的门才要求跨门唯一归属 | 用户点群体回到父门、事件与图；不能把显示坐标阈值无说明套原事件。通道不匹配、补偿来源不明或父门缺失拒绝运行；不把图像分水岭用于事件门控 |

### 开发次序、独立验收证据与本轮核验范围

每个场景按“确定性解析fixture → 完整候选模板 → 真实开发样本 → 冻结方法及独立留出 → 限定范围启用”推进。第一步已经可由AI实现；未知数据授权、样本身份、科学负责人或容差只阻止对应使用/晋级，不阻止读取器、契约、故障处理、合成评测和报告链开发。用户正常处理已启用模板时不逐样本重新批准。

用户验收使用中文“导入”“运行”“查看来源”“接管”“保存新版本”“导出”；固定正常和异常样本由交付包准备。独立工程检查负责源摘要、浮点协议、单位和坐标一致性，用户不需核对JSON或写代码。科学门槛另报告全部预先登记样本的失败、自动完成、错误放行、量值/对象误差及分层，不挑最好一次。

本轮2026-10-31只新增本章节文档，没有安装算法依赖、改产品或运行真实实验样本。已用bundled Python复算本章标量例：IF40/160/1µm²、flat200/200、WB积分10、qPCR4与3.61、ELISA30及90、划痕60%、克隆20%/2mm²/16000，退出0。这些是算术核对，分割、拟合求解器、自动估角和整条产品链均未实测。已有读取尝试误指`quantification.py`失败，随后按实际文件`quantify.py`核对，不把失败隐藏。

#### 来源与适用限制

所有新增访问日期均为2026-10-31。官方API页面版本用于说明候选实现行为，不是本仓库已安装依赖版本；实施时锁定并验证依赖。B-004来源台账及既有T01–T05/E01–E06继续适用，本节只补新增技术事实。

| 编号 | 来源与日期 | 已核验内容和限制 |
| --- | --- | --- |
| L01 | 较新树`dfc48ed7...`，`tools/wb/src/wb_tool/domain/lanes.py`与`quantify.py`，本轮只读 | 核对整数准入、行均值、固定dtype上限、线性基线非负梯形积分；未运行产品，未改公式 |
| N01 | [scikit-image Thresholding](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_thresholding.html)，读取版本0.26.0，页面未列发布日期 | 官方正文：Otsu按类间方差选阈值。不是无对象判断器，不保证生物分割准确 |
| N02 | [scikit-image Watershed segmentation](https://scikit-image.org/docs/stable/auto_examples/segmentation/plot_watershed.html)，读取版本0.26.0，页面未列发布日期 | 官方正文和示例：距离变换极大值作marker，负距离分水岭分离相接形状；真实细胞/核参数未验证 |
| N03 | [CellProfiler 4.2.8 Image Processing](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.2.8/modules/imageprocessing.html)，固定版本，页面未列发布日期 | 读取照明校正、图像对齐及强度变换说明。本文dark/flat与环带是明确的项目候选，不声称照搬CP全部行为或对任意图适用 |
| N04 | [scikit-image registration API](https://scikit-image.org/docs/stable/api/skimage.registration.html)，读取版本0.26.0，页面未列发布日期 | 相位相关为平移配准；文档指出照明/噪声影响。本文固定共同观察窗是项目设计，不是已验证划痕结果 |
| N05 | [Pfaffl 2001 A new mathematical model for relative quantification in real-time RT-PCR](https://pmc.ncbi.nlm.nih.gov/articles/PMC55695/)，2001-05-01 | 原始正文读取公式变量、控制减样本及E=10^(-1/slope)，固定E=2的条件；不借原实验性能给本产品容差，需验证仪器Cq定义 |
| N06 | [Immunoassay Methods 官方PDF](https://www.ncbi.nlm.nih.gov/sites/books/NBK92434/pdf/Bookshelf_NBK92434.pdf)，2012-05-01，更新2019-07-08 | 本轮读到39页PDF，印刷页19–21的标曲、4/5PL、权重、回算论述；HTML仍遇浏览器检查。截图一页返回cache miss，依正文提取核对。本文4PL参数化/数值例为显式数学设计，不移植文献某实验CV阈值 |
| N07 | [SciPy least_squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)，读取版本1.18.0，页面未列发布日期 | 官方正文核对有界TRF及残差最小化。求解器success不等于标曲科学通过；本轮没有运行该求解器 |

本章冻结的是可开发候选、输出含义和独立预期。算法默认、检测阈值、质量放行和科学容差只有在相应方法任务完成后才进入正式模板；Agent只能组合已准入版本，不能在实验数据上随意改算法寻找期望结论。

## 6. Agent 什么时候加入，具体做哪些开发

### 6.1 先让系统可调用，再让模型决定如何调用

从 V0 开始给模块建立机器可读描述，这只是做好可调用接口，不接模型。V2 开始保存真实计划、状态和来源，为后续训练/评测任务准备结构化样例。V3 获得可靠 WB 闭环后，可以开发仅针对 WB 的影子规划器；V4/V5 的实际跨工具连接验证通过后，才把“多实验编排”作为正式能力。V6 接入受限执行；V7 才接入新算法研发。WB 范围的 V6 可以与第二场景开发并行，但不得宣称已验证跨实验智能组装。

Agent 不是另起一套工作流系统，也不通过模拟鼠标去点自己的软件。它调用普通界面使用的应用服务，计划最终落到相同的 WorkflowSpec、资产和任务引擎。模型服务暂时不可用时，实验人员仍能通过已有模板完成工作。

### 6.2 新增代码放在哪里

| 拟新增位置 | 具体实现 | 不承担的职责 |
|---|---|---|
| `packages/agent_runtime/src/agent_runtime/catalog.py` | 把已注册模块、输入输出、参数和适用域投影成可检索目录 | 不读取具体工具内部，不扫描用户目录自动加载 Python |
| `intent.py` | 结构化用户目的、数据范围、希望交付物、缺失信息 | 不从聊天文本臆造样本与重复身份 |
| `planner.py` | 从已批准模板选型，必要时组合目录内节点，输出计划 | 不自己判定科研方法已被验证 |
| `plan_validator.py` | 复用通用 DAG/类型校验，加授权、预算、方法和数据范围检查 | 不把模型的“看起来合理”当校验结果 |
| `session.py` | 保存任务上下文、计划版本、工具请求与运行映射；脱敏诊断 | 不把完整原图默认塞进聊天历史 |
| `provider.py` | 模型调用接口、超时/限额、重试和结构化输出解析；实现由装配层注入 | 不硬编码到某一服务商，也不散落 API 密钥 |
| `apps/desktop/.../agent_controller.py` | 助手意图→服务命令→真实成果链接，复用暂停/取消 | 不直接写工作区数据库或科学结果 |
| `apps/algorithm_lab/`（V7 新增） | 隔离候选包构建、评测、证据比较与准入请求 | 不与正式计算共享可写目录和生产凭据 |

`agent_runtime` 的依赖限通用契约和受限服务端口；工具目录由应用装配提供。模型 SDK 作为适配器依赖，避免把大型模型运行环境加入所有分析工具。第一次只有一个 provider 实现和一个本地模板 fallback；真实需要替换时再增加第二实现，不能先造插件市场。

### 6.3 给 Agent 的工具必须足够窄

| 工具 | 参数/返回 | 执行前校验 |
|---|---|---|
| `inspect_dataset` | 已授权 asset IDs → 格式、样本字段、质量摘要 | 数据范围与大小；默认不发送原始像素给外部模型 |
| `list_methods` | 任务目的/输入 kind → 可用模块和方法适用域 | 只返回调用者可用的方法；研发目录与正式目录分开 |
| `propose_workflow` | intent + catalog snapshot → WorkflowSpec 候选 | 模型输出只是计划，没有执行权限 |
| `validate_workflow` | 计划 → errors、warnings、所需输入、资源估算 | 连接、科学准入、权限、资源、成果可达性确定性校验 |
| `start_workflow` | validated plan ID + input revision + idempotency key → run ID | 计划摘要未变；数据范围/预算有效；服务端去重 |
| `observe_run` | run ID + cursor → 新事件与成果引用 | 只能观察允许的任务；文字总结不得替代状态 |
| `request_pause` / `cancel_run` | run ID + 操作 ID → accepted/current state | 相同操作重试幂等；终态按引擎返回 |
| `export_results` | 已提交 run ID + 成果类型 + 批准输出目的地 → 文件清单 | 产物完整、方法状态、路径；对外发送不在此工具的默认权限中 |

预览和运行完全本地也能工作；外部模型默认只拿结构化元信息和必要摘要。是否上传图像必须在具体部署配置中明确，不将一次文本对话同意扩展为原始数据上传权限。

### 6.4 一条真实任务的执行逻辑

用户输入“把这批 WB 做成灰度表、内参归一化和拼图”。系统先读取当前批次选择及样本表。若方法、内参和对照已在模板中，Agent 选模板、绑定输入、校验后直接执行；不额外让用户审批每一步。若缺配对关系，只问“哪些样本对应哪个内参/对照”，不能让模型猜完继续。未授权花费、对外发送或新数据上传仍由具体授权边界处理。

```json
{
  "intent_version": 1,
  "goal": "wb_quantification_and_figure",
  "dataset_id": "batch_001",
  "document_revision": 12,
  "template_id": "wb_auto_v2",
  "outputs": ["raw_measurements", "normalized_table", "figure", "provenance"],
  "execution_mode": "formal",
  "constraints": {"data_egress": "metadata_only", "allow_unapproved_methods": false},
  "missing_fields": [],
  "validation_required": true
}
```

这只是意图示例；真实执行使用校验后固定的计划 ID，不接受助手自由文本中的文件路径作为运行命令。科研工具请求超时重试沿用 operation/idempotency key；若服务端已开始，返回原 run，不再开一份计算。模型在运行中断线后，引擎按已冻结计划继续；重连先读取真实状态，再解释，不凭聊天历史推断成功。

模型调用费用另设账本，不能靠科研任务幂等保证供应商不重复计费。请求前按配置的最大输出 token、输入估计和价格快照预留额度，限制重试次数与累计预留；超时且计费状态未知的请求继续占用额度，取得用量记录后对账。预算不足停止新的模型请求并保留本地任务。价格未知或服务商不能支持必要限额时，不开启自动付费执行；这些是实现时的真实配置条件，不在本方案里虚构单价。

### 6.5 受限 Agent 如何验收

建立版本化任务集，覆盖已知正常目的、等价自然语言、缺少实验身份、错误端口、方法未准入、预算不足、数据越权、取消、服务断连与重复请求。每个题目有独立的允许计划/必需成果/禁止动作；合理计划可以不止一种，不能只逐字比对一个标准 JSON。

首轮建议至少 40 个任务作为工程冒烟样例：12 个正常/改写目的、8 个缺参、8 个非法连接或方法、6 个权限/预算、6 个中断/重试。样例规模是拟定起点，不能据此宣称广泛可靠。另建未参与提示词调整的评测集，固定模型/提示词/目录版本，报告完成率、无意义追问、错误拒绝、执行工具选择、运行费用与耗时分布。

放行的硬门槛是：未校验计划不得执行；测试集中的越权/未准入调用全部被**执行层**拦截；相同幂等请求不产生重复任务；成功宣告全部能定位真实已提交文件。自然语言理解正确率的对外承诺在取得代表性任务结果后确定，不能先承诺“理解所有科研需求”。数值正确性属于所调用科学模块的独立验收，不以语言模型评分替代。

### 6.6 新算法开发是一条独立的研发流水线

V7 的研究任务先结构化：目标端点、输入范围、现有基线、禁止改动的标签/标准、资源上限、训练/调参/独立验证数据边界。Agent 生成候选源代码与方法声明，在隔离环境构建，跑解析例、开发样本和性能探针，再把候选提交给独立评测。评测结果回到方法中心，不能直接把代码文件复制进正式模块目录。

| 研发步骤 | 必须生成的可交付物 | 晋级条件 |
|---|---|---|
| 定义问题 | `method-spec.json`，例如“在明确倍率范围改善密集核分离”，列支持域与端点 | 有基线和可计算评价指标；“更智能”不构成目标 |
| 构建候选 | 固定源码摘要、依赖锁、模型来源/版本、输入输出 schema、资源需求 | 可在干净隔离环境重建；依赖与模型使用范围可追溯 |
| 开发评测 | 解析例结果、开发集比较、失败样本和速度/内存 | 不弱化测试、不删除难例、不只报均值掩盖失败域 |
| 独立验证 | 冻结候选在隔离留出集上的逐例结果与结论 | 阈值在看结果前定义；科学负责人确认适用域与限制 |
| 工程准入 | 安装/接口/资源/取消/故障恢复检查；包摘要 | 不破坏宿主，支持声明的接口和环境 |
| 发布方法版本 | 宿主维护的准入记录，关联精确包摘要/证据 | 独立科学和工程条件均满足；候选生成者不可自签 |
| 撤销/回退 | 禁止新正式调用，历史成果带方法状态说明 | 历史不可覆盖；重分析生成新结果并说明变化 |

科学负责人不是要求普通实验人员每次运行都审批算法。正式方法完成一次版本级验证后可以自动用于其适用范围；改变方法语义、模型或关键预处理时重新评估对应版本。没有负责人或代表样本时，可以继续工程框架和研发模式，不能把未知项当已批准科学方法。

在 Windows 本地首个候选实现应选择真正隔离的虚拟环境边界，例如独立虚拟机内运行、输入只读传入、输出经校验接收、默认断网、无生产工作区挂载和凭据。具体虚拟化产品/镜像/可用平台在 V7 技术探针决定，不能把 Python venv、普通子进程或内存预算当安全沙箱。Linux 服务器的隔离方案也必须验证文件、网络、进程和资源边界，而非仅画出容器图标。

独立留出集由评测服务保管；候选不能读取答案文件，研发 Agent 不能无限查询同一留出集然后据此调参。失败后返回预先约定的诊断粒度，重复迭代消耗的留出资格要记录；确认被用于调参的样本转为开发集，并补充新的独立样本。结果需同时包含性能、误差、失败覆盖和适用域，不只挑最优例图。

## 7. 本地、云端与企业级能力如何落地

### 7.1 默认本地，远程算力按同一协议扩展

| 方案 | 进程与数据路径 | 引入时间/适用条件 | 必须实测的项目 |
|---|---|---|---|
| 本地单机 | Desktop → 本机调度 → worker；原图、SQLite、结果都在本机工作区 | V0–V5 默认，适合仪器电脑与常规批次 | 目标电脑安装、16 位保真、内存峰值、断电恢复、离线导出 |
| 本地计算+云模型 | 原始分析本地；助手经 provider 发送被允许的任务元信息 | V6，有明确模型服务及费用配置 | 摘要脱敏、断网/超时、费用封顶；关闭模型仍能用模板 |
| 实验室服务器 | 客户端 → 项目/运行服务 → worker队列；服务维护项目写入与角色 | 多台电脑共同项目或本机算力不足时 | 两客户端修订冲突、身份权限、恢复、配额；不直接共享SQLite并写 |
| 全云托管 | 项目服务、对象存储、计算队列、机构身份/隔离、账单 | 数据上传及机构托管需求验证后单独建设 | 上传/下载耗时与费用、数据地域和保留、访问隔离、离线策略 |

本地到远程不改科学模块：新增 `ExecutionBackend` 适配器，用同一 ExecutionRequest/OutputManifest；资产传输以内容摘要去重、校验完整性，计算端不能把客户端本地路径当远程路径。远程后端新增可信任务身份和终态/取消凭据，不能给本地 RunRecord 塞一个伪 PID 或要求客户端观察服务器 OS 退出；该协议在远程阶段独立版本化和验证。远程任务使用可重试 operation ID；断网是状态未知/重连待确认，不能直接当取消成功。UI 仍观察相同事件投影。

首版工作区组织沿现有存储约定扩展 raw、draft、staging、results 的逻辑职责，不承诺这些新目录名已存在。缓存不等于权威结果；删缓存只能影响速度，不能使已提交结果失去必需原始依赖。备份从一致性快照生成，恢复必须到新目录演练，不能只确认 ZIP 能打开。

### 7.2 企业级首先是可维护和可恢复

V0–V3 先交付固定依赖、日志关联、失败恢复、版本迁移和安装验证；V4/V5 证明包边界和第二场景扩展；多人需求出现时增加身份、项目权限与冲突管理。暂不引入微服务集群、跨机构租户或复杂计费系统。它们各有明确触发条件，不能挤占首个实验成果闭环。

正式发行包必须能够说明：应用/方法/模型版本、支持格式与设备、数据目录、备份恢复方式、已知限制、安装/升级/回退结果。依赖升级独立修改，数值变化与纯重构分开。日志记录 run/node/attempt/revision 和错误码，默认不记录原图和身份敏感内容；用户可导出脱敏诊断包。

资源规划采用实际计量：每批输入字节、峰值内存、CPU/GPU 时间、预览传输、模型调用量、存储和支持工时。将计量数据留在成本表，再决定定价和云端预算。本文不凭当前没有的客户规模或模型价格计算虚假利润。

## 8. 可运行版本与成果交付切片

以下V0—V7均为**拟议构建版本**，不是已完成软件或发布日期。RD编号只是本节的行为拆分标识，不创建产品任务、不替换P任务状态。样例文件名描述未来实际交付结构，本轮没有生成这些实验结果。

基线沿用B-004核验的四包结构、WB原值方法、Workspace事务与Qt WebEngine工作台；已有导入、裁剪、定量、归一化、PNG/TIFF/CSV和恢复能力可复用，通用工作流、IF及Agent不能写成已有。[依据A] 统一旋转以用户最新要求及本方案第3/5章为准：自动估角后从原图一次采样，一份校正分析资产供预览、ROI、曲线和定量共同引用；不让用户操作两套旋转。B-004早期“双旋转操作”建议不作为新目标。[依据B]

### 8.1 三屏工作台：批次、过程、成果

三屏共用同一项目导航与版本栏，切屏不停止计算。普通用户看到样本、步骤、成果和异常；包摘要、事件序号等放在“查看来源”抽屉，不占主操作区。

|屏幕|信息与主要入口|必须形成的交互|
|---|---|---|
|批次|左侧项目/批次；中央文件和样本身份表；右侧方法模板、成果清单；“导入文件夹”“导入样本表”“开始处理”|自动读取已有映射和模板；只对缺失身份提问。显示准备就绪、待补信息、不支持的分别数量；不按识别条带数臆造样本|
|过程|左侧按样本/步骤的执行树；中央当前图像、ROI和曲线；右侧参数、质量与来源；“暂停并调整”“继续”“取消”|点击任一步保持查看焦点；接收进度不强制跳屏。区分计算中、暂停请求、已暂停、待处理、已保存；临时预览有明确标记|
|成果|左侧按批次/样本/版本筛选；中央表格、拼图或曲线页签；右侧来源和修改影响；“打开输出文件夹”“修改并生成新版”“恢复项目”|表行与图中对象互相定位；报告显示成果覆盖和缺失项；用户能同时打开旧版、新版比较，不以新结果覆盖旧版|

前端在现有WebEngine宿主中逐步建立批次列表、步骤树、按需图像/曲线视图、结果页签和来源抽屉；这些是拟议构件，不宣称当前已有同名组件。宿主只发布小状态和资产引用，表格分页、图像按可见范围读取。无需为三屏先改换前端框架。[依据A §3/6]

### 8.2 V0：旧WB方法从界面装配中独立调用

**可运行入口与流程：** “验证中心→旧WB方法对照→打开验收样例→运行”。用户选择冻结的旧项目，看到“旧结果”“独立调用结果”“差异”三列；此入口服务工程对照，日常WB入口继续保留。

**构建物及依赖：** 在wb_tool.api后增加一个成熟粗粒度用例的模块适配器；静态ModuleSpec、ExecutionRequest、OutputManifest由真实调用贯通，复用现有worker与Workspace提交。前端增加薄对照页，不重做全工作台。输入是已存在的原图、ROI及旧方法参数；不增加科学校正、不放松uint8/16旧入口约束。

**输出样例：** v0-compare/measurements.csv、differences.csv、run-manifest.json；表内包含样本/指标/值/状态/方法版本，失败列保留原因。输出需由真实运行产生，不从旧表直接复制。

**图形验收与拒收：** 点击运行并打开差异表，正常样例逐项符合冻结旧输出及事前约定精度；加入坏分母或不支持输入时，两入口保持相同失败语义。随后打开原项目，旧界面与历史仍可用。仅导出模块清单、结果不带来源、隐藏失败或旧入口失效均拒收。工程等价不等于独立科学准入。

**RD行为顺序：** RD0.1实际适配旧请求并调用；RD0.2双入口运行并比较冻结结果；RD0.3持久化结果和失败后重开；RD0.4在隔离安装中运行同一对照入口。

### 8.3 V1：自动校正资产真正进入数值分析

**入口与流程：** “批次→新建校正方法验证批次→开始”。自动估角、生成分析图和ROI，直接显示曲线及定量；只有不支持或不确定样本进入待处理，不弹出逐图旋转确认。主动覆盖角度只修改同一几何定义。

**构建物及依赖：** 依赖V0真实调用及方法评测契约。后端建立AnalysisImage加载路径、float输入及反相范围契约、有效mask、坐标映射、来源质量记录，新worker/结果版本与旧入口并存。角度变化从原图重新一次采样；前端同源预览、ROI叠加和版本对照同时接通，不能只完成一张转正图片。[依据C]

**输出样例：** A01-analysis.npy、A01-valid-mask.npy、A01-geometry.json、measurements.csv、quality.csv；恢复包中保存原图引用和新旧方法身份。内部载荷固定为受控NPY；若附加分析TIFF导出须记录转换语义，不把导出文件直接作为新的权威输入。

**验收与拒收：** 打开带倾斜的固定样例，查看转正图、表行和“来源与版本”；三者指向同一分析版本。用“改变角度”产生新版，旧版仍在；不确定角度显示原因而非成功0度。独立样本另核验估角与最终量值。RGB8预览参与定量、补边被计入真实信号、抹掉原始端点提示、旧显示角静默改写历史数值均拒收。未科学准入时界面固定标“研发候选”，不得以工程通过发布正式方法。

**RD顺序：** RD1.1输出并校验分析资产/mask；RD1.2数值核和worker接受明确新契约；RD1.3同源ROI/预览/表行联动；RD1.4角度修订、旧项目重现和错误输入反例。

### 8.4 V2：自动工作流加运行前、中、后的可选接管

**入口与流程：** “批次→WB自动成果模板→开始处理”，自动完成校正、ROI、定量、归一化、成图与导出。过程屏可浏览任何步骤；“暂停并调整”先显示请求，再在安全位置停下；完成后“修改并生成新版”只重算依赖分支。

**构建物及依赖：** 依赖V0模块调用、V1资产工程契约。后端加入版本化WorkflowSpec、NodeAttempt、持久化调度、依赖失效、事件通道和宿主提交仲裁；前端三屏贯通，提供参数表单、重算影响摘要、进度与临时/正式预览。研发模式可以接候选方法，正式模板只调用准入范围内方法；调度器不得凭模块自称approved放行。

**输出样例：** run-manifest.json、node-results/、measurements.csv、normalized.csv、figure.png、exceptions.csv。中断时保留有效已提交产物与未完成状态，不能把临时图列入成功清单。

**验收与拒收：** 运行多图批次时切屏看曲线；主动暂停一个步骤、调整ROI再继续；导出后改字体，应重做图而非数值，改配对应重做相关归一化。用“恢复演练”按钮模拟中断，再重开项目。迟到结果覆盖新草稿、取消已先行生效却仍成功（若最终提交先完成，必须如实返回已完成）、整批一项失败却标全成功、声称已暂停但仍改当前结果均拒收。

**RD顺序：** RD2.1串行真实WB子流程；RD2.2持久化事件与按需预览；RD2.3安全暂停/取消/恢复；RD2.4修订失效、缓存准入及迟到事件反例。

### 8.5 V3：人员可以安装并交付真实WB成果

**入口与流程：** 安装版启动到“批次”；选择实验室方法模板、导入数据与样本表，自动到“成果”；点击“导出交付包”，再用目标常用软件打开。不能要求人员进入终端或手工搬数据库。

**构建物及依赖：** 依赖V1具体方法科学准入、V2完整运行及代表负载体验证据。后端打通安装身份、版本化项目归档、导出完整性检查、升级前副本与恢复；前端增加首次模板配置、异常处理入口、成果覆盖摘要、中文诊断与图形恢复演练。支持格式、目标设备和方法范围逐项明确；未验设备不冒充支持。

**输出样例：** WB_批次01/定量.csv、归一化.csv、Fig01.png、Fig01.tif、分析说明.html、待处理.csv、项目恢复.zip。恢复包包含受控相对路径及资产清单；缺项导出明确“部分成果”，不能只改文件名伪装齐全。CSV为本切片明确承诺的表格交付；XLSX若纳入，须逐项核实已有写出能力并补内容核验，不能仅因需求写了“表格”便视为已支持。

**验收与拒收：** 按交付单在目标机器打开批次、自动出表图、用指定软件检查行列与图像、关闭重开，再恢复到新目录并定位原图。在副本升级后执行“恢复旧版备份”。缺文件、错配、乱码、原图变化、恢复后失去方法来源或仅开发机可启动均拒收。

**RD顺序：** RD3.1成果包一次完整提交；RD3.2安装后执行固定任务；RD3.3升级/归档/恢复副本；RD3.4脱敏诊断和中文错误定位。

### 8.6 V4：二维IF形成第二条完整实验闭环

**入口与流程：** “新建批次→二维IF强度”，导入保留强度的通道图与样本/视野映射，选择已批准ROI/背景模板，自动得到ROI指标和叠加图。不把Z-stack静默压成二维，也不为IF强行执行WB旋转。

**构建物及依赖：** 复用V3的资产、执行、来源和导出；新IF模块独立实现通道/曝光适用性、ROI、背景、强度端点和重复层级汇总。前端增加通道选择、叠加开关和ROI表联动；共享工作台不出现“如果工具是IF”的实验公式分支。第二消费者出现后才提取已经重复的图像读取、标尺或ROI视图。

**输出样例：** if-roi-measurements.csv、field-summary.csv、sample-summary.csv、A01-overlay.png、analysis-report.html、项目恢复.zip。字段明确通道、ROI、样本、视野、单位、背景方法和状态；视野数不冒充生物重复数。

**验收与拒收：** 点击一行回到通道和ROI，主动修改该ROI，仅相关指标生成新版；在汇总页展开重复层级。缺曝光信息而方法依赖它、坏通道映射、不支持轴序均留下具体状态。复制WB归一化公式、无背景定义、只交分割按钮或无来源汇总拒收。IF独立科学验收通过后才进入正式目录。

**RD顺序：** RD4.1通道/实体映射真实导入；RD4.2ROI强度及背景计算；RD4.3分层表图交付；RD4.4同一宿主运行WB/IF并验证互不依赖内部实现。

### 8.7 V5：计数与IF共享对象证据，验证平台复用

**入口与流程：** “新建批次→二维核计数”，明确计数对象后自动生成编号轮廓和数量；成果页提供“查看计入对象”“查看排除对象”。需要时可选拆分、合并或补标。细胞计数使用另一个方法声明，不能把核数改标题当细胞数。

**构建物及依赖：** 依赖V4实际复用证据。新增独立检测/分离/边缘排除方法与ObjectSet，引用同一图像和坐标资产；前端对象选中、轮廓编辑和计数行联动。计数对象可向已准入的IF对象测量端口传递；坐标、通道或单位不符时连接器拒绝，不能按数组形状强接。

**输出样例：** objects.csv、excluded-objects.csv、count-by-sample.csv、A01-labels.tif、A01-numbered-overlay.png；CSV每个被计入对象都能对应稳定对象身份，不只交一个总数。

**验收与拒收：** 用固定稀疏/密集样例运行，点数量展开对象列表；拆分一个对象，核对数量、对象历史和叠图同步。打开“IF对象强度”模板观察对象传递；故意接入不匹配坐标应拒绝。只测像素重合而不核验数量、静默漏掉拥挤区、修改轮廓后只改显示不改计数均拒收。

**RD顺序：** RD5.1对象和排除身份贯通；RD5.2纠正产生可追溯修订；RD5.3计数端点独立评估；RD5.4对象到IF的合法/非法连接实跑，证明公共接口可复用。

### 8.8 V6：Agent把需求变成已验证模块的执行结果

**入口与流程：** 三屏右侧“科研助手”，输入“把批次01做成WB定量表和拼图”。已有身份与模板时直接执行，并显示它选了什么方法、当前步骤和成果；确实缺参才问最少问题。用户仍可关闭助手使用模板。

**构建物及依赖：** 最低依赖V3的可靠执行，跨实验声明须取得V4/V5相应证据。后端增加意图结构化、受限计划生成、确定性连接/准入/权限/预算校验、执行观察及中断恢复；前端为任务卡和结果链接，不是独立聊天页面代替工作台。模型只调用正式工具目录，不直接写正式结果或数据库。

**输出样例：** 用户得到与模板相同的交付包；内部另有plan.json、plan-validation.json、agent-trace.json和cost-summary.json。记录实际工具版本与执行结果，助手文字不作成功凭证；诊断默认脱敏。

**验收与拒收：** 依次提交正常任务、缺参任务、未批准方法任务和超预算任务；正常任务开出真实成果，其余准确澄清或拒绝。图形按钮模拟模型服务中断，已有本地运行可继续或准确恢复。聊天说完成却无文件、重试重复提交/超支、私自上传原图、越权调用候选算法均拒收。

**RD顺序：** RD6.1影子计划不执行；RD6.2确定性校验负例；RD6.3获准计划接真实引擎；RD6.4服务断连、重试与费用上限实跑。

### 8.9 V7：算法研发产出可验证候选，再进入正式目录

**入口与流程：** “方法中心→研发新方法”，选择明确问题、授权研发样本和验收目标。页面展示实验候选、对照结果、失败样例和资源消耗；正式项目只看见已准入版本，不能把“生成成功”按钮当上线。

**构建物及依赖：** 依赖V6执行能力及独立评测/方法准入。后端增加受隔离的构建与评测执行器、固定依赖、只读输入、资源/网络权限、独立留出访问边界、候选注册与撤销；普通worker进程不冒充恶意代码沙箱。前端提供候选对照、证据缺项和晋级状态。方法审查者可读取验证证据，研发Agent不能自签准入或反复偷看留出答案。

**输出样例：** candidate-001/source/、dependency-lock、method-spec.json、validation-report.html、failure-cases.csv、resource-summary.json；实际部署再产生固定实现摘要的发布包。报告明确研发结果，不混入正式实验成果目录。

**验收与拒收：** 在准备好的隔离演练中让候选尝试写正式区、读未授权文件或超限，均被边界阻止；合法候选能重建并复算。完成独立审查后，新版本出现在方法目录；撤销后新运行和缓存采用均被阻止，旧成果保留撤销说明。生成代码即晋级、依赖漂移、无法重建或把同一评测反复调参称留出均拒收。

**RD顺序：** RD7.1候选隔离构建/限额；RD7.2对照评测与证据包；RD7.3独立准入和目录固定版本；RD7.4撤销、旧成果查看及受控重现反例。

### 8.10 用户故事：导入后拿到表和图

以下是V3以后应实现的体验，不是已完成演示。小林打开“批次”，导入仪器文件夹和实验室样本表，选择保存的WB方法。系统识别两组Fig及明确内参关系，列出将生成的定量表、归一化表和拼图；信息齐备后点击“开始处理”，不再手动旋转。

“过程”逐步出现校正图、ROI和曲线。小林点开已完成的Fig01观察，后台处理Fig02而不夺走视图。一个不支持样本变为待处理，独立样本继续；顶部显示实际完成和缺失数。若主动修改ROI，他点击“暂停并调整”，等待安全状态、拖动ROI、继续；系统保留旧修订并重算受影响分支。

“成果”中点击一行可定位对应条带与方法来源；点击“导出交付包”，在常用表格软件和图片查看器检查。若仍有待处理项，包内有缺失清单，不能显示全批成功。次日重开或恢复到新目录仍能看到同一成果；改字体生成新图，不暗改数值。

### 8.11 多人机构能力由具体使用问题触发

|触发条件|新增可运行能力|验收动作|
|---|---|---|
|同一台仪器电脑由多人轮换|操作者记录、只读历史、个人草稿、交接包；本机标记不冒充强身份认证|两人轮换打开工程，能辨认谁生成哪版，后一人不覆盖前一人历史|
|两台以上设备需同时处理同一项目|项目服务集中提交、租约/冲突处理、分析/查看/方法管理权限；客户端不直接并写共享SQLite|两客户端同时改同一修订，一个提交后另一方获冲突说明；越权读取/改方法被拒；备份在新位置恢复|
|机构确需统一升级和算力调度|固定方法目录、受控更新通道、远程任务身份、断线恢复与配额|升级试点失败可回退；远程重复请求只产生可解释的执行记录；断网不伪报成功|
|出现跨机构托管需求|再建设机构身份、数据隔离、存储/保留策略及资源计量|跨机构访问反例、删除/导出边界和资源超限均验证后，才承诺该部署范围|

每个机构增量直接接上述三屏与结果身份，不另造一套分析流程。是否采用独立服务或云组件由并发、数据边界及运维实测决定；不把更复杂的部署图当产品进展。

### 8.12 本地依据与使用边界

- [依据A：B-004实际架构核对](../../../work/evidence/B-004/architecture-audit.md)，重点§1—4、§6：已有能力、真实代码基线、四阶段调度与性能缺口。
- [依据B：B-005主计划](../scientific-agent-platform.md)，重点§8、§15—18：统一分析资产、场景端点、拟议契约与图形验收；其规划不作为实施完成证据。
- [依据C：B-004技术复核](../../../work/evidence/B-004/technical-review.md)，自动校正补充R1—R6：float入口、mask、ROI、旧历史和新方法准入。B-004早期旋转建议与最终用户指示冲突部分，以依据B和本节统一操作为准。

## 9. AI 接下来按什么顺序真正开发

### 9.1 第一轮必须交出一次真实运行

本方案取代 B-005 作为产品设计主依据；B-005 中的任务索引、规则回执与交接方法继续作为配套流程。P-001 至 P-006 的状态仍由各任务卡维护，本轮不把任何一张产品任务标完成。P-001 接入新方案时，补齐 B-006 文档/来源清单并核对目标树；B-005 的旧 transfer-manifest 是旧版本快照，不能当本方案的搬运清单。

第一轮接续以 V0 为具体交付，不以“读完方案”结束。执行顺序如下：

1. 在较新产品树确认 HEAD、dirty 和实际集成基线，保留在用版本；按该树现行规则建立实施任务并重载 context。将本方案接入文档入口，不复制本目录旧产品代码或旧规则回执。
2. 选择一个已成熟的 WB 项目分析用例，记录现有入口、请求/输出、冻结样本和异常行为。独立调用先维持旧科学语义，不夹带旋转或背景公式变更。
3. 新增最小 ModuleSpec/ExecutionRequest/OutputManifest 和 WB 适配器，通过固定 worker 调用现有用例；让请求、真实运行、持久结果贯通。第一版只注册这一个模块。
4. 用既有入口和独立入口处理同一冻结样例，保存逐项差异与失败原因。隔离安装后再运行；证明它不需要打开 WB 窗口才能得到结果。
5. 加薄的“旧方法对照”验收入口与结果打开按钮。用户能看见一次真实输出，工程审查能追到实际调用和提交；V0 到此才具备可验收形态。

随后 V1 分别推进自动估角与保精度分析契约；V2 才把真实节点接成自动流程。新模块从一个可运行竖向切片开始，再扩异常和性能。不会要求先把所有实验包、全部 UI 和完整 Agent 框架建完再见第一张表。

### 9.2 工作安排、并行与停止扩张的条件

| 工作流 | 前置 | 可并行内容 | 退出时必须留下的产品证据 |
|---|---|---|---|
| 基线/粗模块（V0） | 正确树与冻结输入 | 已有 UI 性能测量、方法验证协议整理 | 独立运行产物和与旧路径差异 |
| 自动校正与分析（V1） | V0 输入输出贯通 | 几何/位深数值验证、同源预览、真实样本采集 | 校正图+mask+ROI+数值+版本记录 |
| 可观察执行（V2） | V0/V1 可用契约 | UI 小状态投影、进程/存储故障注入 | 实际暂停/继续/取消/恢复，依赖重算 |
| WB 交付（V3） | V2，正式方法的科学准入 | 安装/升级、成果包、典型负载优化 | 用户从安装到完整表图的演示与文件 |
| 第二/第三场景（V4/V5） | V3 底座，场景输入与方法定义 | IF 和计数有共享契约后分包实现；表格路线可独立开发 | 新实验完整闭环，跨工具合法/非法连接实跑 |
| 克隆/划痕扩展 | V5 对象/mask能力、对应独立方法评估 | 可与 qPCR/ELISA 表格路线并行，按首批真实需求择先 | 各自端点表、图、失败列表及恢复项目 |
| qPCR/ELISA 扩展 | V3 表格/来源/导出底座；独立板图和样本设计 | 不必等待分割、GPU 或 Agent | Cq/浓度曲线到完整成果包，方法适用域实测 |
| Agent（V6） | V3 最低执行条件，跨工具须有 V4/V5 证据 | 影子计划与场景实现可并行 | 自然语言到真实运行；故障/越权/预算反例 |
| 算法研发（V7） | V6，独立评测与真实隔离能力 | 只在限定方法问题上做候选实验 | 可重建候选包、验证报告、准入或拒绝证据 |

一个阶段遇到真实科学样本不足，不阻止无关的存储、类型、UI 或其他已明确场景继续开发；对应方法保持研发候选。一个工具尚不能导出其最终成果时，优先补齐它的闭环，不以不断增加新菜单显示进度。IHC 全切片、流式、高维组学等大范围场景按第5章后置条件启动，不在现有 WB 任务里顺带展开。

### 9.3 每个版本交给用户怎样验收

工程团队每次交付一份“可打开的软件/入口 + 样例包 + 5–10 分钟中文操作单 + 预期成果 + 已知限制”。用户只需按操作确认是否完成实验任务；源码、事件和差异报告供开发与独立审查使用。需要真实标注或方法专业判断的部分由有资格的方法负责人完成，不把所有科学责任转给不懂代码的产品负责人。

| 验收层 | 用户能判断的问题 | 开发必须提供的证据 |
|---|---|---|
| 功能 | 我导入后能否得到需要的表和图？是否要反复手动整理？ | 固定输入→实际输出完整清单；正确和异常两种操作路径 |
| 可控体验 | 运行时能否看每步、暂停改动、继续、取消？ | 图形操作演示加真实事件/版本；迟到消息与取消竞态反例 |
| 科学可信 | 值对应哪张图/哪个ROI/什么方法？失败是否明确？ | 独立解析样例、代表样本比较、事前容差、适用域与缺口 |
| 稳定交付 | 关闭重开、恢复、升级后能否用？ | 目标环境安装、完整成果打开、备份恢复与故障注入结果 |
| 扩展成本 | 新实验是否能复用底座而不会破坏旧实验？ | 模块安装/依赖边界、旧场景回归、第二工具的真实端口连接 |

用户验收记录为待验/通过/未通过，不由 AI 代签。工程测试通过与用户尚未体验可以同时存在；不能为追求“全部完成”抹去这个差别。每次验收失败明确到行为和样例，例如“暂停后改ROI，旧结果回写了表”，再对应修复实现，不重新堆叠治理文件。

### 9.4 产品首发成功的明确终点

WB 第一可交付版本是 V3：在已声明的样本范围和目标电脑上，导入后默认自动完成校正、识别、定量、归一化和表图导出；能观察过程、处理异常、可选接管并保留来源，重开恢复可靠，具体方法完成独立验证。若仅工程闭环完成而科学或目标环境证据缺失，名称必须保留候选/试验范围。

平台初步成立是 V5：WB、IF、计数通过同一底座得到完整成果，至少一次跨工具对象传递真实运行且拒绝错误连接。Agent 初步成立是 V6：用户需求能转为受校验、可追踪的真实运行。算法研发成立是 V7：新方法有可重建实现、独立验证和版本准入；生成一段代码不算完成。

HTML 与 Markdown 源是一份设计的两种载体；后续改变架构/接口/阶段时更新源并重新生成 HTML，保留旧交付快照。任务状态不写进网页变成第二个看板。文中数值例是验收预期，目标不是让 AI 照着文字宣布完成，而是让它提交能产生这些结果的代码和证据。
