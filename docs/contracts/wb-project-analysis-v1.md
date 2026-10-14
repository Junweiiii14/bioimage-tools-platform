# 项目定量计划与结果引用 v1

本契约对应独立 `wb_figure_project` schema v3 / `WBAnalysisProject`，继承v2的行计划与候选快照。v1/v2继续读取；旧单图文档、积分算法和worker协议均不变。首次配置定量才进入v3。

用户2026-10-14确认CLX不在范围；TIFF是设备原图，TIF是裁剪产物。软件继续接受 `.tif`/`.tiff`，格式名与扩展不能独自证明某个文件的测量身份。保留明确选源和原图SHA/裁剪坐标，不开发CLX解码。

每行 `ProjectRowAnalysis` 保存row_id、配置时的整行crop、空泳道元信息、AnalysisRequest及可空的终态RunRecord。N由完整固定网格确定，泳道位置不能因空位删除；首个项目闭环每泳道仅一个稳定 `target` 条带，可编辑边界/基线/包含状态。源SHA、ROI、泳道顺序和条带身份必须一致。手工空泳道强制excluded，其他泳道初始bounds=None，不能把整块裁剪自动认作正确的积分区间。

计划本身不包含大幅profile或测量副本，仅引用已提交运行的不可变结果资产。run的document_id=项目ID，revision=所用AnalysisRequest.revision，且不得大于当前项目revision；仅保存succeeded/cancelled/failed/interrupted终态。结果值只有在资产字节数/SHA、严格JSON、ResultFrame一致性以及请求全部匹配后才可用于填表。运行时宿主仍须走原有PID、进程退出、平台事务；引用一个候选结果对象不等于完成运行。

修改原图/裁剪/N/空位/撤回审核/统一高度使当前计划stale；不删除不可变旧运行，表格不给旧有效数值。Fig/蛋白名称与排序变化不改变测量，重复名称仍以row_id区分。请求边界/基线/极性修改会清除当前run引用。重新执行按本次即将保存的项目revision冻结选中计划，并清除其旧run；未选中行仍可保留原运行。后到的来源/请求/修订不匹配结果不得附着。

自动表逐行保留N槽，状态区分missing_source、pending_review、unconfigured、stale、not_run、cancelled/failed/interrupted、result_unavailable及已有valid/quality_review/invalid/excluded/not_detected。只有valid可有数值，其他状态为空且有原因；真实0仍为0。初步表按项目Fig/行顺序排列，并输出源SHA、请求修订、run_id、lane_id与band_id。尚不自动归一化，不按名称猜参照。

应用层依赖已有 [手工定量契约](wb-manual-analysis-v1.md)、[worker v1](wb-worker-v1.md)及 [工作区 v1](workspace-v1.md)，无新公式/第三方API选型。本阶段用两个不同SHA且同名蛋白的解析profile、零/缺失/空位、坏结果资产/过期请求验证。

宿主先保存同一revision的全部所选标注，每行prepare明确指定该revision并比对冻结文档，再逐个走真实RunSession。进程退出和提交后读取不可变结果资产，不以worker候选填表。结束将run引用保存到下一草稿；取消保留已经完成的行，未开始行不伪造cancelled记录。关闭等待当前进程和后台回调结束，保存引用后退出QThreads。generation改变只保留平台历史，不覆盖新草稿。重开逐个核对工作区RunRecord完整内容及资产，单行损坏/外来run引用不阻止其他行校验。准备后若输入损坏且未能启动进程，该准备记录留给既有恢复机制，不伪造退出收据。

每行请求初始bounds=None；先计算可得到原始曲线及not_detected状态，填写边界后重新计算。UI仅允许固定网格中的target边界/基线/包含状态，不删除空槽。结果页每页200泳道，项目曲线缓存按结果资产大小限64 MiB；超预算结果保留在存储，显示为未载入，不用历史数值冒充。项目表与严格结果校验在后台线程，GUI只呈现当前页。

XLSX复用现有单图表的字面文本OOXML与无覆盖发布，包含按Fig/蛋白的宽表及逐槽状态/来源表；缺失/排除为空，真实0为数字0，名称即使以等号开头也不是公式。每表仍使用现有200000单元格预算；超过明确拒绝。导出先保存当前项目修订。项目OCR/自动名称绑定、归一化和统一ZIP归档尚未接通，不能以本阶段定量/导出测试替代。
