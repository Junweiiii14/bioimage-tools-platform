# WB 独立 Fig 继续处理 v4

T080：`intake_workflow@4`。新的顺序配置确认调用 `prepare_intake_workflow(...,
batch_stages=True)` 使用 v4。已有 v1/v2/v3 文档保持其策略和阶段历史；只重开、继续或
再次运行不会静默升级。已有 v3 的明确分组修订也保留 v3 严格暂停语义。
外层项目 schema、定量公式、原像素和运行证据门禁不变。

v3 仍在任意 needs_review/failed/cancelled/interrupted 时停止整个批次；v4 只停止依赖
缺口的 Fig。v4 调度按 crop、compose、measure、export 优先序选择目前真正可执行的
待处理项；同阶段按清单顺序。所有蛋白原始裁图完成后才能合成其 Fig，Fig 成图真正
保存后才能测量。另一 Fig 的失败不改变这些本组依赖，也不把缺口挤掉、填零或猜测。

当所有当前可执行的非 export 项都已退出，而剩余项目只依赖失败/待复核项时，v4
允许领取 export 票据并保存部分目录。仍使用真实标准导出/运行核验；完整性由实际
结果决定。部分结果索引 `complete=false`，errors 保留真实缺项，export 阶段记录
failed，并保留 needs_review/failed 原因。不会把“已保存部分快照”当作整批完成。
若完全没有可成图的 Fig，部分目录可能没有恢复 ZIP，沿现有输出契约明确记录原因。

部分输出后不自动无限重试。人工修正原图范围或明确重试一个失败阶段时，只重置它
及其依赖 Fig/最终 export；其他成功 Fig、原始运行收据与槽位身份继续保留。命名目录
已封存时建立新代，不改写部分目录或旧 ZIP。全部测量实际完成且新完整索引经资产
导入与 CAS 后才把 export 记为 done。

重开后调用 `continue_intake_sequence` 且未提交新的 crop 时，v4 先检查真实可运行的
pending 阶段；存在时原样返回当前快照，由宿主正常保存/启动调度，不重试或改写
needs_review 项。可运行阶段已全部退出时才按已有顺序要求人工核对或重试失败项。
v3 的整批暂停语义不变，摘要过期和运行中继续仍拒绝。

用户取消仍是整批取消：cancel_requested、宿主取消 token 和活动票据终态规则未
放宽。新旧输入摘要、session key、generation、revision、单活动票据和先 CAS 后执行
规则保持。失败组继续不允许旧 worker 回复覆盖新修订。

桌面/网页接点：batch/follow/自动裁图接受/已保存 Fig 展示识别 v3、v4；v4 的 paused
只在实际空闲时成立，处理其他可用 Fig 时仍显示当前真实活动阶段。UI 不根据失败
数量推断整个批次成功；`complete` 仍要求所有阶段 done 和当前完整输出证据。

验收分别保留旧 v3 的真实页面暂停/继续测试与新 v4 的真实 worker 集成：第一个 Fig
裁图需复核时第二个完成成图/测量/部分输出；修正第一后全部完成，第二个 run、attempt
与 claim 不重复，旧 ZIP/原图字节不变。科学准确率与安装验收另按 T080 主任务记录。
