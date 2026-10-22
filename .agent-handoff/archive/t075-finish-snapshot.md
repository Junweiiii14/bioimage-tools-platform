# T075 收尾时的历史恢复指针（已被 T076 替代）

# 当前恢复指针

- 唯一任务 [T075](../work/tasks/T-075-ui-system.md)。用户授权完整M1–M6并默认推荐决策；此前已重设目标ACTIVE，无预算。恢复时先查真实目标及PR状态，不重新创建，不自动扩展任务。
- 仅活动树 `C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`，分支 `codex/t075-ui-system`。最新产品基线T074 `0376f23`；冻结候选 `5c56f5509e8ad9381420e26af059e9c60501ebbb`。原ResearchVault dirty树、原图/历史和旧安装目录保持。
- 草稿PR36 base `codex/t074-curves-fig-grid`（PR35），不合并或公开发布；规则回执base0376正确。
- M1–M6实施、同源HTML/四主题/本地Noto/舒展/动效、appearance@1及四高级网页工具完成。34前端source/wheel/install文件、7780载荷和26PNG逐像素相等。真实安装四工具/跨窗/输入基线3项20.75s、强制新revision IME1项3.91s、19项selfcheck11.391s均0。代码、有限视觉和本机交付独审通过。
- 候选 `.local/releases/runtime-5c56f5509e8a`，安装 `%LOCALAPPDATA%/Programs/BioImage WB 界面系统测试版 5c56f55`；桌面 `BioImage-WB-界面系统测试版-T075-5c56f55` 含安装器/34文件预览/快捷入口/录屏/说明。UI-test快捷方式和卸载注册更新到该候选，旧候选目录及其他通道保持。
- 产品目录 `apps/desktop packages tools` 从5c56f55到697c428无diff；后续仅诊断和文档，不重命名或重建冻结候选。前端自e8b034e未变。
- CI180/run39657811667：Windows1191过1败746.36s/child1（原角度4.8/真实命中复合断言无分项）；Ubuntu既有20次窗口关闭回收挂起，60s Python栈worker retire/storage emit/Qt wait，15min取消，均未到wheel，根因UNKNOWN。保留.local/t075-ci180-{windows,linux}.log与durable摘要，后继成功不销账。
- 697c428仅给原断言添加同次JS原子诊断字段及捕获正常session刷新，独审Accepted，未改expected/timeout/skip/gate/产品。Windows定向3项4.57s、WSL4项6.83s均0。
- **CI181/run39660837328已成功**：Windows job119433080046 1192项692.49s/child0；Linux119433079915 1192项480.61s/debugger0；两平台全部隔离wheel/真实OCR，desktop及rules39660837322全部success。摘要work/evidence/T-075/ci-181.json，原日志.local/t075-ci181-{windows,linux}.log。
- **最后完成闸门**：提交这轮仅文档/证据收尾，绑定该提交做有限独审，推送后等当前HEAD四必要检查成功。届时将实时结果保存.local/t075-final-ci.json及桌面验收记录，更新PR说明、桌面说明和本地bundle摘要，再完成goal。所有条件已满足后无需再次提交纯状态文案导致无穷CI循环；任务首段明确以当前HEAD成功为完成条件。若CI失败则继续定位，不完成goal。
- 需核最终报告、产品无diff和当前HEAD CI，不能沿用697c428代替后续commit的检查。最终文档独审本地报告可随桌面交付，代码独审链已入库。
- 科学留出、干净Win10、物理DPI/IME、历史Qt/D3D/native UNKNOWN继续独立保留；录屏和rAF/CDP不是物理输入延迟证明。两次有界视觉已完成，不开启新一轮装饰微调。
- 历史HTTP预览服务自动审批拒绝，未绕过；直接本地HTML可用，不改名重启服务。GCC长路径已同版短路径11602文件相等解决；旧失败包和原日志保留。
