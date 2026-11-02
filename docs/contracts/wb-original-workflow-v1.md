# 原值WB工作流节点 v1（P005开发中）

三个固定注册节点自动处理原始整数TIFF；不增加旋转、阈值或积分方法。原wb_v0_compare对照入口、profile_integral@1数值、旧schema及历史文件不变。节点输出仅candidate，正式结果仍由共享RunSession观察实际OS/进程树退出、检查全部文件并经Workspace事务提交。

1. wb-verify-original / original_tiff_validation@1：原AssetRef→validation.json小型凭据。实际检查大小/SHA、TIFF解码准入、uint8/uint16、YX shape及原始坐标源SHA。凭据保留明确未知的仪器位深/范围/物理标定，不把解码类型当仪器来源证明；不复制大型原TIFF，也不赋予科学准确性。
2. wb-analyze-original / profile_integral@1：同时接原AssetRef与完全同源凭据，重验实际原文件/解码描述/转换，再调用既有analyze_annotations，输出完整旧AnalysisResult。参数仍为既有AnalysisRequest，固定fresh document0/fixed_grid@1/legacy_bounds@1；源SHA显式绑定，图generation另存。未修改旧数值实现或质量状态。
3. wb-publish-original / wb_original_report@1：完整AnalysisResult→measurements.csv、curves.json、灰度report.png与report-manifest.json。有效值包含真实0；invalid/quality_review/excluded/not_detected的主value为空，状态/原因及仅供复核的原积分分别保留。CSV沿用可逆text:前缀避免公式执行；完整原始/极性剖面不平滑、不截短，不假称单条SeriesMetadata。报告是显示资产，不进入定量；按CSV顺序标明行号、值和状态，源/样本/条带全文在CSV及JSON。

发布参数的compact/comfortable只控制显示行距20/28像素，expected_rows冻结完整行数；报告宽1200，高140+行数×行距，拒绝超出既有3200万像素预算，不截断行。新报告渲染/模板版本为@1，不替换旧figure_display@1。节点总成果仍16MiB，IPC仍1MiB；原图只走引用。Pillow沿用已锁定figures/desktop可选依赖，不新增依赖。

新WBWorkflowStart以有界端口→绝对文件路径列表传递最多8个输入，原始ExecutionEvent身份/序号保留到ProcessEvent.module_event；匿名hello来源仍由宿主attempt/run绑定。新固定--worker wb_workflow入口仅按三种固定ModuleSpec处理，不从工作区加载Python模块。旧运输信封/代码路径保持。

模块实现摘要读取固定生产源文件；环境包括Python、依赖、OS/CPU、图像codec及TIFF准入配置。宿主workflow_runtime_environment另外计算实际已安装contracts/runtime/desktop源码摘要；必须在后台实际核对后才能执行/复用。当前节点只验证自身环境及宿主字段存在，不认证宿主自报摘要就是真实准入；GraphSession的当前注册/环境认证接线仍待实现。加载历史用于查看与允许当前执行必须分开，不静默迁移旧计划。

RunSession的require_dispatch_ack为新增可选宿主确认路径：真实PID已入库并通知started后，待宿主持久化账本started，再用匹配run_id/pid的authorize_request允许发送请求。默认旧入口保持原行为；取消或已退出拒绝新授权。该路径解决快worker终态先到时丢失running过渡的问题，仍须由通用工作流会话真实使用，不把测试父进程串接节点当成自动调度器。
