# B-004 实际产品结构与目标能力核对

核对日期：2026-10-31。性质：只读源码与既有证据审计，没有修改产品、运行产品验收或验证科学准确率。下文“已有”表示在准确提交源码或既有记录中有实现/证据，不代表本轮重新验收。

## 1 版本基线

- 报告工作目录：`<原调研工作区；以记录的分支和HEAD定位>`，分支 `feat/T-021-laboratory-figure-layout`，HEAD `bb5601addda64fa96fa007612ceda0a0e1ed9b74`；存在既有 dirty 内容。不能据此目录旧代码断言最新产品能力。
- 本次实际审阅产品树：`<原调研工作区；以记录的分支和HEAD定位>`，分支 `codex/t082-reliability-remediation`，HEAD `dfc48ed7c2c944dc8f03c3931bc7985452a31393`。2026-10-31 独立执行 `git status --short` 为空，clean。
- 冻结产品源码/构建源：`ed830e1d3bab3d0c8c57f3766a898991e8a0f431`。`git diff --stat ed830e1..HEAD` 仅19个文档/交接/证据文件，没有产品源码差异。
- 既有 T082 记录：1503 项测试、四包 isolated wheel 与本机 Windows 11 最小安装矩阵通过；本轮只阅读这些记录，没有重跑。T082 任务仍有独立科学材料/负责人判定和外部目标环境未验，整体未完成。
- 最近在用交付为 T081 R2，产品 `f1e6142`；T082 验收安装身份已经卸载，未替换 Laboratory。不要把三个版本写成同一个“当前发布版”。
- 实际成员仅 `apps/desktop`、`tools/wb`、`packages/tool_contracts`、`packages/platform_runtime`；包版本分别0.14.0、0.19.0、0.1.0、0.2.0。`desktop_sdk`、`imaging_core`、`imaging_ui`、IF/IHC尚未创建。包版本不能替代提交号识别代码。

出处：最新树 `README.md`；`docs/module-map.md`；`work/tasks/T-082-reliability-remediation.md`；`work/evidence/T-082/final-handoff.md`；各包 `pyproject.toml:3`。以下源码位置均相对此最新树，引用时可拼接上方绝对路径。

## 2 WB 实际上已经不止灰度积分

| 用户可得到的能力 | 已有实现与证据 | 要保留的边界 |
|---|---|---|
| 导入仪器批次、保留来源、按Fig和蛋白组织 | instrument_intake、intake_grouping、export_discovery；当前模块地图“仪器导入与分组” | 文件名和同名蛋白不证明实验配对；候选不自动成为事实 |
| 原图定位、固定N裁图、槽位与空位保留 | `domain/prominent_band_geometry.py`、`domain/fixed_lane_frame.py:29`、`application/intake_crop.py`；workflow@5 | N由人员明确给出；不按检出数补造样本；不支持情形应失败或待复核 |
| 手动裁剪、显示旋转、执行后修正 | `application/intake_crop.py:715`；`application/intake_revision.py:218` | 当前显示角度与测量几何分开，旋转后的RGB8显示数组不进入定量 |
| 拼图、字体、蛋白/Fig标签、分段和模板 | `application/laboratory_layout.py:21,60,81`；`adapters/laboratory_figure.py:212` | 图示分段/重排的来源可追溯，不能伪装成连续原图 |
| 曲线、背景边界、峰纳入与原始/有效信号 | `domain/lanes.py:47`、`domain/quantify.py`、各quant_policy；`docs/contracts/wb-fig-quant-v1.md` | 固定科学定义是原像素逐行均值、线性基线以上正残差梯形积分，不乘泳道宽 |
| 显式内参和对照归一化 | `domain/normalization.py`、`application/project_normalization.py` | 内参是否稳定/是否在线性范围不由软件自动证明；坏分母不填0 |
| 拼图OCR、原文校对、明确绑定表格 | `application/project_ocr.py`、`adapters/ocr.py` | 识别不是正确身份的保证；本地OCR能力不等于科研Agent |
| 表格、PNG/TIFF拼图、逐Fig交付和恢复包 | `application/intake_output.py:200`、`application/intake_delivery.py`、`adapters/intake_output.py` | 输出保留身份/状态/来源，不覆盖原图和历史输出 |
| 保存、重开、历史、备份与恢复 | `platform_runtime/Workspace`、归档/恢复适配器 | 外来历史证据不冒充本机成功运行；未知running重开为interrupted |
| 自动顺序执行和人工复核后继续 | `application/intake_workflow.py:28,161,303`；宿主 `intake_workflow.py:494` | WB专用四阶段调度，尚不是任意模块的通用DAG |

因此“WB功能闭环已较完整”有源码和工程记录支持；“WB已经科学验收完成或可向任意实验室承诺准确率”不成立。`work/evidence/T-082/scientific-baseline.md:3,28` 明确没有独立留出和负责人比较约定。新报告不应为了扩展平台，把尚未证明的可靠性写成商业卖点。

## 3 现状与目标的具体差距

| 目标 | 当前真实状态 | 需要的增量 |
|---|---|---|
| 独立模块重复使用 | WB公开 `wb_tool.api`、domain/application/adapters/ui分层；四包隔离wheel | 为成熟用例增加稳定的模块描述、输入输出/资源/取消能力和方法版本；先粗粒度，第二场景验证后提取共性 |
| 任意有向无环工作流 | WB `Stage = Literal["crop", "compose", "measure", "export"]`；依赖按Fig/蛋白专门计算 | 新通用流程描述与验证器、节点运行记录、依赖失效和调度；WB逻辑留在WB节点/子流程，平台不加入实验特判 |
| A 运行前调整 | 已有清单、N、极性、ROI、策略、模板等输入和显式确认 | 每节点参数表单从同一严格schema生成，运行前显示方法/来源/预期输出和变更影响 |
| B 节点等待人工处理 | 已有needs_review、未完成裁剪屏障和明确继续 | 通用ReviewTask与审核凭证；绑定run/node/attempt/input digest/参数/方法版本，恢复后可继续；不能把“停止排程”说成正在运算的算法已经暂停 |
| C 完成后修改和部分重算 | 已有分组修订、裁剪修订和Fig级失效；标签改动在数值请求全等时可复用旧run | 一般DAG上按语义依赖求后代失效集合；分离数据依赖与显示依赖，保留旧分支；相同标签不能作为复用键 |
| 任意步骤中间图/曲线 | 已有后台预览、阶段提交投影、curve/quant页面、progressChanged | worker protocol v2增加progress/preview/checkpoint/heartbeat等消息；只传资产引用，做背压/合并与序号保护 |
| 暂停、继续、取消 | 当前批次可停止/继续和等阶段退出后改草稿；真实worker具取消和退出仲裁 | 新节点声明pause=between_nodes/checkpoint/unsupported；运行中暂停由算法协作检查点实现，否则明确“完成当前步骤后暂停” |
| Agent组流程、执行 | 静态WB/OCR worker注册；没有Agent服务、模块检索/计划审批/预算机制 | 新规划层输出受限流程JSON，经确定性验证器和权限仲裁后执行；Agent不直接写数据库或把聊天文字当成功 |
| Agent开发算法 | 没有算法生成、隔离构建或模型/代码晋级平台 | 独立开发环境、固定依赖、禁止生产凭据/默认网络、测试和科学验证、签署版本晋级；正式运行只加载批准的不可变包 |
| 云/本地切换 | 当前Windows离线Python/PySide6/QtWebEngine+worker | 运行位置适配器和能力/数据策略；云端还需账号租户/对象存储/队列，不能把本地SQLite文件直接共享成多租户服务 |

## 4 是否需要架构大改

判断：需要对“编排、模块契约、事件与审核”进行中等至较大的局部架构建设；没有证据支持推翻WB数值核心、工作区事务或桌面技术栈，也不宜继续把所有新实验和Agent能力堆入现有WB宿主。

应保留：原图/结果不可变与SHA校验，Workspace CAS和结果提交仲裁，原始/显示数据分离，既有WB数值与历史读取，安装与wheel边界，现有QProcess/后台存储生命周期。`tool_contracts.api:55,78,97` 已有AssetRef/RunRecord/退出凭证；`platform_runtime/workspace.py:366,468,566,580,618` 已有草稿CAS、冻结运行、取消和提交机制，是可复用基础。

应新增：通用模块清单与能力声明、流程定义/节点尝试/审核记录、输入输出类型与方法版本检查、事件订阅和预览资产服务、受限Agent工具目录、隔离算法研发及晋级记录。它们不能从现有WB schema继承链机械扩展出来。

应逐步拆分：`apps/desktop/.../intake_workflow.py` 将宿主I/O调度和WB专属逻辑交织；新工作流不要继续增加其实验分支。`web_bridge.py` 当前构造WB整项目快照，逐步换成有边界的模块视图投影和按需资产/表页。`WBJob` 在 `application/desktop_data.py:59` 是大量操作加可选字段，未来新增链路优先采用每操作的严格请求类型，不为统一而重写53个历史操作。

现有schema1–15链保留兼容读取。新通用工作流工程采用新的版本化文档模型，通过WB适配器引用旧工程；显式迁移时备份、建立映射、双读比较。不要把每种实验再加成第16、17层WB继承。R12证据显示旧链尚无必须全面重写的已复现缺陷，新跨工具需求才是新增组合式模型的理由。

可触发更大改动的证据：两个独立实验仍无法通过同一契约接入；宿主频繁出现实验特判；事件/数据传输测量表明现UI边界无法满足目标；确有多用户远程协作和权限需求。文件长、AI热门、已有15个schema本身不构成重写理由。

## 5 旋转必须按用户目的分两条路径

当前实现已经明确区分。`intake_crop.py:715–735` 写明人工角度只改变display sampling；`laboratory_figure.py:228–244` 使用RGB8仿射双线性与LANCZOS显示重采样。`fixed_lane_frame.py:1–4,42–45` 则说明原图测量区域是互不重叠的轴对齐矩形，不宣称等于旋转多边形。`lanes.py:47–63` 直接对原uint8/uint16矩形逐行求均值。

因此现有“看起来拉正”不能写成“已经完成参与定量的几何校正”。显示框旋转与定量区域可能有可解释但需要提示的几何差别。

建议工作流里把节点命名分清：`figure.rotate_display`只产生DisplayAsset和原图坐标映射，不能连接定量输入；`image.correct_geometry`若确有需求，必须是新的科学方法版本，明确原坐标ROI/掩膜路线或强度重采样路线、插值方法、边界填充值、像素面积、有效区域和定量偏差。先比较原图掩膜/方向剖面是否满足任务，再决定是否重采样；不预设旋转后数值必然守恒。

修改角度是否影响后续计算由依赖类型决定。现有 `revise_completed_intake_crop` 会保守撤销所属Fig compose/measure和当前export，即便传入display_angle；未来纯显示改动可仅重渲染，但必须证明数值请求及其完整源摘要不变，不能直接删除失效保护。

## 6 流畅交互的关键不是再加一个转圈动画

已有Qt异步存储、worker进程与后台解码；`process.py:18–20` 事件目前仅hello/accepted/result/failure/cancelled，`process.py:13–14,65–80` 单帧4MiB、总流8MiB、最多8帧。此协议不能直接承载持续进度流，需显式v2/独立遥测通道及新预算，不能悄悄删除旧上限。

`web_bridge.py:202–206` 每180ms检查更新，`publish:563–625` 先发小进度，键未变时跳过全快照；不是每180ms无条件重建。`web_ui/motion.js:1–4,21–40` 已有每节点可取消动画、不会阻塞命令，并尊重系统reduced-motion。可继续使用。

真实已有性能证据不应遮掩：R09前后同合成数据，本机软件渲染，30样本+5预热。行式512×96热构造+JSON p95 657.76→144.83ms，点击1221.5→512.4ms；仪器512×96为824.30→207.28ms、2162.9→1233.7ms；载荷仍15,190,523B和27,149,399B。小行式点击177.2→234.8ms有回退且归因未知。不是实测客户日常规模，private采样不是全程峰值。这些数据支持先改投影/分页/图片引用，而不支持把动效当性能优化。出处 `work/evidence/T-082/r09-disposition.md:5–17`。

建议事件分级：状态/终态/审核/错误必须可靠有序；高频进度和预览可合并、限频、只保留最新。运行中显示真实阶段/已处理数/最近更新时间，未知剩余时间不编造百分比。中间图标“预览，尚未提交”，提交完成后再显示“已保存”。用户选中旧步骤观察时保持视图焦点，不被自动跳转夺走。

暂停与修改流程：点击暂停立即反馈请求已接收；停止发新节点；支持检查点的节点保存检查点后进入paused；不支持者显示等待当前步骤结束；修改产生新草稿/新分支并重新确认失效范围。取消先持久化cancelling，等待受管进程/后台退出与清理，再发布cancelled；结果晚到不能覆盖新草稿。`RunSession:73,134` 与现有终态CAS应复用。

## 7 Agent应成为受控规划和研发层

建议层次是自然语言需求 → 任务规格与澄清 → 选择已批准模块 → 严格流程JSON → 确定性校验/预览影响与数据去向 → 人员批准需要的动作 → 现有运行基础设施 → 结果和出处解释。Agent没有重写正式结果的权限。常规已授权流程可按机构策略自动执行，不必每一步反复弹确认；数据出域、方法变更和新算法晋级需要各自明确规则。

算法研发与实验数据运行分离。研发作业只拿授权/脱敏/合成数据副本；独立只读输入、临时输出、CPU/RAM/时限/网络限制、固定依赖和环境摘要。普通QProcess/Windows Job Object仅提供进程生命周期与资源管理，不等于对恶意生成代码的安全沙箱。当前LocalAssetFilter与本地页面导航限制（`web_window.py:36–61`）也不能替代算法隔离。

算法晋级最低证据：任务/适用范围、来源和许可证、算法及参数schema、解析/性质/反例测试、资源与失败测试、独立留出与方法负责人预先约定指标、对旧版本差异、依赖/权重SHA、审查记录、可回退版本。编译通过或AI自评通过不足以进入正式目录。算法生成、复现、改进与原创性声明分开；公开论文的复现代码不自动成为新发明。

## 8 可执行演进顺序

1. 冻结WB兼容基线和科学验证计划。先保住现有原图→表格/拼图/恢复包闭环；邀请方法负责人确定实际留出和比较设置。
2. 抽一个成熟WB粗粒度用例为headless模块，并保持单工具入口。用模块manifest声明输入原值类型/坐标/单位、输出、版本、预计资源、cancel/pause能力。
3. 建小型串行/有限分支流程与ReviewTask，复用Workspace/RunSession；验证A/B/C、晚到结果、重开、取消、磁盘满和双分支，不先制作万能拖拽画布。
4. 选一个有真实设计伙伴的二维IF强度或细胞计数场景验证第二消费者。方案中可比较候选，但不宣称已完成选择/科学语义。
5. 将桥接改为阶段事件和分页投影，建立代表数据/目标电脑的交互分位数与内存测量；验收运行中观察和暂停，动效仅表达状态。
6. Agent先只组合批准模块并解释选择；验证自然语言到流程的正确率、拒绝不支持任务、成本和误操作边界。
7. 最后增加隔离算法研发与人工晋级，云端/院内/本地采用相同契约与各自权限策略。

本轮没有新增依赖、改科学公式或发布代码。上述是技术建议和差距判断，尚未形成实施任务或工期承诺。

## 9 本轮命令与限制

- 只读 `git worktree list --porcelain`：exit0，定位最新工作树。
- 沙箱内 `git -C <最新树>` 返回Permission denied；随后经只读沙箱外命令 `git status --short; git branch --show-current; git rev-parse HEAD`：exit0、clean/分支/HEAD如上。没有进行写入。
- 只读 `git diff --stat ed830e1..HEAD; git status --porcelain=v1`：exit0，仅文档/证据变更、clean。
- 使用Get-Content/rg读取上述源码、契约、README、既有测试和验证记录；几次猜测文件名不存在后通过rg --files定位实际文件，没有以空读取作判断。
- 未运行doctor/check/smoke-env/policy/audit、新产品单测、GUI操作、性能测试、安装验收、真实样本科学比较或安全渗透测试。既有记录的1503测试和性能值均明确标为历史证据。
