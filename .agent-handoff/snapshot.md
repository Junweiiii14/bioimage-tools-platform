# 当前恢复入口

2026-11-04，当前任务[ P011 WB学生结果闭环 ](../work/tasks/P-011-wb-student-results.md)，无预算active goal继续。活动树C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync，分支codex/p010-wb-discovery；原bioimage-tools-platform旧dirty树不碰。

- P010调研已完成并经PR61正常合入main87dba64196f8591405dd222f05a69dca07434291。P002/M1/M2/P009不重做。
- 当前产品HEAD4dcd41e（修复身份草稿共享），合入main提交411aadb，产品918af16，测试修正e349b2e，视觉证据1970937。P011回执已重载新基线，唯一当前integration清单历史为空；P010/B019原回执在main完整保留，未删改门禁。
- 产品PR60仍draft：https://github.com/Junweiiii14/bioimage-tools-platform/pull/60。7e875d1的rules-context和desktop已成功，双平台旧运行41839649342不能覆盖4dcd41e；本次提交审查记录后push触发最终CI。旧head35cfe的Windows/Linux全门禁与desktop已成功，不能代替新HEAD检查。
- 本机全门禁91098已终态exit1：1696pass/5fail；父目录p011-check-all.log。定向诊断发现两处测试入口/同步问题：native freeze无网页token触发正确的dirty保护；snapshot预览读取未完就continue。只改测试走真实按钮/等待ready，3例通过；没有改产品保护或门槛。
- 当前端到端单图/三联图/无效反例3例通过，解析面积/背景边界/旧wire5例通过。CDP实际画面已查看，证据work/evidence/P-011/visual；Qt grab可陈旧，CDP工具打印0xc0000139但exit0，仍不代表干净目标环境验收。
- 没有本机测试进程仍需等待；91098、78523、39739、56657、65363、63827、23692均已终态。自行启动原生窗口45312及子53468已正常关闭。下一步只追踪PR60新CI，勿重启已完成测试。
- 只读独立审查已完成：初审发现身份草稿共享P2，4dcd41e修复；独立Node及真实GUI复审通过，见P011/independent-review.md。独审绑定最终产品提交；作者自验不算独审。尚未满足产品合并/goal完成条件。
- 用户不知道真实配对/处理组/重复/原软件背景方法，并要求少问自主推进。科学语义保持UNKNOWN，合成输入不证明真实实验效果；独立学生试用、科学留出与干净Windows/DPI待办见risks，不冻结无依赖工程。
- 用户不要过度设计：普通文案/交接随任务处理，不扩展其他实验、Agent、安装器发布、外联、花费或数据上传。
