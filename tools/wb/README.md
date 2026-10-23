T077：intake_visible_table@1 是可见原始积分宽表的独立显示/导出投影，旧归档表语义保持；实际验证及限制见 T077 任务与可见结果表v1契约。

T075新增工作台明确修订公开用例 prepare_workbench_revision / apply_workbench_metadata / revise_workbench_figure_order；不改变算法与项目schema，保留历史并撤回相应阶段批准。契约见 ../../docs/contracts/wb-workbench-revision-v1.md。

T074 当前增量与契约：`../../docs/contracts/wb-intake-supervision-v1.md`。下列为既有版本说明，不代表本轮验证。

T061新增清单v2的导出组/来源角色/信号区域与未知N建议；显式集中确认后接既有固定N裁剪，保留原图复核。旧清单v1字段/摘要保持。公开契约见 `../../docs/contracts/wb-export-discovery-v1.md`。

E3 implements `intake_crop@1` / schema12, preserving explicit N and stable slot IDs even
when original geometry is unlocated. Automatic proposals remain unreviewed; an explicit
original-coordinate rectangle confirms fixed-N segmentation. Reviewed crops export the
original TIFF samples through an owned active ticket, with no overwrite or premature
measurement. Source geometry thresholds and quantitative algorithms are unchanged.
See `../../docs/contracts/wb-intake-crop-v1.md` and `../../work/tasks/T-056-fixed-slot-cropping.md`.

# WB 数值核心

T072 adds versioned `intake_crop@2` geometry acceptance for explicitly started whole
batches. Machine acceptance retains `reviewed=false`, exact original slot geometry,
and original-sample crops. Existing oriented frames feed display-only straightening;
manual angle edits and reset retain quantitative source coordinates. Old @1 evidence
and project schemas remain readable; older readers reject the unknown @2 policy.
Contract: `../../docs/contracts/wb-intake-automatic-crop-v2.md`.

T065新增明确执行后裁剪修正 `revise_completed_intake_crop`：新修订只使所属Fig及当前输出过期，旧修订、运行和产物保留；见 `../../docs/contracts/wb-intake-revision-v1.md`。目标区域由采集组明确选择并传入原坐标固定N复核，不自动成为已审核结果。

T064清单v3支持采集组草稿，未知N/未选源可持久化，完整组投影到原有稳定执行身份；原清单v1/v2 wire shape和历史编辑入口保留。公开契约见 `../../docs/contracts/wb-intake-grouping-v1.md`；实现/验收状态见任务，不把草稿保存等同科学确认。

E3/T056已完成宿主接入、本机工程验证及绑定独审：schema12/intake_crop@1保存固定N槽位与原图几何建议，
无定位仍保留完整槽位，不伪造坐标/测量。显式审核后通过既有原值TIFF适配器导出，
schema1–11读取保持；契约见`../../docs/contracts/wb-intake-crop-v1.md`。
E4/schema13连接完整Fig后原像素定量，E5/schema14连接身份填表、新目录导出与恢复；E6复用冻结渲染。实际阶段证据与外部验收边界见`../../docs/wb-execution-acceptance.md`，不以纯核心测试代替宿主/安装验收。

T055/E2新增schema11清单阶段账本，保存行crop/完整Fig compose/measure/项目export依赖、
尝试票据、取消请求及中断恢复；账本不代替已提交数值证据。桌面后台准备执行摘要，
未执行时可返回清单修改；真实裁剪执行器已在E3接入。契约见
`../../docs/contracts/wb-intake-workflow-v1.md`。

T054/E1新增`build_intake_execution_plan`：从已确认schema10重建不可变槽位、
安全相对路径、布局占位和pending/None表格；无I/O/OCR/定位/测量。
派生计划不增加持久化权威，后续结果另行版本化。契约见
`../../docs/contracts/wb-intake-execution-v1.md`。

T051新增`WBIntakeProject/schema10`与仪器原图池、稳定Fig/蛋白身份、固定槽位数、
显式批量分配及确认摘要；未分配来源和原名/相对路径可保存重开。
T051当时仅覆盖导入规划；后续E3–E5已接通执行。清单确认仍不等于裁剪审核或产生定量；旧独立灰度OCR保留。
公开API和兼容约束见`../../docs/contracts/wb-instrument-intake-v1.md`。

T045增加完整泳道手动框选、共享原图分组、补峰/排除及schema9 Fig拼图定量。
`WBPartitionProject`保留原图OCR与版本化机器建议；普通WBQuant多峰和UB整段共用
已有积分。新契约`../../docs/contracts/wb-fig-quant-v1.md`，验证状态以T045任务为准。

公开入口 `wb_tool.api`；包版本0.19.0，实现定量/手工Qt闭环、OCR复核、结果表、归一化、批量元信息、统一归档和明确分段版式。
数值契约与参考来源见 `../../docs/contracts/wb-reference-v1.md`。

- 输入：未平滑且已声明极性的非负有限剖面、闭区间 `BandBounds`、可选 `Baseline`。
- 输出：不可变 `ProfileMeasurement`，含信号、边界、基线来源、算法和单位。
- 失败：`QuantificationError`；有效平坦区域返回真实零值，未检测状态由后续用例表达。
- 数值领域不读文件、不依赖 UI、不推断蛋白身份、不乘泳道宽度。
- `load_tiff` 支持单页 uint8/uint16 灰度与 RGB/不透明 RGBA，保留原文件与位深；
  RGB 使用整数 BT.601，MINISWHITE 不静默反相；多页/透明/非左上方向明确拒绝。
- `compute_lane_profiles` 需要显式 dark/light 极性与稳定 lane_id，坐标为半开矩形。
  读取数组以 bytes 为后备，不能重新开启写入；均值以 float64 计算，不修改原像素。
- NumPy 和 tifffile 依赖均固定为已有锁版本，不引入新的第三方包。
- 协议使用已有锁版本 Pydantic 2.14.1；`python -m wb_tool.worker` 是单任务后台入口，
  stdout 仅为 UTF-8 NDJSON，容量/身份/顺序/取消规则见 `../../docs/contracts/wb-worker-v1.md`。
  worker 返回结果候选，不提交数据库或宣告宿主成功。
- `analyze_annotations` 接受来源摘要、revision、泳道/条带不可变标注，返回明确定量状态；
  取消或来源不符不返回成功结果，部分泳道失败保留原因；位深上下限像素触发复核，
  待复核原始积分不能进入有效信号列。契约见 `../../docs/contracts/wb-manual-analysis-v1.md`。

验证：仓库根 `uv run --locked --no-sync pytest tools/wb/tests -q`；
完整门禁 `uv run --locked --no-sync python dev.py check --all`。

`[desktop]` 可选依赖使用已有锁定Qt；普通API/worker导入不加载Qt。
create_wb_view/create_wb_background 是延迟装配入口；PreviewRaster 是显示专用字节，
不会传给定量用例。WBDocument v1 保存原输入资产/标注，契约见 wb-document-v1.md。
后台关闭排空已接受请求后，由worker在自身线程移回owner，再停止原QThread；
owner非阻塞确认线程退出和实际QObject销毁后才发送closed，避免跨线程析构的Qt锁/GIL反转。
隐藏兼容控件也须明确归属View；宿主排空完成不等于窗口已经析构。
独立进程生命周期回归验证父对象销毁后子控件释放和真实退出码，不对全局测试窗口强制清理。
`ManualQuantTarget/configure_manual_quantification` 提供不依赖自动裁膜/拼图的人工测量目标，
复用已有schema7逐行高度及正常worker；相同目标保留人工参数，显式重置才恢复边界。
契约见 `../../docs/contracts/wb-standalone-quant-v1.md`，旧运行/原图保持不可变。
桌面入口由apps显式装配：`uv run --locked --no-sync python -m bioimage_app`。
当前界面可拖ROI/编辑闭区间与基线/查看原始曲线、OCR原文和自动结果表。

可选`[ocr]`固定RapidOCR3.9.2/PP-OCRv6/ONNXRuntime1.31.0/OpenCV5；普通API不加载OCR/native模型。
recognize_figure校验模型后本地CPU识别，suggest_figures/propose_worksheet只给未确认的空间建议。
Worksheet保存明确Fig/行/列与lane/band关系；fill_worksheet保留失败/缺失/排除与零值差别。
export_worksheet输出新的XLSX，Windows采用无覆盖rename发布，POSIX采用link；字面名称不成为公式。
0.7.0已接入OCR worker、Qt复核表和v2文档；可以先识别后画ROI，或关联另一张拼图。
跨图由用户指定lane/band，禁止按像素坐标猜配。布局建议@2支持短编号、主标签列与并排重复标签，原OCR不丢弃。
v1草稿继续读取，协议/文档契约见wb-document-v2.md。自动裁剪、模板拼图、项目批次及完整产品验收仍待完成。

0.8.0增加fixed_lane_grid、CropRequest/export_crop及桌面框选模式。固定N保留空位，左右Marker排除由用户给定；新TIFF裁剪保持原通道/位深/像素，内嵌来源和半开坐标记录。详见wb-crop-grid-v1.md。当前导出所选单框，整行可用单框模式标记；不是自动膜/Marker检测或模板合成。

0.9.0新增独立WBFigureProject v1和FigureRow/Template、plan_figure_layout、render_figure、export_figure_bundle。多原图批量去重、固定N整行审核、Fig/蛋白排序、模板保存/复用、后台预览及新ZIP导出（PNG/记录/原值TIFF/原图/字体）。使用[figures]可独立渲染，desktop也显式声明已锁Pillow12.3.0，普通API仍不加载Pillow/Qt。旧单图v1/v2不变。契约见wb-figure-project-v1.md。

0.10.0增加CropDetectionSettings/detect_crop_candidates/suggest_crops，以及CropSuggestion/WBReviewProject和read_figure_project。候选算法@1在私有数值副本定位膜、左Marker排除槽、固定N网格和条带行；弱/可能空/多候选/回退均需复核。项目首次记录建议升级为schema v2，原v1继续读取，旧单图文档不受影响。Qt后台逐图检测/取消、失败筛选、候选切换/应用/恢复和膜区域聚焦；仅应用建议才写ROI并撤销审核，手动空位元信息不被覆盖。建议与参数/源SHA/源修订/原图提示随草稿和ZIP保存；更改N或高度须重新检测。显示聚焦仍输出原图坐标，不改变像素。契约见wb-crop-suggestions-v1.md。项目级OCR/定量/归一化、完整人工标注准确率及产品验收仍待完成。

0.11.0连接多原图定量：WBAnalysisProject/schema v3保存固定N标注和已提交RunRecord引用，继续读取v1/v2。边界初始为空；明确dark/light、闭区间边界、人工或端点基线，复用原积分与曲线。空位强制排除；源/几何/审核变化使计划过期，参数修改清除当前run，名称和排序不改变测量。后台结果校验/自动项目表/XLSX保留原图SHA、row/lane/band、请求修订与运行身份，缺失不填0。项目UI每页显示200泳道，结果资产加载预算64 MiB；未载入结果不给有效值。CLX按用户说明排除。契约见wb-project-analysis-v1.md。

0.12.0新增WBProjectOCR/schema v4，继续读取v1/v2/v3：独立TIFF拼图OCR原文/token位置/置信度、可改Fig/蛋白、人工补行、明确关联原图row_id/SHA/ROI/N、确认后自动填表及XLSX。识别显示与原图定量独立；同名蛋白不猜配，空位和真实0保留。改名撤回确认，来源或几何变化使关联过期；重开须再次核对已提交OCR资产和运行，坏OCR不会伪造数值。成功重新识别重建未确认行；失败或取消保留旧关联。每项目当前一张TIFF拼图、最多512行；PNG/JPEG OCR、统一归档和产品验收仍待实施。契约见wb-project-ocr-v1.md。

0.13.0新增WBNormalizedProject/schema v5，继续读取v1–v4，允许无OCR配置归一化。显式选择目标/内参或磷酸化/总蛋白、逐泳道样本映射、包含与对照；初始无样本名、参照泳道或确认。lane_reference_ratio@1分开保存原始积分展示、比值、对照均值和相对值，派生值从核验run重算，不写回原始结果。零/缺失/异常分母和无效对照给空值及原因，不加epsilon或跳过坏对照。Qt复核、OCR标签视图、重开与带来源XLSX共用同一计算；改映射撤回确认，源/ROI/N变化使关系过期。契约见wb-project-normalization-v1.md。用户实验偏好和真实对应未替用户选择；独审与完整产品验收待办。

0.14.0增加PNG专用OCR输入（含透明白底和16位灰度），TIFF旧预处理身份保持；PNG不进入原图定量。项目“生成并识别当前拼图”保存精确修订后在后台生成完整PNG/嵌入来源，通过不可变资产导入进入既有真实OCR/人工校正/明确绑定流程，保留定量/归一化。单图独立拼图入口也支持PNG。成图/导入取消或晚到结果不替换当前源；自动刷新合并调度，不覆盖操作错误。预算和预处理详见wb-png-ocr-v1.md；JPEG/16位彩色PNG、统一归档及完整产品验收仍待办。

0.15.0增加read_metadata_file/preview_metadata/filename_metadata/apply_metadata：有界只读XLSX/UTF-8 CSV、表头/字段选择、严格row_id/SHA/文件名匹配、重复/未匹配提示、可修正预览、所选行/字段原子应用、共同参数及字面文件名分段。公式缓存不导入，空白不覆盖，几何/N/空位有效性沿用原契约；v1–v5字段不变，已有run/OCR/归一化保持。原图列表增加128边后台缩略图及SHA缓存；重开可按需加载。详见wb-project-metadata-v1.md。真实匹配、独审与完整产品验收仍待办。

0.16.0为原图/OCR/归一化导出增加CSV，和XLSX共用表格数据；文字以可逆text:前缀编码，数值/真实0/空值分开。export_figure_bundle新增可选ArchiveRunEvidence，archive.json v2索引所有成员的SHA/大小/角色，ZIP统一包含原图、原值裁剪、拼图、CSV/XLSX、原始请求/结果及当前配置。重新校验运行资产，坏结果标明不可用、其他行继续；不把缓存或外来记录当本机成功。后台有界、取消/无覆盖发布，项目v1–v5与原算法不变。详见wb-project-archive-v2.md；ZIP导入和完整产品验收待办。

0.17.0增加有界ZIP检查/stage_project_archive和schema6归档历史证据，保留原ZIP、原图、OCR关联、原始结果，严格重建表/像素检查。schema1–5兼容，来源表/界面区分归档历史与本机运行，外来RunRecord不登记本机收据。再次导出保留历史来源链，最多8代并受2GiB总预算限制。见wb-project-restore-v1.md；真实科学准确率/独审与最终产品验收仍待办。

0.18.0新增export_figure_image：直接保存完整RGB8显示TIFF/PNG，沿用原裁剪几何及既有16位整除257显示映射；嵌入相同来源JSON、DPI，原图/字体SHA与字节数核验，写入后重读核对像素和标签再无覆盖发布。已知本软件显示TIFF可走OCR，load_tiff定量入口明确拒绝；未知第三方图不按扩展名猜来源。PNG64MiB/TIFF128MiB、来源16MiB、3200万像素/32768边长预算；项目schema和数值公式保持，完整恢复仍用ZIP。见wb-direct-figure-image-v1.md。

0.19.0新增WBLayoutProject/schema7：明确原泳道横向分段、原ROI逐行高度、独立Fig字号与列排布；v1–v6仍按旧渲染，不自动升级。渲染按源逐次解码一次并释放，保留显示顺序与逐段来源。export_figure_template/read_figure_template保存和读取.wbtemplate，只含通用排版样式和字体，导入新工作区后建立新字体资产及空项目，不带原实验绑定或测量。模板I/O必须后台调用；有界解析/字体SHA核验/无覆盖发布，详见wb-laboratory-layout-v1.md、wb-figure-template-v1.md。独审与真实科学/最终产品验收按任务记录，不能由功能存在推断通过。

T-024新增 automatic_wb_proposals@1 与 WBAutomaticProject/schema8：原像素泳道/裁剪及积分边界建议、可保留图上调整的后台入口、机器来源证据与过期校验；人工审核标记保持false。旧schema1–7读取不变，积分profile_integral@1不变。策略、限制、验证见work/evidence/T-027/automatic-core-validation.md（仓库根）。

T-024自动主流程已集成。schema8与自动输出契约见 `../../docs/contracts/wb-automatic-v1.md`；质量复核的原始积分与有效信号分列；失败来源保留，未知蛋白和归一化配对不猜测。

T-041：FigureLayoutStyle显式standard_lane_ratio@1可将同Fig不同原生ROI尺寸显示为每泳道lane_unit宽、4/5 lane_unit高的RGB8 LANCZOS行；原生默认、定量和原值裁剪保持。manifest操作@2明确回源与显示重采样，TIFF定量入口拒绝；预算仍3200万像素。详见wb-laboratory-layout-v1.md。

T-042：source_geometry@2以短膜轮廓、上下边方向和跨阈值泳道中心推断几何；多行Marker证据仅排除实际Marker。检测/显示拉正保留原像素逐泳道ROI。手动ROI/N变化撤销该行旧显示框，旧项目与旧策略仍可重放。background_support@1要求连续背景支持，原始profile_integral@1公式不变；背景不足/多信号需复核，不能作为有效信号。现网页工作台默认启用两项新策略，HTML/CSS布局未改。研究与8图限定评分见docs/research/2026-10-17-source-only-geometry.md、work/evidence/T-042/crop-scoring.md（仓库根）。

T-044当前阶段：folder_sources@1目录头信息筛选已知派生图和明确采集编号变体；literal_source_labels@1按明确Fig路径/采集文件名保留字面分组与条带标签，不推断配对。后台自动选择支持标签的已安装字体后导入项目资产。旧项目/原值/积分策略保持，完整状态和未完功能见work/tasks/T-044-wb-workflow-and-integrals.md。

T-044新增当前网页工作台默认anchored_context@1/anchored_background@1，固定原目标、逐步扩展最多25%背景上下文；保存目标/采样原坐标与比例，手动几何编辑清除旧边界并从目标重新规划。旧策略和已有请求不会静默升级，旧序列化字节保持，三份机器schema增加显式版本化扩展。原始profile_integral@1/位深风险保持，背景不足不强判有效。详见wb-anchored-context-v1.md与T044实际验证。

E4/T057新增schema13完整Fig依据、稳定行/槽位与冻结原图请求映射，
`prepare_intake_figure`生成并核验显示PNG，`complete_intake_figure`原子完成成图及计划；
`complete_intake_measurement`只接受同冻结请求/真实运行/已验证结果。缩放预览另存
显示变换，原PNG/原ROI不变。手动分段保留且不改变定量输入。桌面接通真实worker；
最终全门禁状态见T057，不由API存在推出科学/发布完成。契约见wb-intake-figure-v1.md。

审核后原位置回存契约见 `../../docs/contracts/wb-crop-return-v1.md`。
`return_reviewed_crop` 复用显示分段映射和原值裁剪，写后核验且不替换旧文件；
多文件部分失败明确列出已发布文件，无完成记录，不改变定量公式或项目格式。

E5/T058新增schema14和intake_output@1：`fill_intake_table`按Fig/蛋白行/固定槽位填表，
CSV/XLSX来源审计记录稳定身份；新目录发布原值/显示裁剪、Fig、索引和恢复ZIP。
资产及run请求/结果有界冻结并再次核验，索引导入与CAS成功后才完成输出阶段；
取消、部分失败、未知活动阶段恢复保持真实状态，不注册外来PID为本机成功。
旧schema1–13保持。契约见wb-intake-output-v1.md，完成证据以T058任务为准。


T067新增明确执行后分组编辑与intake_workflow@2，未选源/未定N草稿可保存重开；换源/N/移组失效受影响证据，标签重建显示时可复用完全一致数值输入的真实运行。历史修订与原图不改。见 ../../docs/contracts/wb-intake-group-revision-v1.md。
