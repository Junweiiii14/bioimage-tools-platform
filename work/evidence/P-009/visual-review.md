# P009 独立视觉审查及一次确认

审查者为fresh context的`/root/impeccable_finish_reviewer`，按已安装impeccable明确要求启动。非作者只读，未修改共享文件、未运行第二次detector。范围是既有Operate工作台的编排扩展，不是整卡代码独审或科学验收。

## 首轮：disposition: fix

准确首轮源码bb42d6b9116ecf05085bc5a0e076d334d02f3f28。审查者先打开全部12张有效详细图，确认四主题、已有字体/材质、主操作、目录/画布/检查器、真实结果/来源符合既有体系。模板新世界、comp和新资产要求不适用于本次保留既有体系的扩展。

唯一material fix：窄窗任务密度。四张960×640参数图首屏没有可编辑科学参数，640×720画布初始只有节点标题、没有可用端口。顶部路径/标题/工具栏/状态/页签和次要版本/替换信息占用过多任务区域。要求保留40px控件、身份、保存运行和真实状态，同时局部滚动。

backdrop色值advisory不构成截图中的实质问题，不需扩大为全局主题修复。

## 一批修正

短/窄窗口压缩持久顶部和页脚，完整路径保留在tooltip；版本/替换/技术来源和方法参数移到任务之后的高级折叠区；优先暴露实际极性/布局/预期行数，窄窗仍有当前步骤切换；图视图减少初始垂直空白。全部编排按钮/输入/select保持至少40px。计算布局值/数值方法、结果、运行器不变。

真实GUI五流程及原生图探针最新6passed41.34秒，退出0；pyright与web静态检查退出0。确认采集仍用相同12视图和有效性守卫，`.local/p009-ui-confirm-active-capture.log`退出0/15.57秒。没有为确认放宽纯色/实际颜色匹配守卫，也没有重新运行detector。

## 确认原文

> Resolved — viewport usability/task density. Reopened all 12 required captures; all are valid. Every `*-960x640-parameters.png` now exposes the editable signal-polarity control immediately. `forest-640x720-graph.png` shows a complete preflight node with readable input/output port buttons. Workflow title, save/run, status, saved revision and local scrollbars remain visible. Four-theme identity is preserved. No material regression from this fix batch identified.

> Clear for the scored fix. This ship verdict covers that fix only, not the whole surface or performance, scientific, physical IME or target-device acceptance.

**disposition: ship**，精确范围为上述唯一修正已解决。不能将其改写成全产品“无问题”或性能通过。最终确认截图位于`.local/p009-ui-confirm-windows-active/`，同路径副本`.impeccable/review/`；源码/日志/图像摘要随visual-confirmation.json记录。首轮及所有无效采集保留，不覆盖原失败历史。普通扩展的设计一致性文档检查随后由独立documenter记录；最终代码独审/性能/wheel/PRCI仍待做。
