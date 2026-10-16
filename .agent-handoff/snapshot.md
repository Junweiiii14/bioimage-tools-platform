# Handoff Snapshot

- 更新2026-10-17；当前T-037灰度定量监督，唯一状态work/tasks/T-037-quant-supervision.md。总体WB T003未全部完成。
- 活动树C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform；codex/t037-quant-supervision；产品9be19b1。旧主目录dirty与.impeccable/questions保留。
- 用户最终流程：裁原图条带→按Fig拼标注图→Fig组灰度→结果；自动完成落点拼图。整组泳道框由manifest映射原ROI，每泳道按蛋白分段显示曲线，图框/文字/间隔不参与积分。
- WBQuant1.4.3 MIT冻结纯数值核心、独立泳道、封底/边界编辑自动重算、原图灰度表已接同源桌面，不旧quant窗口，无逐张确认。质量警告与原始Signal并存。
- 指定两原图3/5泳道分别独立Fig；同ROI8个Signal与旧包差分<1e-10。两源Qt实测exit0，合成2蛋白×3泳道Fig的6框/6值与分段曲线验证exit0，失败历史保留。
- 全check第二轮592passed1failed（append新图缺composition段），fb6e461修复且独立失败用例exit0。最终check594passed及隔离wheel exit0，日志.local/t037/check-final.log。详细失败/验收见work/evidence/T-037/validation.md。
- 当前T037本地验收完成：最终视觉ship、独审绑定9be19b1；追加重开队列修复专项通过。当前桌面已打开双源项目（opened.json），保留测试封底调整值。下一步用户体验反馈；不自动扩展OCR/模板或其它工具。
- .local/t037含验证JSON、截图、工作区、打开灰度定量工作台.cmd；启动器读verification.json，只有最新成功harness才更新该文件。OCR/模板/归一化仍原生高级入口，干净Windows与PR/main未做。
