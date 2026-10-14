# Handoff Snapshot

- 更新2026-10-14；用户授权持续开发至WB自动化软件完成，Goal active，无token预算。阶段自验不能标整体完成。
- 活动仓库bioimage-tools-platform；当前分支feat/T-015-project-normalization，产品提交0cd390b3751c55ec22766e998bd99a0324193acb，base9dddcba。最后HEAD见git。T-014/T-015 review待独审，T-016 ready；任务文件为状态唯一来源。未推送、PR、main集成或发布。
- 用户明确CLX来自特殊设备且忽略；其他设备TIFF原图、裁剪TIF。继续支持.tif/.tiff并保留明确选源/SHA/ROI；不按扩展或_0/_1猜定量用途。CLX不再待决或阻塞。
- wb-tool0.13.0/app0.8.0：多源固定N标注/原曲线/明确边界与基线/真实进程/自动项目表/XLSX；独立TIFF拼图OCR原文/置信度/位置、可改Fig/蛋白、明确原图绑定、确认后自动值；新增明确样本/参照配对和归一化Qt完整流程。
- 项目v5 WBNormalizedProject保存参照类型、目标/参照row/SHA/ROI/N、逐槽样本/参考泳道/包含/对照/确认及备注；可不含OCR，旧v1–v4继续读，v4仍必须有OCR。project_with_ocr/analyses/suggestions保留v5字段。派生值不写入原始run或项目数值缓存，重开从校验的RunRecord/资产重算。
- lane_reference_ratio@1：q=T/R，T有限>=0、R有限>0；可选单个对照或明确所选对照q算术均值m，再f=q/m。坏对照不能静默跳过；m<=0、非有限/溢出/正数下溢均给空值与原因。合法目标0保持0，无epsilon。原始积分/q/m/f分列，带双方run/SHA/修订/lane/band和配置来源XLSX，无公式/覆盖旧文件。
- 初始无样本名、参照泳道、对照和确认；不按同名蛋白或相同N/泳道号猜配。UI改映射撤回确认；来源/ROI/N或审核改变关系stale。只有已核验测量可算；OCR标签视图仅已配置且当前确认关联行可显示。成功OCR重识别保留归一化计划、重建未确认OCR行。
- 用户归一化偏好异步询问尚无回复（目标/内参或磷酸化/总蛋白，再相对对照，或两者）。已提供显式选项，不视为选定默认，不擅自填真实实验配对/内参/对照/重复统计。科学来源与解析定义见docs/research/2026-10-14-project-normalization.md及wb-project-normalization-v1.md。
- 最终完整门禁退出0：284测试85.27秒、Ruff207文件、Pyright0、9合约、4wheel/5隔离场景。work/evidence/T-015/validation.md绑定0cd390b；锁文件仅两个本地包版本，无容差/忽略/门禁弱化。源码Qt截图.local/requirements-review/T015-normalization.png已查看。独审、真实实验/最终产品验收未完成。
- 既有数值仍每泳道一个target，初始bounds=None；裁剪不是积分边界。候选/显示/OCR不进入定量。曲线资产64MiB、结果每页200槽、每表200000单元格、OCR/归一化最多512行；大项目按需/流式与性能仍待改善。Qt旧偶发Aborted根因UNKNOWN，本轮未复现不等于修复。
- T-014真实组合TIFF探针15token/11未确认未绑定行，源SHA保持、保存重开一致；全部私有资料/模型/探针在ignored .local。真实人工真值未冻结，高置信OCR误读仍需复核；不把测试数量等同准确率。
- 下一步T-016-composed-figure-ocr：现成图PNG但OCR仅TIFF，补PNG输入与当前已审核拼图直达OCR，保留完整生成像素/来源/修订、原预处理版本兼容和人工明确绑定；禁止用缩略图定量。先核对git、读契约及任务、按scope执行dev.py context --record后修改。已只读了解ocr.py/load_tiff/figure_export/background，尚无T-016代码或回执。
- 其余首版缺项：批参数/元信息导入/缩略图、统一归档/ZIP导入/直接TIFF成图/CSV、模板精修/横向分段、真实准确率、独审/远程CI/最终Windows包/DPI/干净机/物理FAT与用户验收，见work/wb-acceptance.md。不要恢复归档工作流、不要自行启动子代理、不要再次调用被用户Esc停止的原生CUA；pytest-qt截图不等于包态交互验收。
