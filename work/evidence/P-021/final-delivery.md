# P021 固定研究工作流工程交付

2026-11-06，PR [73](https://github.com/Junweiiii14/bioimage-tools-platform/pull/73) 按上游在独审通过后的明确集成安排正常squash合入，未绕过规则。准确受审候选 `3f425b5ba5804b5d542980f3410ddda2d177c9cb`，原base `aa3302ad2980dfeec1ac6f7776fec6176f18fcda`；main `2a3c7a32936c6e4daf63dac23fb953cc4512e840`。`git diff --exit-code <candidate> origin/main` exit0，整个树相同。

## 实际可用

`uv run --locked --no-sync python -m bioimage_app` → 工作流编排 → 项目与模板。可新建固定核分割/BCA研究图、添加本实验兼容节点、绑定原始输入、保存预检与后台执行、查看已提交成果、保存模板并换合规输入复用或冷重开历史项目。核分割需已有受信worker/模型配置和单帧uint8灰度TIFF；BCA需长CSV及对应确认板记录。详 [操作入口](../../../docs/runbooks/research-workflow.md)。

复用P009执行器/Workspace和工具公开API，未新建引擎/插件框架、未改第三方算法、模型、依赖或门禁。两张作者真实StarDist图46/18核标签与P015逐字节相同，BCA两份CSV与同输入CLI相同。旧schema1读取不迁移，显式保存新修订才转schema2。输入/结果完整性、partial及失败语义保持；R01恢复准入先于创建，R02只在真实工作区切换后撤销旧ready，取消/dirty拦截保留原草稿。

## 准确候选验证

- [最终独审](independent-review-3f425b5.md) pass，R01/R02/N01全部关闭；独立9项回归、两入口反例、旧46核冷读及exact规则通过。未改科学链的证据沿用初审，原changes_required和失败日志保留。
- [quality 42212939235](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42212939235) success，head为3f425b5；Windows完整check --all：1774 passed/10 warnings/1029.07s；Ubuntu：1770 passed/4 skipped/10 warnings/948.59s。两平台后续wheel/独立安装检查及desktop-environment成功。3条研究worker依赖源码解析警告保留。
- [rules 42212939301](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42212939301) success。服务器四项必需检查全通过；native-case为本次普通流程不触发的SKIPPED，不伪称执行。
- 原始准确CI日志为ci-final.log.gz；本机混合源码全量exit1/1770passed仅诊断，唯一旧R01已修复，不改写为成功。29项原证据索引SHA全部核验一致。
- 本次集成后仅核对main同树和本地交接文档，不重复未变科学链/全量，不为纯收据推候选。

## 保留边界与交接

当前是固定研究方法编排MVP。完整跨实验语义组合、插件安装卸载、Agent、科学/化学准确性、LoQ、训练重叠/患者独立性、真人、物理DPI/OS IME、目标机及用户安装更新均未完成；旧GPU警告未声称修复。原图、历史结果、旧dirty树及安装保持原样。

一次本地收尾在codex/p021-closeout，以main为基线；只含任务/规则回执/交接/证据，随下一任务带入，不推纯收据。提交完成后活动树释放给上游，下一个任务由上游新窗口明确派发，本窗不另起产品任务。
