# P011进行中验证

活动树bioimage-plan-sync，HEAD3caf797，产品修改未提交。Windows本机Python3.12/Qt，现有锁依赖。

- P011 context --scope . --record --integration：exit0，回执同目录。
- 定向identity/machine/normalization：6 passed，40 deselected；网页原测试2 passed；原生网页身份保存+导出忙态2 passed。
- pyright及npm check:web在新增连续回归之前通过；最终候选尚待重跑。无锁/依赖变化。
- 连续回归 tests/test_wb_student_results.py：最新exit1，1 failed/1 passed，18.23秒。正例值仍无效；负例全部失败行可导出/保存重开，原始输入和既存归档SHA不变。测试先修复DOM重绘后的失效元素引用，未放宽busy guard或质量阈值。
- 三联图、Gaussian及矩形候选均在当前批次common采样限制下缺少背景。历史prepared路径允许扩大背景，不能作为当前路径完成证据。原因见任务；下一步解决方法衔接，当前不能称最小完整流程完成。
- GPU/mailbox日志仍有；window.grab先前截图不能可靠反映抽屉，没有合格视觉验收结论。真实学生/独立科学/干净Windows未验。
- 全门禁、独立审查、PR和集成：未运行。保留历史回执，不绕过门禁。

## 后续修复验证

新增bounded_background_context@1：原目标不变，仅有界开放原坐标背景上下文；记录版本，旧wire省略默认字段。当前网页真实worker/归一化/导出/重开正反例2 passed，19.31秒，exit0。反例改为含dtype_min原值，仍明确无效；原先背景不足在旧limits解析测试保留，没有改质量预期为成功。

新5例通过：解析面积13×30000、其他条带、膜孔洞、裁图界限、旧wire/未知版本。首次新测试有两个测试代码错误（遗漏polarity与strict Python tuple输入），修正为显式dark及真正JSON wire；未修改产品以迁就测试。现有几何/自动裁图42例通过。

全门禁首次被新测试长行ruff拒绝（exit1），仅断行后再次执行；当前session91098仍运行。静态/类型/边界/web通过，pytest尚未完成。日志父目录p011-check-all.log，勿提交长日志。原生grab仍没有可靠显示抽屉，视觉验收未通过。待最终独审与集成。

## 集成阶段修正（35cfe0b）

PR60 rules-context失败：Integration needs exactly one changed integration context。原因是P010/P011均含集成清单；不删除/重命名历史回执、不修改门禁。按既有runbook拆文档前置PR61（head3caf797，basec8f1bcb），本地准确base/head规则检查exit0；PR61服务器rules-context与desktop-environment已SUCCESS，foundation双平台仍运行。待PR61按必需检查集成后，再更新P011准确基线及回执。PR60保持草稿。

本机check--all session91098仍live（pytest已到38%，至少4fail，未出最终摘要）。此轮未重启测试。原自行启动验收窗口45312的真实子进程53468已CloseMainWindow正常退出，父/子均确认不存在；未强杀或操作其他应用。

## 全门禁结果与测试入口修正

本机check--all（session91098）已终态exit1：1696 passed / 5 failed / 11 warnings，1427.22秒。失败：v5恢复批次、两个旋转canvas、失败route诊断、workflow cancel退出。原日志父目录p011-check-all.log保留；含GPU context-lost及一个子进程UTF8解码warning。后续未把失败抹为通过。

使用CI相同offscreen/--disable-gpu定向5旧失败+3新端到端：7 passed/1 failed，65.02秒；旧cancel仍超时，新单图、三联图、dtype_min反例均通过。静态Qtgrab能显示抽屉，但显示内容帧仍陈旧，不能称完整视觉验收；下一步用已有CDP捕获路径验证真实当前DOM。

隔离cancel诊断1 passed；原顺序组合诊断2 failed/3 passed。失败时捕获stage=confirm_draft、authoring.dirty=True、batch=cancelled/closed：测试直接native freeze没有网页pending token，网页正确保护未知回执后的草稿。修正测试为连接就绪后点击真实wf-run按钮；不自动丢弃草稿。v5测试的snapshot会发起预览asset读取，因此在继续请求前等既有wait_saved（不延长超时、不绕过busy）。这三例最终3 passed/12.43秒，exit0。临时print诊断已移除。产品取消/保存代码没有修改。

PR60 Ubuntu foundation已SUCCESS，Windows仍运行；PR61的规则和desktop已SUCCESS，foundation仍运行。待准确最终HEAD所有必需CI与独审，不凭定向通过宣称全门禁完成。
