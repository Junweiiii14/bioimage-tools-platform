# Current Work Log

## 2026-10-14 / T-004 手工分析用例

上一目标回合归类 progress：93a84bb 实现并验证 TIFF/剖面。本回合实现 WB application，明确来源/revision/缺失/排除/无效/真实零/待质量复核，并支持取消无完成结果。90 测试、4 合约及隔离 wheel TIFF→手工分析通过。独审、后台进程、存储与 GUI 未完成，目标保持 active。

## 2026-10-14 / T-005 后台协议与真实进程

上一回合 progress：e3932ee/45d0c5f 手工分析。本回合实现协议 v1、strict JSON/schema、host 会话门禁与数值限线程真实 worker，123 测试及隔离 wheel 启动通过。布尔 Literal/JSON tuple 模式反例已修复且保留。合作取消不是宿主强停/存储完成证据；后续继续宿主、工作区与 GUI，目标 active。

## 2026-10-14 / T-006 工作区与恢复

上一回合 progress：bd1af2e/74e6561 后台协议。本回合新增通用契约与工作区宿主存储；164 测试、7 合约、三独立 wheel 通过。原图快照、草稿 CAS、旧运行保持修订、发布/DB 故障、3 真实 os._exit、取消竞态、同大小损坏、Windows junction/硬链接及一致性备份均验证。平台无 WB 字段，Qt/UI/强停和独审未完成；目标 active。

## 2026-10-14 / T-009 恢复并完成桌面自验
用户补充真实项目与组合图后恢复开发。增加OCR-first/独立拼图/显式跨图关联、严格OCR进程与v2保存重开、后台XLSX导出；205全量/9合约/4wheel5场景通过。高置信误读和源导出身份不明保留人工复核，不使用任务趋势优化信号。下一阶段裁剪/固定泳道/Marker/模板，T-009进入review待独审。

## 2026-10-14 / T-010 网格与原像素裁剪
在用户补充资料基础上，增加固定数量网格/人工Marker左右排除/单框原像素TIFF导出。网格保留空泳道，原像素不受预览影响，来源/坐标嵌入派生TIFF；主文档保存明确ROI，未扩展schema。wb-tool0.8.0/bioimage-app0.3.0；215全量/9合约/4wheel5场景通过。一次原生中止仍未定位，详见T-010证据。用户原/goal在暂停后明确继续，Goal已重新建立为active，无token预算；不能因当前阶段通过标完整产品完成。

## 2026-10-14 / T-011 诊断与首版验收追踪
四轮36桌面用例含GC阈值与线程生命周期探针未复现旧中止。增加桌面入口本地日志、Qt fatal显式线程栈、保留原处理器与已有faulthandler配置；真实子进程Qt致命错误证明退出前证据落盘，完整218通过。根因仍UNKNOWN，不改线程和Qt版本。整理用户方案第7–11节首版验收矩阵，T-012多原图项目/模板ready；Goal保持active。

## 2026-10-14 / T-012 多原图与Fig模板
在cfe0c56上创建feat/T-012-figure-project。新增独立项目文档/行身份、Qt批量导入去重/审核/排序/模板、后台PNG+原值TIFF+原图ZIP、CAS保存重开和复用模板新项目；旧单图v1/v2保持。全量230及隔离安装通过，用户10原图只读导入重开通过。新增契约/研究/验收证据，更新模块地图及规则回执，任务review待独审；T-013自动候选ready。未推送/发布，不把该手工阶段记为完整自动化。

## 2026-10-14 / T-013 自动候选与项目复核
在194794e上创建feat/T-013-crop-candidates。实现工程候选@1、项目schema v2快照与旧兼容、Qt后台逐图/失败继续/取消/过期保护、切换/应用/恢复/筛选和膜聚焦。原图与定量公式保持，真实10图探针暴露边缘误检后加入显式guard及回归；白背景/原导出身份不明保留。最终244全量/隔离安装通过，真实10图快照保存重开与源SHA保持；T-013 review待独审，T-014项目定量/OCR自动表ready。Goal active，未推送/发布。

## 2026-10-14 / T-014 多源定量第一阶段
从5bea9d3创建feat/T-014-project-measurements，产品提交79a675a。接通项目v3标注/run引用、固定N原图曲线/边界/基线、逐源真实进程、已提交结果自动表/XLSX、取消关闭/保存重开与过期拒绝。损坏结果逐行核验，新增通用run查询；模型/公式/平台字段不扩展。用户CLX排除说明进入契约、风险和任务。T-014仍implementing，下一步项目OCR显式绑定；整体Goal active。完整验证与失败修复见work/evidence/T-014/validation.md；未独审/推送/发布。

## 2026-10-14 / T-014 项目OCR关联
上一目标回合progress完成多源定量，本回合产品05e5d56接通项目v4独立拼图OCR、原文位置/置信度、人工校正、明确原图绑定、自动填表/XLSX及重开校验。取消保留旧关联、关闭等待退出、过期导入/识别拒绝覆盖；原图审核变化同步绑定候选。268全量/9合约/隔离安装通过，真实组合TIFF15token/11未确认行保存重开和SHA保持通过。T-014 review待独审，T-015归一化ready；用户偏好询问尚无回复，不推断科学默认。Goal active，未推送/发布；详情work/evidence/T-014/ocr-validation.md。

## 2026-10-14 / T-015 项目归一化
从9dddcba创建feat/T-015-project-normalization，产品0cd390b实现v5显式目标/参照、逐槽样本/包含/对照、比值与相对单对照/均值、Qt编辑撤回确认/自动表/OCR标签/保存重开/XLSX。派生值从核验run重建，无epsilon或静默丢坏对照；v5可无OCR，旧v4约束保持。284全量/9合约/隔离安装通过，源码Qt截图已查看。T-015 review待独审，T-016生成PNG衔接ready；用户偏好仍未知，Goal active，未推送/发布。证据work/evidence/T-015/validation.md。

## 2026-10-14 / T-016 完整生成拼图与PNG OCR
从5cf7c71创建feat/T-016-composed-figure-ocr，产品1d5ae2a新增PNG专用解码/已知预处理、完整PNG生成/来源/异步字节导入、真实OCR复核自动表、单图PNG入口。保留原图/归一化，取消与过期保存/成图不覆盖编辑；诊断发现成图错误被刷新覆盖，改为合并计时和错误保留。304全量/隔离安装通过；真实用户组合TIFF的独立PNG显示副本15token/11未确认行、源SHA保持、保存重开一致，两个Qt截图已看。T-016 review、T-017批量元信息/缩略图ready；整体Goal active，未独审/推送/发布。

## 2026-10-14 / T-017 批量元信息与缩略图
从0c8fc3f创建feat/T-017-project-metadata-batch，产品9ea4089实现有界只读XLSX/CSV、明确完整键匹配/可改预览、显式行字段选择、共同值与文件名分段原子应用，以及后台128边缩略图/坏图继续。v1–v5和积分保持，N/空位变更沿既有有效性撤回审核，保留历史run/OCR/归一化。335全量/隔离安装通过；真实表1张50×49/190公式、47提议0绑定0应用、2原图缩略图/重开，源SHA保持。关闭导入回退按旧测试修复；另一次全门禁停滞未复现/未定位，保留风险。T-017 review、T-018统一结果CSV/归档ready；Goal active，独审/发布仍未完成。

## 2026-10-14 / T-018 CSV与统一结果归档
从ba8a678创建feat/T-018-project-result-archive，产品c5f5787接通源/OCR/归一化CSV与XLSX共用表、原值资产/裁剪/PNG/当前配置/原始请求结果的统一ZIP v2。保存后逐个核对工作区run和资产并后台重读，不用旧缓存冒充；成员SHA/大小/角色与坏run原因明确，取消/关闭/代际和无覆盖保持。364全量/9合约/隔离安装通过，作者自验不替代独审；T-019准备有界ZIP检查/恢复与历史证据保留。Goal active，未推送/发布，用户原资料未改。详情T-018/validation.md。

## 2026-10-14 / T-019 ZIP恢复与历史证据
从f79b7b3创建feat/T-019-project-archive-restore，产品6a06369实现schema6历史来源/原ZIP/复制请求结果、有界普通/ZIP64检查/表与像素重建、专用线程新工作区恢复/初始修订快照、重开核验/编辑失效/真实复算及再次恢复。398全量124.27秒、Ruff244、Pyright0、9合约、4wheel5场景通过；旧Qt/停滞风险未宣称解决。T-019 review待独审，T-020直接TIFF/PNG成图ready；整体Goal active。未推送/发布、用户资料未改；详情T-019/validation.md。

## 2026-10-14 / T-020 直接成图
从3a38af6创建feat/T-020-direct-figure-image，实现完整RGB8 TIFF/PNG直接输出、来源/DPI与像素重读核验、原图/字体声明大小检查、已知显示TIFF拒绝定量而OCR允许。Qt精确保存后后台导出，取消/关闭/修改与已发布文件状态有回归；425全量143.71秒、Ruff251、Pyright0、9合约、4wheel/4个隔离环境通过。真实组合图格式探针原SHA/显示像素保持，OCR17token未确认/绑定，Qt与导出截图已看。T-020 review待独审，T-021实验室版式/横向分段ready；Goal active，未推送/发布。详情T-020/validation.md。

## 2026-10-15 F-003

补长期维护矩阵、技能/REA初评和PR诊断，保留T-021产品改动。网络故障阻断安装与远程修复；旧快照已归档，当前指针按真实分支纠正。

## 2026-10-15 F-003续办完成

网络恢复。两技能固定SHA安装/锁及许可，Impeccable引擎SHA/默认启动器验证。REA6.5.0隔离静态Electron分析/追踪通过，篡改记录按预期拒绝，覆盖partial。PR #5独立目录补回执并推送ac75f6f，四项CI全通过。未合并/发布、未动T-021产品内容。

## 2026-10-15 / T-022 前端与视觉参考

用户确认四步工作流，随后要求同时使用新装两技能并提高精致度；最终明确旧WBQuant仅外观布局相似，不保留旧操作。使用Impeccable原生Operate和Taste实际方向抽取；源码Qt迭代至32a2d18。保留原主目录dirty，复用协调worktree/codex/t022-workflow-ui；作者与独立审查分开。f71083b全门禁498通过，最后布局32a2d18专项17和独审/截图ship；最终检查见T-022/validation。新合成演示与使用说明在.local/deliveries/WB-workflow-20261015，旧F006报告不覆盖。未推送/发布，不声称真实科学与最终包态验收。

## 2026-10-15 / T-023 全新UI候选

用户要求完全重新设计，先给候选再实施。复用协调worktree，新分支codex/t023-ui-candidates从059d01b开始。用Impeccable Operate及Taste制作A证据工作台/B清晰实验流程/C图像专注静态稿；三张1440×900真实浏览器截图已看，图像全为合成示意。正式前端/科学规则未改，DESIGN与PRODUCT新系统尚未锁定。用户可从选择页0ea9eab8或聊天回复选择；实施必须等其选择。任务T-023/证据为唯一状态。

## 2026-10-15 / T-023 A证据工作台

用户选择A，正式Qt改为顶部横导航及来源参数/原图曲线/复核结果三栏。双向编辑、SHA切源与ROI失效回归补齐；原图坐标/科学值不变。产品0d9aad94，独审15项8.13s通过；视觉13图有效，两项修复resolved。独立合成演示及报告在.local/deliveries/WB-evidence-20261015。最终门禁详见T-023 validation。未推送/集成/发布。

## 2026-10-15 F-007 产品目标纠偏
用户停止操作教学，要求工具平台与 WB 自动化进度解释。核对实际入口、空积分边界初始化、裁剪候选及验收表，确认平台可见入口和自动化主流程未完成。停止以精准坐标教学推进；更新 F-007、snapshot 和进度报告。原代码/输入未改；未跑产品测试。规则回执、diff 检查及 handoff 容量检查退出 0。

## 2026-10-15 T-024 平台与自动化闭环

按用户纠偏实现真实平台、自动识别/裁剪/积分与完整输出；三独立worktree子代理集成至16f3877。真实10图5检出21泳道、5未检出，所有质量状态保留。532全门禁/193.25s与五缺陷修复独审通过；真实5视图完成两视觉修复复核。科学真值/完整配对/包态及PR集成未完成，未发布。

## 2026-10-15 T-028 全面 UI 审核与方案

用户要求自动建目录、选图即处理，但明确所有产品变更待方案审核。Taste实际抽取product-performs，Impeccable独立A/B审核及8页真实Qt补拍完成；启发式18/40，不是功能准确率。报告work/evidence/T-028/UI全面审核与改版方案.md；critique helper存档成功，trend仅当前一次。未改产品代码/PRODUCT/DESIGN，任务awaiting_user_review。临时ZIP恢复独立项目，未改原图和交付结果。

## 2026-10-16 T-029 已批准工作台实施

按批准方案以协调树+T030/031/032子树实施自动项目入口、三模式图像工作台与上下文工具。实际10图自动输出和原图SHA一致，独立代码/视觉纠正保存上下文、撤销、结果刷新；最终取消/缩略图修复及11b1d96绑定独审通过，560全门禁+后续专项回归通过；核心交付，剩余项显式保留。真实记录见work/evidence/T-029/validation.md。

## 2026-10-17 T037

完成WBQuant1.4.3数值/表格对照及Fig组同源定量监督。用户明确裁图→Fig标注拼图→组定量；图框映射原图，各蛋白分段积分。最终9be19b1代码独审通过、视觉ship、文档同步。594完整门禁与后续重开专项通过，真实桌面已打开；前轮失败和局部门禁范围保留work/evidence/T-037/validation.md。

## 2026-10-17 T-041 标准显示

- 新显式standard_lane_ratio@1和DisplayFrame，仅显示RGB8重采样，manifest含原ROI/输出框/仿射矩阵，原生默认冻结hash保持。
- 目标88测试、Ruff、strict Pyright通过；独审/全仓/真实8图未运行，交协调任务。详见work/tasks/T-041-standard-display.md。

- T041独审P1：禁止部分泳道段携带完整行display_frame，新增重复三泳道负例；31专项通过，详见任务。

## 2026-10-17 T040
Executed approved real dataset, published8no-overwrite named crops,4Fig images,48supervised observations/Excel/ZIP and reopened real desktop. Preserved first failed automatic predictions and old integrals. Integrated display-only standard frames and source overlays, independently reviewed throughf7a6651. Detector/baseline shortcomings and fullcheck abnormalexit remain explicit; see task/evidence.

## 2026-10-17 T040 deep technical audit
Three independent readers traced crop/quant/pipeline and cross-reviewed17-section report. Source-only membrane/Marker and17boundary replays exit0, original hashes unchanged. Corrected prior vague attribution, documented script-vs-product and scientific/units/precision/coordinate/model-validation limits; no product modifications. Fullcheck not rerun for this report.


## 2026-10-17 T042 实现与真实网页验证

社区原始来源调研、几何与背景策略已接现有网页工作台；8图独审8/8，原图旧结果保持，web3正常8run保存重开及48网页结果验证exit0。发现并修复Marker显式误删、ROI旧frame、同框重算frame、双峰漏警、worker质量flag。误开旧Qt测试入口已纠正；无web_ui设计变更。完整门禁/最终独审进行中，详见T042任务和validation；未发布。
