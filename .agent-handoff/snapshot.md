# Handoff Snapshot

- 更新：2026-10-14。用户补充 WB 资料并明确继续，暂停已解除；上位目标 T-003 完整 WB 软件。当前 T-009：OCR/工作表完整闭环自验完成，独立审查尚未执行。
- 分支 feat/T-009-fig-ocr-table，base feat/T-008-wb-desktop (34831e4)。本轮从184d018继续；最新提交以 git log 为准。main/PR/远程CI未操作。
- wb-tool0.7.0 / bioimage-app0.2.0：原TIFF手工ROI/条带/基线定量、离线OCR专用进程、Qt名称/关联复核、自动写表/新文件XLSX、v1/v2草稿保存重开。允许先OCR后ROI，支持单独拼图资产与显式跨图绑定；一次草稿仍只有一个定量原图。
- 文档v2保存OCR原文/坐标/引擎模型摘要、原图与拼图资产、已确认工作表和当前有效测量；v1保留只读兼容。更改ROI/极性清除当前值，更改名称取消确认；缺失/失败不转零。原图与历史运行不可覆盖。
- 完整检查退出0：205测试（59秒）、Ruff/Pyright strict、9导入合约、4独立wheel/5安装场景；安装产物真实OCR worker通过。原生Qt实测先识别后ROI、跨图绑定、保存重开、XLSX数值、名称修正及ROI失效。证据见work/evidence/T-009/validation.md。
- 新资料只读检查，私人提取/预览/原始OCR放.local/requirements-review（忽略目录）。真实组合图含短编号、倾斜样本名、并排同名蛋白、空位。布局@2给长图16组；另一图Fig1C高置信误读为Fig1G，必须复核，未建立准确率指标。
- 下一步 T-010：用户已知泳道数的固定网格、Marker排除与原坐标条带裁剪复核；随后Fig/蛋白模板合成，再项目批次、归一化与产品打包。详见docs/research/2026-10-14-wb-materials-workflow.md。首版OCR/自动写表要求持续有效。
- 待用户说明同曝光无后缀/_0/_1 TIFF与CLX含义及定量来源。界面可显式选源，不能根据位深/命名自动选；任务单趋势不作为算法优化目标。Excel数值单位未确认，不作为灰度真值。
- T-003至T-009产品阶段均尚无绑定提交的独立审查；T-008一次pytest原生Aborted根因未独立重放，后续全量通过不能抹去风险。T-001真实人工标注未冻结，P0包态交互/DPI和干净Windows仍待办。
- 启动：uv run --locked --no-sync python -m bioimage_app。静态--worker wb/wb_ocr；platform_runtime不含实验语义，各跨包仅用api。
- 不恢复归档项目；不提交私人资料/模型/安装包。Goal API本轮先前返回null，没有创建替代目标。
