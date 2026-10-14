# Handoff Snapshot

- 更新：2026-10-14。用户提供WB资料后明确继续，原暂停已解除。Goal当前active，目标完整WB软件；未设置token预算。不能在局部功能完成时标goal complete。
- 当前分支fix/T-011-qt-lifecycle，base12cac86；T-011诊断子阶段自验完成，根因仍implementing。T-012-figure-project.md已ready，下一轮进入多原图行计划与Fig模板。最新head查git log；没有推送/PR/main集成。
- wb-tool0.8.0/bioimage-app0.3.1：已实现原TIFF定量/手工ROI/条带/基线、真实离线OCR、Qt名称/绑定复核与自动表/XLSX、单独拼图资产、OCR-first/v1-v2保存重开，以及固定泳道网格/人工左右Marker排除/后台原像素单框裁剪。
- T-010最终自验：215测试（60.92秒）、9导入合约、4wheel/5安装场景，Ruff/Pyright全部通过。裁剪uint8/16/RGB/RGBA/MINISWHITE/planar/大端、原值/坐标/无覆盖/错误源，Qt拖框保存重开和安装产物API均通过。详细work/evidence/T-010/validation.md。
- 一次T-010组合测试在新用例漏load_document超时之后、旧GUI用例中原生Aborted，栈顶WBBackground._reply。测试已修正、9桌面/215全量随后通过，但原生根因未明；T-008旧同类风险仍保留。T-011四轮36桌面探针未复现；已增加正式桌面入口本地Qt/Python日志和致命错误线程栈，三个真实子进程验证落盘。最新218全量/9合约/4wheel5场景通过，但不是根因修复。停止无新假设压力重跑，继续T-012；下次复现先读日志。
- 完整首版需求/证据矩阵：work/wb-acceptance.md，来源为用户方案第7–11节和明确首版OCR要求；完成前逐项审查，不按已实现功能缩小目标。
- 后续产品功能：自动膜/Marker候选、整行裁剪组织与Fig/蛋白模板合成、多原图项目批次、归一化、产品打包验收。当前一次草稿仅一个定量原图，跨图为一个原图对一个拼图；原像素导出只导出选中单框，整行可在单框模式框选。固定网格参数不存历史，保存明确坐标不按默认值重建。
- 新资料只读检查；私人提取/预览/OCR位于.local/requirements-review。长组合图布局@2给16组；另一图Fig1C高置信误读为Fig1G，必须人工确认。用户首版必须OCR/Fig/自动写表要求保留；真实人工真值/准确率验收尚未建立。
- 待用户回答无后缀/_0/_1 TIFF与CLX分别是什么导出、哪种用于定量。当前显式选源，不按位深或命名猜测；任务单趋势不用于调整检测/测量，Excel单位未明不当灰度真值。
- 所有产品阶段绑定提交独审尚未执行。T-001人工标注、P0包态交互/DPI/干净Windows、物理FAT未验收。最终产品仍未完成。
- 启动uv run --locked --no-sync python -m bioimage_app；各跨包只用api，平台不含实验语义。原图/历史结果不可覆盖，不恢复归档项目，不提交私人资料/模型/安装包。
