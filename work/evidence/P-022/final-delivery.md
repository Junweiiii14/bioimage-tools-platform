# P022 可选工具装配工程交付

2026-11-06，PR [74](https://github.com/Junweiiii14/bioimage-tools-platform/pull/74) 按上游授权及固定独审集成判断正常squash合入。准确受审候选 `47ded5e5e3ef01afadadf2b9a76e9c59cbb8ed69`，原base `2a3c7a32936c6e4daf63dac23fb953cc4512e840`；main `b13e71aa5aaebe91edecde44f386fc20ef693b19`。集成前四项必需检查全绿、head精确匹配、CLEAN；集成后完整树diff exit0。

## 实际可用

普通桌面入口支持仅平台、WB/核分割/BCA各单工具及全工具。主页设置允许下次启动启停；缺包、停用与缺少核分割worker/模型分开提示。缺工具历史不可执行且原字节保留，其他工具可继续。开发环境默认仍含三工具；安装组合及入口见[可选工具运行说明](../../../docs/runbooks/optional-tools.md)。固定可信注册，无热插拔或任意代码加载；方法、上游算法、权重、参考和第三方依赖版本未改变。

作者隔离wheel矩阵完成三工具真实运行、正式保存和冷重开、WB停用/实际移除后的剩余链与历史字节保护，详[原证据](README.md)。R01在任何打开状态写入前检查WB可用性，缺包/停用真实Qt拖放后仍能实际执行BCA；N01同步驱动使用前一进程的真实设置。

## 准确候选验证

- [首审](independent-review-47c8d08.md)changes_required保留；[最终独审](independent-review-47ded5e.md)pass，R01/N01关闭，独立两环境drop/BCA提交与15项相关回归通过；未变13场景装配等证据按报告沿用。
- [quality 42221567451](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42221567451)最终success，head准确47ded5e。Windows首轮1777 passed/12 warnings/1485.33s；Linux唯一一次失败job重跑1773 passed/4既有skip/12 warnings/693.92s。两平台均完成后续wheel与安装工作流检查。desktop-environment和[rules 42221567439](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42221567439)success；native-case为普通流程不触发的skip，不称执行。
- Linux首轮在既有BCA图测试收尾挂起，60秒Python栈位于storage retire的moveToThread，最后20分钟job上限取消。完整失败与成功日志分别归档为p022-ci-linux-failed.log.gz和p022-ci-linux-attempt2.log.gz；Windows为p022-ci-windows.log.gz。
- 本机相关16项22.33s/exit0，记录p022-ci-close-repro.log.gz。此前跨R01修复执行的本机check --all exit0，仅诊断而非准确候选全量证明，原日志p022-check-all-final.log.gz保留。
- [固定独审集成补充](integration-review-47ded5e.md)核对关闭链和以上证据，未发现具体新增关闭缺陷，允许保留UNKNOWN非阻断风险后集成。不证明本PR与挂起无关，也不把一次重跑成功当作根因修复。无测试、容差、skip、超时或门禁削弱；不再重复测试。

## 未验与交接

Linux窗口收尾挂起根因UNKNOWN保留，不能称已证明旧问题或基础设施故障；下次真实复现需端口身份和原生线程证据。科学/化学真值/LoQ/训练重叠、真人、物理DPI/OS IME、干净目标机、冷缓存/峰值内存、用户安装更新及发布仍未验。逻辑文件大小不等于实际增量磁盘；样例与封装一致不等于科学准入。

一次本地收尾分支codex/p022-closeout以main为基线，仅任务/交接/规则回执/证据，不推纯收据；随下一任务带入。提交后共享bioimage-plan-sync释放给上游，下一新窗口由上游派发准备可运行交付候选。本窗不续开产品任务；卡片堆叠设计仅聊天预览，未加入软件。旧dirty树、原图、历史、在用安装未修改。
