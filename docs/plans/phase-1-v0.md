# 第一阶段V0：现有WB用例独立运行到真实成果

授权：2026-10-31用户要求GPT-6 Astra在新聊天使用目标模式持续推进第一阶段。阶段以[研发总方案3.0](research-platform-rd.md)第2、3、4、12.2、13.1节为准。

先完成P001：核对远端与本地T082，保留全部dirty和历史科学/环境缺项；把方案与任务接入正确产品树，按该树协议生成实际base对应回执及必要integration清单，不覆盖最新规则。不将本轮文档PR误作产品基线已接入。

然后完成P002及V0必要配套：选一个成熟旧WB用例，经wb_tool.api、最小ModuleSpec/ExecutionRequest/ExecutionEvent/OutputManifest真实调用；复用已有worker及Workspace提交，不复制科学公式，不把显示图送入计算。ScientificAsset按需组合既有AssetRef，V0不引入float校正方法。

必须交付：无GUI可调用入口；一个保持现有工作台风格的薄对照入口；真实运行生成measurements.csv、differences.csv、run-manifest.json；正常/异常样例；保存后重开、旧历史仍可读；绑定提交的独立审查和适用门禁；可复查PR及中文操作说明。对照结果不能复制旧表伪造。

达到上述结果才结束本阶段目标。不能只完成任务卡、空接口或文档即完成，也不能在V0顺带进入自动校正V1、IF、自由节点编辑器或科研Agent。方法科学证据与现场用户验收未取得时如实列明，旧工程等价不冒充新方法验证。

执行状态只在P任务卡，GitHub issue是讨论/链接入口。新聊天先调用create_goal建立真实目标；用户未设置token预算，不自行给预算。持续处理已授权实现、故障修复与审查，直到V0完成或遇到确实需要外部输入的具体阻塞。
