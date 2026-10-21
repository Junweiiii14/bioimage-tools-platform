# 当前恢复指针

- 唯一任务 [T075](../work/tasks/T-075-ui-system.md)，目标 ACTIVE；普通判断自主，持续M1–M6。用户清除旧目标后已重新创建，无预算；不要重建或提前完成。
- 仅活动树 `C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`，分支 `codex/t075-ui-system`。基线T074 `0376f23`，候选冻结 `5c56f5509e8ad9381420e26af059e9c60501ebbb`；目前仅诊断测试/工具/文档改动，产品未变。原ResearchVault dirty树与旧数据/安装保持。
- 草稿PR36 base codex/t074-curves-fig-grid（PR35）；规则回执base0376正确。不得合并/公开发布。
- M1–M5实施完成。四主题/本地Noto/舒展/可中断动效/同源HTML/appearance@1及四高级网页工具真实接入。已验候选在 `.local/releases/runtime-5c56f5509e8a`，安装 `%LOCALAPPDATA%/Programs/BioImage WB 界面系统测试版 5c56f55`。
- 桌面新目录 `BioImage-WB-界面系统测试版-T075-5c56f55` 含安装器、34文件预览、url入口、录屏、使用说明。UI-test快捷方式/注册指向新候选；旧候选目录和其他通道快捷方式保留，不能声称旧同通道所有注册不变。
- 本机26PNG逐像素、records相等；34源/wheel/install前端SHA相等；7780载荷相等。来源固定fixture `.local/t075-final-source-stable`、安装 `.local/t075-final-installed`，nativeQt6.12/Chromium140/GPU未禁/DPR1.5；高缩放DPR2.25。捕获工具新增正常session refresh冻结保存标签，非图片后处理。
- 安装privatePython高级/跨窗/IME基线3passed20.75s，146产品/Qt磁盘模块安装来源；selfcheck19项0。独审指出原IME publish可能去重，补stateChanged及JS revision到达断言，另1passed3.91s。全部证据入work/evidence/T075，原报告/截图/视频在.local。
- 代码独审链5c56Accepted、视觉edafe限定ship、本机交付独审Accepted见 `work/evidence/T-075/t075-delivery-review-5c56f55.md`；科学/物理DPI/干净Win10/native UNKNOWN保留。
- **当前必要工作：CI180失败，不能完成目标。** run39657811667 Windows1failed1191passed746.36s，既有test_rotation_preview_and_one_real_click_commit[False]的输入4.8/真实命中复合断言失败；原日志无分项。Ubuntu在既有test_repeated_window_close_and_collection等待resources_closed挂起，60s Python栈worker retire/storage emit/Qt waitUntil，15min取消，缺原生锁证据。均未进wheel。规则142、desktop success。原日志.local/t075-ci180-{windows,linux}.log，摘要work/evidence/T075/ci-180.json。
- 已保持原断言与真实QTest点击，改为单次JS JSON记录value/hit/focus/fonts/viewport/animations，便于下次定位；无等待/预期/timeout/skip/gate变化。相关3项本机4.57s通过，不称远端已修复。即将提交并推送诊断和证据，等新CI，必要时精确修复并绑定独审。
- 如新CI通过，更新最终CI证据/任务/设计/交接/桌面说明，确认产品字节仍等冻结候选；无需仅因文档改动重建。若产品改变则须新独审/安装及受影响还原。
- 历史：edafe构建GCC长路径问题已同版11602文件SHA复制短路径解决；旧候选高级open revision/busy时序已修5c56且安装验证，失败留档。HTTP预览server自动审批拒绝过，未绕过；使用直接local文件。不得把此阻断的服务改名重试。
