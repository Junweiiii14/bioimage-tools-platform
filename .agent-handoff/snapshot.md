# Handoff Snapshot

- 更新2026-10-15。总体T-003；当前T-024工具平台与WB自动化主流程，唯一状态 `work/tasks/T-024-platform-automation.md`。已完成本地闭环/真实输出/独审，待用户实际试用及PR集成，不代表最终科学验收。
- 活动工作树 `C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform`，分支 `codex/t024-platform-automation`，产品 `16f38777d8bf8262b429e4004413937dd55b0195`。原仓库旧T-021 dirty保留；不要覆盖。当前预存未跟踪 `.impeccable/questions/` 保留。
- 默认入口是真实工具平台，WB工具目录导入→自动泳道/裁剪/积分边界→真实测量进程→表/拼图/可恢复ZIP。源图左224/中央图/右272；Qt冷白青绿；图上移动缩放，不要求坐标。schema8机器证据不伪装人工审核，原像素计算，旧1–7读取不变。
- 子任务平台T-025、画布T-026（修正重复ID）、核心T-027已集成。Impeccable用于Operate/native；Taste明确不适用app screen。独立代码审查五P2均修复且绑定16f3877通过；独立视觉两修复resolved/ship（限定所审修复）；设计documenter已核对。
- 最终 `dev.py check --all` 退出0：532 passed/193.25s，Ruff317格式/Pyright0/9合约/隔离wheel与真实OCR烟测通过。详见work/evidence/T-024/validation.md。
- 实际10张用户TIFF完整处理：5张检出21泳道、5张无可靠候选。全部21条有质量警告，原始积分已输出而有效信号留空。无人工真值准确率声明、不猜蛋白/组别/内参，不按文件后缀推断来源。
- 最新交付 `.local/deliveries/WB-platform-20261015-212916`：workspace、真实5视图截图、启动脚本、使用说明；输出 `workspace/outputs/WB-20261015-212920-84db3a`。严格ZIP恢复验证10行/schema8/5机器证据/0人工review。原图/产物不提交Git。
- 下一步依据用户实际试用处理检测失败/质量复核、明确实验标签和样本配对，再验收完整科学工作流。其他工具不自动扩展。旧坐标教学已停止。远程CI/PR合并/包态发布未做。
- 历史Qt中止/停滞根因UNKNOWN，真实准确率与干净Windows仍待验收；不得以本轮通过删除风险。旧snapshot已存archive/t024-pre-integration-snapshot.md。
