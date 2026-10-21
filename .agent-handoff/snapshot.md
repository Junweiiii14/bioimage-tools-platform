# 当前恢复指针

- 唯一任务：[T075](../work/tasks/T-075-ui-system.md)，用户批准完整 M1–M6 UI 重构；Codex 目标已激活，未完成。常规判断自主推荐，不中断；以最新软件为准。
- 活动树 `C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`；分支 `codex/t075-ui-system`，基线 T074 `0376f23`，已核对远端最新产品。原 ResearchVault dirty、其他树、旧安装保留。
- M1 已完成；M2–M5 实施中：四主题/本地 Noto/密度/可中断动效、同源演示适配、外观 QSettings、高级网页工具与最新 Intake 修订用例已落地。M6 未完成。
- 下一步：最终提交独审、必需CI及新独立安装候选资源核验；补安装目录同源截图和交付说明。
- 关键文件：web_ui/{design_tokens,components,advanced,appearance,motion,interactions,preview_adapter}；desktop/{appearance,web_advanced,web_window,figure_window}；wb/application/workbench_revision；tooling/capture_workbench。
- 当前检查：6项新核心修订测试通过；6项受影响网页回归通过；真实网页模板/元信息/OCR/归一化保存、导出与重开整链测试通过，加入并发字段冲突确认后亦通过。具体环境/原失败见任务与验证记录。
- 捕获：Qt6.12 / Chromium140；QWidget.grab 会滞后一帧，禁止用其作验收；已改为本机 CDP Page.captureScreenshot，.local/t075-visual-valid 为首轮有效批量截图。theme* 首轮调用仅 apply 被会话覆盖；t075-visual-confirm 已用真实按钮完成26图、平台字体和69帧录屏。原生Windows DPR2.25短场景110帧中位16.7ms，非物理DPI验收。
- 原 appearance+intake_web_ui 联跑 D3D access violation 仍保留，未据软件渲染通过宣称硬件稳定；正式渲染设置未禁GPU。未构建/安装/CI/最终独审，不标交付完成。
- 历史科学/干净Win10/物理DPI及 native UNKNOWN 仍见 risks；T074安装证据不迁移为T075证据。
