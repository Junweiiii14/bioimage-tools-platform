# P022 集成判断补充

2026-11-06，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`。绑定PR74、base `2a3c7a32936c6e4daf63dac23fb953cc4512e840`、准确head `47ded5e5e3ef01afadadf2b9a76e9c59cbb8ed69`。产品、测试及门禁未新增修改；既有最终独审pass保持。

**判断：可按现有PR规则集成；本次Linux挂起作为UNKNOWN、非阻断风险保留。** 这不是证明本PR与挂起无关，也不是把一次重跑成功写成根因已修复。本次仅核对日志、关闭调用链及服务器状态，未运行新测试、矩阵或重试。

## 已核事实

- `gh pr checks 74 --required --json name,state,link`返回四项必需检查全部SUCCESS：rules-context、desktop-environment、foundation Windows及Ubuntu。PR当前base/head准确，OPEN、mergeStateStatus=CLEAN；native-case为原有非必需SKIPPED。
- [首轮Linux job](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42221567451/job/127904879438)于BCA图测试的fixture teardown阶段未完成关闭。60秒faulthandler快照显示工作线程在 `storage.py:135 _StorageWorker.retire → moveToThread`，主线程在 `qt_test_lifecycle.py:46` 等待窗口资源退出。随后触发既有20分钟job上限，服务器结论cancelled；不是测试通过。该Python快照不能识别具体存储端口、原生锁持有者或互等关系。
- [同SHA唯一一次Linux重跑](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42221567451/job/127917867647)完整成功：1773 passed、4 skipped、12 warnings，随后完成独立wheel检查。原挂起用例本次明确PASSED并继续后续测试。四个skip对应既有Windows shell/private-CPython边界；相关测试及workflow无diff，没有为通过增加skip或延长timeout。
- [Windows首轮](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42221567451/job/127904879952)完整成功：1777 passed、12 warnings，完成wheel。作者本机相关16项22.33s通过为辅助Windows证据，不代替Linux复现或根因定位。

## 为什么当前不新增产品阻断

没有发现具体漏close、漏接结束信号或提前销毁所有者的新增代码证据。失败fixture采用全工具默认启用设置，本次optional guards仍走原装配分支：WebWorkbenchWindow继续关闭authoring、nuclei、bca及WB，并等所有实际resources_closed后退出；AuthoringSession等批次与pending请求排空再shutdown storage，bridge在finished后释放session。AdvancedHost搬移未改变关闭转发或父子关系。该端口已进入retire也不能被解释为“未发起close”。

`storage.py`、关闭测试helper、相关fixture及BCA图测试对base无diff，但装配和加载时序可能影响并发，因此**无diff只用于限定调查范围，不用于排除本PR影响**。当前证据证明一次真实关闭挂起、同一候选后来完成全门禁；未形成可复现且可归因新改动的阻断项。结合已完成的独立装配/生命周期验证、准确head无改动及全部必需检查成功，可在保留风险的情况下集成。

## 保留事项

首轮失败和重跑必须分别归档；不能写成首次全绿、问题已修复、已证明旧问题或纯基础设施故障，也不能与先前GPU/QTest探针异常未经证据合并归因。当前UNKNOWN是“Linux全量运行后窗口收尾在storage retire期间无进展的原因”。后续若再次出现同一关闭症状，按真实复现补端口身份/原生线程证据并重新评估，不在本轮无限重跑。

所核原始日志为作者冻结工作树只读的 `.local/p022-ci-linux-failed.log`、`p022-ci-linux-attempt2.log`、`p022-ci-windows.log`、`p022-ci-close-repro.log`；本审记录路径、大小及SHA于 `.local/integration-log-index-47ded5e.json`。上游一次收尾时将失败、成功及UNKNOWN纳入交付/风险记录，不为纯收据再次改产品或重跑矩阵。本补充更新最终报告当时“CI待终态”的事实，不改写其当时状态或旧失败。

本窗口只回传集成判断，不代上游合并、发布、更新用户安装或释放作者树。
