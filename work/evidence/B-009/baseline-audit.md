# 2026-11-02 实际产品树只读审计

核验者：audit_actual非作者子代理；主作者据此修订方案。没有修改产品文件或运行测试。

- root：C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0
- branch：codex/p002-wb-headless-module
- HEAD：78403be43b225da3626e3a6ef0a8aeda2cbbbaec
- dirty：仅未跟踪work/evidence/P-002/frozen-runs/
- P-001任务done；卡记录PR47合入29930f62a0b158189b76e0fad7d090d632f149d6，未在本轮另查远端。
- P-002任务in_progress；任务head/snapshot仍725fc6a，落后于实HEAD。不自行标完成。
- `.local/p002-check-all-a.txt`尾部停在pytest 23%，无完整成功/退出码；不能视为通过。

路径均相对上述产品root，行号仅绑定所读HEAD。

| 能力 | 源码证据 | 限制 |
|---|---|---|
| 物理资产与Workspace | tool_contracts/api.py:57 AssetRef；platform_runtime/workspace.py:125 Workspace | 文件发布与数据库不是单事务 |
| 模块信封 | packages/tool_contracts/src/tool_contracts/api.py:205 ModuleSpec、:241 ExecutionRequest、:273 OutputManifest、:313 ExecutionEvent | 最小v1，非完整科学端口/图执行 |
| 角色绑定 | 同文件:149 AssetKind、:230 BoundAsset | raw_image/display_image/typed_table/run_manifest/analysis_result；无完整单位/坐标/样本语义 |
| 成熟WB粗模块 | tools/wb/src/wb_tool/application/module_execution.py:59 execute_legacy_module；adapters/module_execution.py:53 wb_module_spec、:86 prepare_wb_execution、:111 execute_wb_module | wb-legacy-analysis@1.0调用旧analyze_annotations，不是新校正算法 |
| 成果提交 | apps/desktop/src/bioimage_app/module_results.py:29 commit_module_result；run_session.py:171；docs/contracts/wb-module-v0.md | 实际退出与核验后提交，不等于整阶段验收完成 |
| CLI/GUI | module_session.py:32 ComparisonSession、module_cli.py:12 run_comparison_cli、web_ui/module_compare.js；docs/wb-v0-acceptance.md | --v0-compare/--v0-open共用会话，最终验收未闭合 |
| 旧批次 | apps/desktop/src/bioimage_app/intake_workflow.py；tools/wb/src/wb_tool/application/intake_workflow.py | WB专用全批裁剪屏障，不是通用DAG |

当前ModuleSpec端口为窄类型+文件名，最多8输入/16输出；ExecutionEvent仅hello/accepted/result/failure/cancelled，sequence 0–2。版本化扩展而非静默放宽。

检索未发现ScientificAsset、WorkflowSpec、通用workflow_engine、可视节点画布、受控扩展SDK或IF/IHC产品包；desktop_sdk/imaging_core/imaging_ui仍规划。现有阶段授权文档只到V0，本轮新路线不得直接扩大P-002任务。
