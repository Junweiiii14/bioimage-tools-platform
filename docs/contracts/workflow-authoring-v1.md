# 工作流编辑与模板 v1

编辑是app层适配，复用P007的WorkflowDefinition/WorkflowLayout和P008同一编译器、WorkflowBatchSession/WorkflowSession。没有新的科学算法、缓存引擎或Workspace数据库结构。

## 草稿和提交

Workspace opaque文档tool_id为workflow_authoring_v1；AuthoringProject.schema_version=1，含document_id/revision、graph、layout、sources、最后冻结批次标识和初始合法seed。graph允许不完整节点/边/输入/输出；保存不等于可运行。真正执行必须转为严格WorkflowDefinition并通过受信目录的同一预检。

固定命令initialize/load/save/freeze/bind/export/results/open在唯一AsyncStorage所有者线程处理，GUI只消费投影。编辑命令携带previous_revision，CAS冲突保留用户本地草稿。计算图revision仅在计算定义变化时增加；文档revision包括标题/布局保存。先持久化冻结批次再派发。编辑文档CAS失败不会把未启动批次写成成功。

Web端拥有当前草稿serial和表单DOM；保存回执仅确认提交时的serial，不替换其后的编辑。初始化、打开项目及显式绑定新输入才替换图；结果回执不能替换当前草稿。运行状态映射使用冻结节点和真实批次，不能用正在编辑的节点标签冒充已执行内容。

## 可移植模板

新GUI导出格式：

```json
{"template_version":1,"definition":{"schema_version":1,"...":"WorkflowDefinition字段"},"layout":{"positions":[]}}
```

上例只示意封装，不是可运行流程。实际definition完整保留严格WorkflowDefinition，layout为WorkflowLayout。GUI和CLI通过load_workflow_template共同读取；原P007/P008无封装的WorkflowDefinition JSON继续接受，生成默认显示布局。未知版本、未知字段、重复键及非有限数由既有严格JSON/模型边界拒绝。

新封装不改WorkflowDefinition格式，不改旧数值或RunRecord。已有只接受原始定义的外部消费者需要升级为封装加载器，不能声称所有旧消费者无需修改。CLI的传统--template-out输出仍为原定义格式；GUI导出使用v1封装。导出采用新文件创建，不能覆盖旧模板。绑定新来源时沿既有WB模板绑定器替换原始资产/关联元数据，保留明确分析参数；不猜新实验身份或阈值。

## 结果与恢复

结果来自持久化批次及相同冻结子图的已提交结果，核对实际RunRecord和资产摘要。文件打开命令必须带冻结batch/sample/node/port身份，不能让网页传任意路径。中间成果仅显示已提交节点；缺失、失败不变为零。PNG预览及表格截取由存储线程读取，预览限制不改变定量资产。

展示/打开与缓存复用共同调用公开validate_workflow_result_selection，对照实际run.result的OutputManifest，不把可变子账本中的输出选择当作提交证明。核对完整输出/质量、原始source_execution/node/attempt、计算键及冻结模块/参数/输入；缓存结果保留原来源而不强绑当前节点标签。错绑已存在资产同样拒绝，不能仅因文件SHA正确便宣称属于该运行。

编辑服务与批次共享一个存储端口。退出等待编辑请求、子worker和所有存储所有者排空；冻结回执前取消/退出不应随后派发。暂停重开保留冻结意图，显式继续才执行。不可执行的历史模块版本/参数保留草稿并解释问题，不用当前新版本静默替换。

验证范围及尚未完成项见work/evidence/P-009/connected-editor-progress.md和P009任务卡；最终准确提交独审、CI及视觉/性能证据单独记录。
