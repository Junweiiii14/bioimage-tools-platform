# 仪器清单阶段账本 v1 / 项目schema11

T055/E2在schema10清单上新增`WBIntakeWorkflowProject/schema11`与
`IntakeWorkflowLedger(policy=intake_workflow@1)`；旧schema1–10读取保持，旧10读取器拒绝11。
准备操作创建正常CAS草稿修订，原草稿/原图/已完成结果不覆盖，不改变平台opaque文档格式。

## 公开接口

`wb_tool.api`导出`prepare_intake_workflow`、`intake_workflow_digest/snapshot`、
`approve_intake_workflow`、`claim_intake_workflow_step`、`finish_intake_workflow_step`、
`request_intake_workflow_cancel`、`recover_intake_workflow`、`retry_intake_workflow_step`、
`return_to_intake_editing`及项目/账本/阶段/票据类型。准备需要当前已确认清单摘要，
运行批准和重试需要当前账本摘要。先批准执行摘要才能claim。

## 阶段与身份

- 每个蛋白行一个crop，每个Fig各一个compose、measure，最后一个项目export；阶段最大1537，不能缺项/重复/换顺序。
- crop不依赖其他行；compose依赖所属Fig全部crop done；measure依赖该Fig compose done；最终export依赖全部Fig measure done。
- 优先推进已就绪Fig，再开始下一行crop。失败/待复核只阻塞所属Fig，其他完整Fig继续；部分进度不标整批成功。
- 状态pending/running/done/needs_review/failed/cancelled/interrupted。只有一个活动阶段，异常状态必须有明确原因；每次claim递增attempt，票据绑定项目/清单摘要/阶段/目标/attempt/会话派生claim ID。
- 旧票据、其他项目/修订输入、重复回复拒绝。请求取消只记意图，活动状态维持running；所属执行器确认退出的回调到达后才能结束。取消期间迟到done变cancelled，不抹去既有真实run。
- 加载恢复将running标interrupted、撤销运行批准，不自动续算不明进程；保留attempt和完成记录，核对后可重试。归档资产重映射后更新清单/账本摘要，旧票据不沿用。
- 重试只允许异常阶段，无活动任务时进行；重置所依赖的Fig后续阶段及最终输出，其他Fig已完成记录保持。重新批准后再claim。

账本是编排进度，不是定量成功收据。`stages_finished`只表示账本阶段记录已终结；
数值、真实零值和运行有效性必须继续使用既有RunRecord、OS退出回执、资产/结果核验。
纯状态测试的done不创造ROI/run/信号，不可据此向用户宣告科学结果或输出完整成功。
执行器完成后也须先持久保存再安装/展示新快照。

票据与活动阶段额外绑定完整输入摘要（不含账本及保存修订号），覆盖ROI、空槽、
复核与模板参数。先在冻结输入上核验并结束票据，再合并执行器产物；
不能先修改running快照的ROI等输入再接受旧回复。嵌套账本/阶段实例重新验证，
`model_copy`不构成绕过状态约束的入口。schema11尚未发布，以上为v1首发约束。
保存提交前取消则不提交；CAS提交中取消保留已提交历史、拒绝安装派生计划，
当前清单草稿标记未保存，下次显式保存创建后续修订，不能覆盖回滚历史。

## 清单、草稿与兼容

清单仍为身份权威：schema11行身份/名称/来源/尺寸/N和Fig顺序必须匹配清单；
只允许ROI、复核、空槽标记与说明作为行派生字段。保留来源池及旧各代证据。
准备是幂等的；未执行过的准备可通过return_to_intake_editing回到schema10继续编辑，
有实际尝试后不能用该操作删除阶段历史。输入修改的下一执行快照另行明确处理。

当前E2桌面接通后台计划准备、CAS保存/重开、执行摘要和异常原因；
尚未接入真实裁剪执行器，因此没有“开始”按钮或虚构测量结果。E3接执行器，
E4/E5接拼图、原像素测量、输出与证据，阶段变更仍遵守同一票据/取消规则。
