# 方法与数据评估基础 v1

本契约对应P003的D1设计/工程评估基础，不授予任何方法S1。公开入口为tool_contracts.api的数据/方法/计划/观测/报告模型，以及platform_runtime.api的method_plan_digest、dataset_partition_issues和evaluate_method。旧AssetRef v1、Workspace/schema及WB公式保持。

ValidationDataRecord区分合成解析预期、独立参考和来源目录引用，记录payload SHA、实际文件/解码/许可用途状态、来源分组及父记录、分区、单位和完整原来源JSON。目录条目保留其原始访问/下载/标注/许可说明；本次未实际核验的源文件payload SHA仍为空、文件/解码状态not_verified，不能因论文或目录可读便写成本地已下载。来源分组ID须在当前登记集合内具有全局含义，父子闭包防止同源裁片/缩放/同采集派生物跨开发和留出。未知分组、缺父、环和同源泄漏阻止评估通过。

MethodEvaluationPlan在执行前冻结精确ModuleSpec、方法/实现摘要、环境、输入记录、参数摘要、每例期望状态/值/单位、参考来源与绝对容差。method_plan_digest按本版本模型JSON字节SHA256计算；字段/序列化语义改变需版本化，不以重新计算摘要伪装旧运行。MethodEvaluationEvidence包含绑定计划摘要、实际实现/环境及每例输入/参数/观测；缺失、额外或重复观测、身份变化、缺参考/容差和未准入数据不能通过。严格Python值先重新校验，再序列化，避免model_copy注入的bool被JSON数值序列化掩盖。

只有valid有有效数值；真实0保持0，invalid/quality_review/not_detected/excluded/missing/failed为独立状态和空值。有效数值均有限，差值溢出保留空误差并标失败。工程报告保留每例比较、完整分母、plan/evidence摘要及frozen_reference_compare@1版本。错误状态与独立预期一致可通过工程失败语义检查，不表示该测量可用于科学统计。

requested_use_allowed只允许通过的engineering请求。scientific请求即使数值完全一致，也保留诊断报告并拒绝准入；本框架永远不生成批准者或S1。MethodReadinessRecord只登记D1、真实工程报告摘要、适用输入、负责人角色/未取得的姓名及待补材料。ready要求已实现方法与真实报告引用；WB新校正候选的版本/实现仍为空、pending。正式方法准入须另任务核验独立材料、负责人认可指标/容差、适用域与准确实现，不能用当前工程布尔结果替代。

## 实际命令与产物

```
uv run --locked --no-sync python -m tooling.wb_method_validation --output .local/wb-method-evaluation-001
```

必须新目录，不覆盖历史。命令先读取P001已有独立解析预期（40/4000/有效0/无效空值/位深复核空值），核对生成图的像素/dtype/ROI与冻结定义，再写plan.json，然后调用真实wb_tool.api.execute_wb_module。输出原合成TIFF、各例实际机器结果、observations.json、report.json、method-register.json及source-catalog.json；校验原合成输入不变。目录引用来自B007已有登记，不下载外部数据。工程通过exit0；加--scientific后数值报告仍可生成，但请求不获准入、exit2。

参数/来源文件为有界严格JSON，重复键、非有限数和未知病例拒绝。部分失败保留新诊断目录，不伪称正式Workspace结果或科学成果；本命令是评估工具，不替代P002真实worker/Workspace发布路径。

安装检查追加无WB/Qt/NumPy的runtime/contracts隔离wheel评估调用、有效零和来源泄漏拒绝，原门禁不删除。真实WB解析用例、输入变化、缺参考及来源分组性质测试独立验证。完成状态、准确提交/命令/退出码和科学/目标机限制以P003任务和证据为准。
