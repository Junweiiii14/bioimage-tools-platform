# 工作台显示快照 @1

T082 R09 的当前本地WebChannel投影使用`snapshotContract="wb-workbench-snapshot@1"`。
这是显示传输表示，不改变持久项目schema1–15、科学参数、原像素、结果值、导出或保存协议。

- 顶层`cells`完整保留结果顺序、rowId、Fig/蛋白、泳道、value/rawIntegral、status/reason。失败、缺失和有效零严格区分；不分页截断、不重新计算。
- `rows`不再重复传输每行同一结果对象。客户端在安装快照前以rowId一次分组，为缺少`results`的行恢复数组，成员引用顶层cells中的原对象，保留次序。旧完整/演示快照显式的`rows[].results`继续接受，不借恢复覆盖明确编辑。
- `sourcePreviews`沿用以原源SHA标识的显示PNG字典。仪器sources和rows对同一预览共享该字典，wire上的preview为null；客户端分别按`source.asset.sha256`及`row.sourceId`恢复显示链接。旧内联preview仍优先支持；独立zoom保持原有高分辨率请求/身份守卫。
- 结果构造按rowId建立一次临时索引；不创建第二份持久结果权威。仪器来源投影复用公开`intake_snapshot`已经产生的数据，不二次逐源序列化。没有改`quant.table`与cells之间不同的状态/积分含义。
- 项目、sessionEpoch、revision、编辑身份、CAS和R03解析/渲染失败回滚保持。恢复工作只操作显示对象，不写原图或原生项目。新页面继续读取此前无snapshotContract的完整格式；未知未来合约不可据此推断兼容。

验收包括完整结果/顺序/有效零与失败保持、传输预览引用可解析及真实图像加载、旧完整载荷、当前草稿/选择与跨会话恢复；同输入/预算的性能前后证据保存在T082。不能只因JSON变小就宣称目标场景或科学适用性已通过。
