# 当前恢复入口

活动任务 [P016 单图核分割研究用户流程](../work/tasks/P-016-nuclei-single-image-flow.md)，goal已建立且active、无预算。只在 bioimage-plan-sync 工作树，分支 codex/p016-nuclei-single-image-flow；候选HEAD c08979d，PR67已创建，当前有数据库异常修复与WB测试等待条件改动待提交。原bioimage-tools-platform dirty树、旧P012 GUI、安装与原图不碰。

首条实际GUI公开样例46核/标签一致、导出/关闭/同run重开已通过；真实零核/缺模型/16bit/取消/历史保护回归通过。c08979d本地全门禁exit0、1735 passed、wheel通过（73881已终止）；PR67 Linux通过，Windows一个既有WB重开测试先读到临时空白host，增加等待原workspace条件，不改结果断言/超时。独审实证损坏SQLite导致线程失败无通知，已在IO边界补捕获，新增损坏/缺失DB真实QThread两例，控制器6 passed。独审代理随后用量限制退出，尚无完整通过结论。详见P016/review-and-validation.md。下一步新提交、准确独审/必需CI、最终截图与逐项验收；不重启已结束73881，不动旧P012窗口。

P016已读Impeccable context及当前UI契约，保持现有视觉；首屏工具入口与核图对话框复用现有组件。Computer Use @oai/sky已实际操作；原生文件对话框UIA索引缓存不可靠，截图与键盘输入成功，不当产品缺陷。新工具显示API改变包implementation fingerprint，已构建 .local/p016-wheels 并重装P015自有worker环境（P014历史环境不动）。若继续改变工具代码，实际模型前须同步wheel。

P015已完成PR66/main a761284、独审/真实模型/双平台CI/正式回传，goal已complete，不重做。当前上游01a19bfd-f3ab-7502-86da-9f61953d1c8a(local)已获用户自动接续要求（成功发送）：执行/验收后回传→上游继续派发，不等待催促。P016未完成前不宣称验收或派发新任务。科学/训练重叠/患者独立性/学生/16bit/Linux真实模型与旧GPU/目标机缺项保持。
