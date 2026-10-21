# 当前恢复指针

- 唯一任务：[T075](../work/tasks/T-075-ui-system.md)，完整 M1–M6，Codex 目标 ACTIVE；普通判断自主，不中断。禁止标完成直到安装/CI收尾。
- 仅活动树 `C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`，分支 `codex/t075-ui-system`。最新产品基线 T074 `0376f23`；产品 HEAD `5c60e82d014af96476879bff6e248190096b406c`，即将推送/构建。原 ResearchVault dirty 树、旧安装/原图/历史保持。
- PR36（草稿）base `codex/t074-curves-fig-grid`（PR35）。规则回执base0376正确。不得合并/公开发布。
- M1–M5已落地：4主题、本地Noto、密度/可中断动效、共享HTML、appearance@1与高级4工具真实保存/导出/重开。最终验收仍看任务。
- 代码独审链：fa746fa发现OCR回执/阶段守卫/跨窗口轮询；1d872bf已修，edafe65裁剪标签显示delta独审Accepted；e8b034e补只读open在保存回执早于主快照时读取当前revision，写入严格generation，加载失败显示重试，独审Accepted。报告 `.local/t075-code-review-{1d872bf,edafe65,e8b034e}.md`。
- 视觉独审：四项修正及小窗口裁剪标注直接回归已ship；`.local/t075-finish-review-edafe65.md`。无后续装饰性猎错。
- 构建edafe首次长路径GCC缺头文件失败，保留 `.local/releases/failed-runtime-edafe65e1451-compiler`。完整工具链复制到 `.local/t075-toolchain/mingw64`，11602文件SHA相等，短路径编译通过；未升级/修改工具链。
- edafe旧候选安装0，7780载荷全匹配、supervision安装19检查通过。但安装高级工具保存后切页时序失败，已由e8修，旧候选不能交付。
- e8新构建成功：`.local/releases/runtime-e8b034e970f6`，新安装目录 `%LOCALAPPDATA%/Programs/BioImage WB 界面系统测试版 e8b034e`（保留旧edafe目录）。安装及验收进行中。
- 下一步：完成 e8 安装自检/实际安装高级工具（helper `.local/t075-installed-acceptance.py` 借用pytest但所有产品/Qt/worker强制安装目录），源码/安装renderer截图录屏、34前端文件和全载荷SHA；CI179 run39656871123当前进行中，规则141通过。然后设计/任务/证据/交接最终文档、候选交付独审、文档提交及必要CI。
- 捕获：`tooling/capture_workbench.py` CDP图像，不用滞后的QWidget.grab；正式Windows Qt6.12/Chromium140/DPR1.5。`.local/t075-e8-source`26图/录屏，有两图保存标签因正常500ms刷新时序不同；`.local/t075-capture-acceptance.py`通过正常preview session refresh冻结静态状态，目标`.local/t075-final-source-stable`与对应installed目录。不篡改图片或字体。实际指针运动见pointer-actions.json。
- 验证：e8两高级测试7.74s、单流程3次7.13/7.09/6.91s、独审2项8.66s；测试停主快照定时器确定性验证新读取与旧写入拒绝。曾一轮模拟并发冲突后template打开5s超时未留失败上下文，补诊断后未复现，原因UNKNOWN保留。
- 安装harness首次2passed后来源审计误把Qt嵌入的相对shiboken模块当磁盘文件，exit1；仅诊断分类纠正，产品4包和Qt磁盘模块仍严格安装路径。后续edafe链路OCR打开失败不是此诊断假阳性，已修e8。
- 原GPU/D3D及Qt mailbox日志、干净Win10/物理DPI/独立科学留出限制保留，不能以成功回归销账；自动审批拒绝过HTTP预览server，未绕过，直接file预览可用。

- 更新：e8安装高级测试精确定位此前冲突后open超时为后台来源读取busy；5c60e82允许只读open在busy查看当前快照，关闭仍拒绝，写入busy/generation保护保持。2项定向8.85s通过，新增确定性busy读/写隔离。需按新提交独审、构建/安装新独立目录；e8不作最终交付。源码稳定截图 `.local/t075-final-source-stable`26张console空，前端资源在5c60未变。
