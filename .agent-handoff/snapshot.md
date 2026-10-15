# Handoff Snapshot

- 更新2026-10-15。当前总体T-003；当前前端任务T-023 A证据工作台实现，状态唯一来源work/tasks/T-023-ui-design-candidates.md；T-022上一版保留。
- 最新产品在C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform，当前分支codex/t023-ui-candidates（从T-022分出）。产品0d9aad94c8bd7a93f34a24163af4fabe8d017d56；文档HEAD2442d408，另有未提交F-007记录。原主目录feat/T-021-laboratory-figure-layout的旧dirty内容保留，不覆盖。
- T-022用Impeccable与Taste（product-performs/seed278796543）重写四步界面。用户最终明确：只要风格和布局大致类似旧WBQuant，不保留旧复制泳道/自动检峰/拖基线/下一组；继续Qt及现有科学规则。源图左参数右画布、定量表/曲线并排、拼图完整fit预览、OCR归定量辅助。
- 最终32a2d18全门禁500/173.83s、Ruff289/Pyright0/9合约/4wheel通过；独立绑定审查17/9.02s无可操作发现，三张新截图ship。详情T-022/validation.md。
- 新演示.local/deliveries/WB-workflow-20261015，真实Qt截图与启动脚本、合成工作区及使用说明。F-006旧7页Word/PDF及演示仍保留在.local/deliveries/WB-preview-20261015-2。
- T-021已完成三项本地实现与独审，1e6cd5a全门禁490；模板/逐源一次解码/schema兼容证据见T-021。未推送、远程CI、PR集成或发布。
- 用户要求完全重新设计，先提供候选再开始实现。T-023用户选择A；正式Qt实现产品0d9aad94c8bd7a93f34a24163af4fabe8d017d56，本地独审15项通过、视觉两修复resolved；最终505/173.57s全门禁通过；一轮停滞未定位仍保留风险。选择页http://127.0.0.1:63028/，question key 0ea9eab8；交付.local/deliveries/WB-UI-candidates-20261015。DESIGN/sidecar已更新为A实际系统；演示.local/deliveries/WB-evidence-20261015，窗口PID34964（以进程为准），使用说明与报告在同目录。
- Qt旧中止/停滞根因UNKNOWN，真实检测/OCR准确率及样本配对未验收；干净Windows依用户安排，Esc停止的原生CUA不重启。CLX忽略，_0/_1不猜测。风险见risks.md。

- F-007操作教学已被用户停止，未完成裁剪/导出。当前要求是说明开发进度及纠偏规划。用户重申统一工具平台、WB首个自动化工具、未来工具共享操作逻辑；不接受默认手填精准坐标。旧版操作可不保留不等于放弃自动化。核对报告与分阶段验收见work/evidence/F-007/progress-and-realignment.md；下一产品重点平台入口、自动候选与图上复核、自动定量建议和完整流程，不能继续仅改视觉或教授手填参数。本轮未实施新产品功能/未重跑产品测试。
- T-024自动核心子树t024-auto-core本地实现待集成；任务work/tasks/T-027-automatic-wb-core.md，schema8机器建议不伪造人工审核；40定向通过/Pyright0/Ruff通过，真实10图5建议+5无候选，无准确率声明。

- T-027后续原始积分证据列独立于有效信号/状态；schema8审计导出扩展、旧表布局保持。58定向测试通过/Pyright0，待根分支集成。
