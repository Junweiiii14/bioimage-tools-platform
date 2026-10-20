# WB算法与消费者清单

2026-10-20 · T068/P5。盘点以本轮已审T064–T067实现及原有E0–E7为准；任务状态另见work/tasks。以下是源码和契约关系，不是科学准确率或退役授权。外部消费者统一从 `wb_tool.api` 进入。

| 链路与入口（WB包内相对路径） | 实际消费者、I/O与原值边界 | 版本/失败与验证 |
|---|---|---|
| `application/intake_grouping.py:acquisition_key` | 清单草稿分组和`adapters/export_discovery.py`共同使用；输入安全相对路径，保留目录/采集标识，输出分组键，无图像I/O | 清单v3；名称不代表实验配对。`test_intake_grouping`/`test_export_discovery`及同名目录宿主测试 |
| `adapters/export_discovery.py:discover_exports` → `domain/export_detection.py` | WBBackground识别任务；核对SHA/尺寸/位深后从原TIFF提出角色、区域、N候选，完整三联才比较白光/合并纹理；不自动确认选源 | `export_signal_regions@1`；失败保留unknown/error，N是候选。`test_export_discovery`与真实95文件开发回归 |
| `domain/automatic.py:detect_automatic_geometry` → `domain/source_geometry.py` | 原图几何检测及独立手工/自动入口；数值定位副本，输出原坐标膜/Marker/行候选；不将显示旋转数组当定量输入 | `source_geometry@2`、旧`legacy_fixed_height@1`/`lane_ratio@1`显式分派；缺定位/弱信号需要复核。source_geometry、automatic相关测试 |
| `domain/grid.py:fixed_lane_grid` / `application/intake_crop.py` | 原值裁剪、完整Fig与人工网格共用；输入明确半开原图ROI和N，输出完整1..N槽位。N含空槽、不含Marker | `intake_crop@1`，未定位保留槽位但没有伪坐标/零值；`test_grid`/`test_intake_crop`/原值8/16/RGB测试 |
| `application/automatic.py:suggest_analysis_for_crop` / `domain/anchored_context.py` | Fig准备与独立灰度构建版本化请求；原目标/采样矩形、极性、空槽和边界进入请求，显示变换不进入 | `anchored_context@1`、`anchored_background@1`；背景不足/多信号保留复核。anchored_context、automatic与intake_figure数值预期 |
| `domain/lanes.py:compute_lane_profiles` → `domain/quantify.py:integrate_profile` | `application/analysis.py`及真实worker；二维uint8/uint16按横向float64均值形成剖面，闭区间积分，不乘泳道宽 | `profile_integral@1`、intensity*pixel；非法输入报错，真实平坦区可为0，缺失不能变0。lanes/quantify/analysis及三角形400/800解析预期 |
| `domain/{background_bounds,peak_envelope,wbquant143}` | 请求中quant_policy的明确分支；旧项目和独立入口仍可使用，不能只按当前UI默认值判死代码 | `legacy_bounds@1`、`wbquant_1_4_3@1`、`peak_envelope@1`、`background_support@1`。原第三方来源/许可证保留；策略测试和旧请求读取 |
| `adapters/figure_export.py` / `laboratory_figure.py` / `intake_figure.py` | 完整Fig投影与独立拼图/模板；源逐次解码，显示RGB8及来源清单；完整原值TIFF另存，定量仍回原图 | `bt601_uint16_div257@1`、`native_samples@1`/`standard_lane_ratio@1`；预算、标签放不下、坏来源明确失败。figure_image/laboratory_layout/intake_figure测试 |
| `application/intake_workflow.py` / `intake_revision.py` | 宿主CAS、IntakeWorkflowSession、后台任务与真实RunSession；稳定身份、冻结票据、取消/恢复，只有完整提交才done | `intake_workflow@1/@2`；editing禁止运行，旧回复拒收；标签/排序只在完整数值请求全等时复用成功RunRecord。workflow/group_revision/desktop测试与绑定独审 |
| `application/intake_output.py:fill_intake_table` / `worksheet.py` / `project_ocr.py` | 按Fig/行/槽位或明确OCR绑定写表；同名蛋白不猜配，原值积分/有效值/失败分列；CSV/XLSX/恢复索引新目录发布 | `intake_output@1`、原worksheet/project schema；未完成/失败不给有效零值，公式字面化。intake_output/worksheet/project_ocr/export测试 |
| `domain/normalization.py` / `application/project_normalization.py` | 显式目标/内参、样本映射和对照；从已核验原积分派生，不改原运行 | `lane_reference_ratio@1`；零/缺失分母为空且有原因，不加epsilon。normalization/project_normalization测试 |
| `adapters/ocr.py:recognize_figure` / `ocr_input.py` | 独立灰度OCR、项目OCR及worker；本机核验模型后CPU识别，token原坐标/原文待人工绑定，PNG专用入口不当定量原图 | 固定RapidOCR3.9.2/PP-OCRv6/ORT1.31.0，TIFF/PNG各自预处理ID；无模型/坏图/取消明确失败。OCR/PNG/隔离wheel真实worker |
| `adapters/tiff_input.py:load_tiff` / `application/desktop_data.py` /宿主预览 | 共用解码、128缩略图和2048大预览；原样本不可写、SHA/尺寸/位深核对；RGB按既有BT.601数值入口，显示数组隔离 | 拒绝不支持的多页/方向/透明与本软件显示TIFF定量；源/会话/generation保护。tiff_input/preview/intake_desktop tests |
| `adapters/intake_output.py` / `project_archive.py` / `archive_restore.py` | 同次冻结渲染复用于PNG/TIFF/ZIP，历史原值/运行/表格和恢复链；不跨操作缓存未经再核验原值 | 新目录无覆盖、部分失败真实报告；外来运行不冒充本机成功。archive/restore/intake_output及实际安装诊断 |

## 精简决定

- **已合并复用**：T064将清单分组和导出识别的同一采集键规则集中至`acquisition_key`，两个实际消费者共享，保留不同目录/曝光身份。未另建平台实验抽象。
- **保留**：独立灰度、OCR、模板、手工分组、旧请求各版本策略都有公开或兼容消费关系。`wbquant143`保留来源和许可证，不能据默认入口变化删除。
- **保留现有优化**：E6同次冻结渲染复用、逐源解码释放和有界预览继续使用。不加跨项目大图缓存；识别二次读取白光/信号是明确的内存/再校验取舍，当前没有需要改变的量化性能证据。95图识别5.0853秒只是已见数据的算法回归，不是整链耗时。
- **没有安全退役候选**：本轮只读扫描非UI/非vendor顶层私有函数，未发现只有定义的名称；也未发现跨文件至少4行完全同AST函数体。此扫描不是传递依赖/运行时可达性证明，名称碰撞可隐藏未用代码，公共/动态/兼容消费者仍须逐项审查。没有据此删公共接口、改策略默认或降低门禁。
- **待独立科学证据**：检测准确率、弱带/拖尾/双峰N、倾斜范围和背景策略优劣仍需独立留出和标注；本次不为“精简”改变数值算法，不混入模型训练或新框架。

可复验只读脚本：`uv run --locked --no-sync python work/evidence/T-068/inventory_scan.py`。输出、提交和限制记录在同目录validation；P7整链及最终完整门禁另计。若未来证明有重复/无消费者，先独立纯重构提交并做同输入前后对照，再考虑数值变更。
