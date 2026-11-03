# WB代码只读核对

核对日期：2026-11-02；分支`codex/p008-workflow-batch`；HEAD `5d5dd226a7dc6bf16879c16257a0d3754b814ff3`。

实际树有P008未提交开发改动。以下核心文件逐项记录内容摘要和行号；任务卡按末尾最新记录解释，旧契约标题的“开发中”不替代最新任务状态。未运行产品测试，未修改该树。

| 能力/证据 | 实际文件 | 定位 |
|---|---|---|
| 输入与位深 | [tools/wb/src/wb_tool/adapters/tiff_input.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/src/wb_tool/adapters/tiff_input.py) | 第271行 |
| 原像素均值剖面 | [tools/wb/src/wb_tool/domain/lanes.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/src/wb_tool/domain/lanes.py) | 第44行 |
| 基线积分定义 | [tools/wb/src/wb_tool/domain/quantify.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/src/wb_tool/domain/quantify.py) | 第57行 |
| 上下限质量提示 | [tools/wb/src/wb_tool/application/analysis.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/src/wb_tool/application/analysis.py) | 第198行 |
| 归一化语义 | [tools/wb/src/wb_tool/application/project_normalization.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/src/wb_tool/application/project_normalization.py) | 第25行 |
| 归一化计算 | [tools/wb/src/wb_tool/domain/normalization.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/src/wb_tool/domain/normalization.py) | 第8行 |
| 实际注册的三个节点 | [tools/wb/src/wb_tool/adapters/workflow_nodes.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/src/wb_tool/adapters/workflow_nodes.py) | 第43行 |
| 导入与分组 | [docs/contracts/wb-instrument-intake-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-instrument-intake-v1.md) | 第1行 |
| 样本元信息 | [docs/contracts/wb-project-metadata-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-project-metadata-v1.md) | 第1行 |
| 独立泳道、多峰与整段 | [docs/contracts/wb-fig-quant-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-fig-quant-v1.md) | 第1行 |
| 基线/曲线交互 | [docs/contracts/wb-standalone-quant-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-standalone-quant-v1.md) | 第1行 |
| 原值自动裁图 | [docs/contracts/wb-prominent-band-crop-v5.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-prominent-band-crop-v5.md) | 第1行 |
| 归一化边界 | [docs/contracts/wb-project-normalization-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-project-normalization-v1.md) | 第1行 |
| 出图与显示隔离 | [docs/contracts/wb-direct-figure-image-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-direct-figure-image-v1.md) | 第1行 |
| 项目交付 | [docs/contracts/wb-intake-delivery-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-intake-delivery-v1.md) | 第1行 |
| 原值工作流节点契约 | [docs/contracts/wb-original-workflow-v1.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/docs/contracts/wb-original-workflow-v1.md) | 第1行 |
| 独立模块验收 | [work/tasks/P-002-wb-headless-module.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/work/tasks/P-002-wb-headless-module.md) | 第1行 |
| 几何方法仍待实施 | [work/tasks/P-004-analysis-asset-contract.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/work/tasks/P-004-analysis-asset-contract.md) | 第1行 |
| 通用执行验收 | [work/tasks/P-005-workflow-execution-slice.md](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/work/tasks/P-005-workflow-execution-slice.md) | 第1行 |
| 积分测试存在，本轮未运行 | [tools/wb/tests/test_quantify.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/tests/test_quantify.py) | 第22行 |
| 归一化测试存在，本轮未运行 | [tools/wb/tests/test_normalization.py](C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0/tools/wb/tests/test_normalization.py) | 第9行 |

完整文件SHA及dirty快照见[JSON](code-audit.json)。

补充检索：相关WB源码、公开api、三节点注册及依赖锁中未见ImageJ/Image Lab/Prism连接器，未见独立实验统计、完整总泳道蛋白染色归一化实现。该结论限定于本次检索范围；现有项目归一化契约明确不计算显著性、不跨膜汇总。

实际开发仍有进行中的批处理改动，后续接入前需重新核对HEAD和接口。
