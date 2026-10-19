# 已确认清单的派生执行计划 v1

公开入口`wb_tool.api.build_intake_execution_plan(project, expected_digest=...)`，返回
冻结dataclass `IntakeExecutionPlan`及`IntakePlannedFigure/Row/Slot/Cell`。
策略ID `intake_execution@1`，不改项目schema10，不新增工作区格式。

仅接收通过完整模型验证的`WBIntakeProject`；摘要必须匹配且清单已明确确认。
无文件读取、目录创建、OCR、ROI、测量或默认样本配对。计划不是新的持久化权威：
项目保存重开后从schema10重建，不能将外部序列化的计划直接当作有效运行授权。

- Fig与行身份使用原清单ID；槽位ID由项目ID/行ID/1起始槽位编号进行带策略命名空间的SHA256派生，不含名称、Fig排序或像素位置。
- 同Fig各行有独立槽位，编号不代表跨蛋白同一样本。N包含空槽，不含Marker；计划只确定数量，不宣称位置正确。
- `figure.position`与`row.layout_row`为0起始显示位置；`slot.position`为1起始行内槽位编号，缺图/未完成不能压缩这些预定位置。
- `geometry_key`绑定项目/行、source ID、原SHA、尺寸、位深、N；不绑定名称/显示顺序。它仅标识定位输入，后续ROI、定位算法和测量参数必须再进入各自运行键，不能把该键当作结果有效性证明。
- `plan_key`绑定策略、项目与完整清单摘要，不含保存修订；`source_revision`单独记录冻结修订。改标签会变plan_key，但不会改变槽位ID或定位输入键；改N/来源改变定位输入键。改Fig归属改变计划映射，几何在同N/同源时可供后续核验复用。
- 输出路径只使用固定ASCII前缀及身份SHA256，采用POSIX相对路径；标签保留原样作为显示元数据。计划包含Fig目录/figure.tiff、行目录/raw-crop.tiff与display-crop.png。实际输出必须另由受限适配器选新根、检查路径/链接并无覆盖发布；计划本身不提供文件系统安全保证。
- `cells`以Fig/行/槽位ID对应预建表格，状态固定pending、value固定None；顺序按Fig/行/槽位展示，无默认sample ID、内参或零值。

返回对象及其内部序列不可变，来源模型也不可变。输入版本/确认/摘要错误抛ValueError。
dataclass只作为进程内派生值；禁止绕过构建器将手工实例直接当可执行快照。
后续阶段持久化、渲染和测量分别扩展版本化契约，不在本版本夹带结果。
