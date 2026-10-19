# 仪器文件夹清单与分配 v1

T-051 新增 `WBIntakeProject/schema_version=10`，其 `IntakeManifest/schema_version=1`
保存 Fig、蛋白、原图池、明确分配及确认摘要。旧项目 schema1–9 的读取和独立灰度 OCR
保持原有语义；旧读取器明确拒绝10。此阶段不含自动检测、ROI、裁剪审核、拼图或定量，
不能把完成分配等同于已确认裁剪，也不会根据槽位数猜测空白的位置。

## 身份与信息

- `IntakeFigure(figure_id,label,lane_count)` 使用稳定身份；N 为1..96严格整数，含空位、
  不含 Marker。同 Fig 只共享数量，没有跨蛋白样本位置对应关系。
- `IntakeProtein(protein_id,figure_id,label)` 可同名；后续行 `row_id=protein_id`。
  Fig 显示名暂须忽略大小写后不重复，以兼容既有按标签分组的行式视图，标签不作为身份。
- `IntakeSource(source_id,asset,original_name,relative_path,width,height,bit_depth)`
  保存原文件名、安全相对路径和不可变资产引用。相同原名、相对路径或内容摘要都不充当
  唯一候选身份；不同候选可共用像素资产，未分配候选同样随项目保存与重开。
- `IntakeAssignment(protein_id,source_id,reuse_confirmed=False)` 是显式关联。相同内容
  用于多个蛋白须明确传 `allow_reuse=True`，相关关联记录 `reuse_confirmed=True`；
  不能通过新增同 SHA 别名或输入布尔标记绕过复用确认。

每种条目最多512项。Fig 和蛋白数组顺序是规划顺序，显示行按 Fig 分组后保留组内蛋白
顺序。无蛋白 Fig 暂存于清单，尚无来源的蛋白投影为缺图行，不产生伪造尺寸或零值。
`project_assets()` 包括整个候选池。未分配来源允许存在；确认要求至少一个 Fig、每个
Fig 至少一个蛋白且全部蛋白完成分配。

## 原子操作与保存

公开 API 全部由 `wb_tool.api` 导出：`create_intake`、`replace_intake_plan`、
`register_intake_source`、`assign_intake_sources`、`unassign_intake_sources`、
`confirm_intake`、`intake_digest`、`intake_snapshot` 及上述模型。

新入口只能从空项目创建。已有原图、裁剪、OCR 或运行结果不能静默转入此阶段；
保留原项目并另建仪器项目。所有后续操作要求当前 `expected_digest`，批量中任一无效
目标、重复目标或歧义均拒绝整批，不修改输入对象。`replace_intake_plan` 保留现有
source pool和同 ID关联；删除已分配蛋白前必须显式解除关联。重分配既有目标须传
`replace=True`。已注册 source ID 不可替换为其他内容。

摘要绑定项目身份和完整清单，排除修订号及确认字段本身；保存增加修订不撤销确认。
实际修改标签、N、顺序、来源或分配撤销确认。`confirm_intake` 只确认对应关系，
不设置 `FigureRow.reviewed`，不生成 ROI、定量请求或 OCR。
读取时验证清单、关联、确认摘要与行投影一致，禁止经旧表格绕过清单修改。

`intake_snapshot` 返回 JSON 可序列化的 snake_case 字段，含 `digest`、`confirmed`、
`project_id`、figures/proteins/sources/assignments；不包含缩略图或原始像素。
`FigureProjectView.thumbnail(sha)` 返回仅显示用途的128边缓存；重开可后台重载，
来源池更换会释放不再所属的缓存。新入口不得自动调用旧文件名标签推断、曝光变体筛选
或导入结束即检测/测量链。

本阶段不提供空项目成图/ZIP成品导出；已实现的通用资产枚举和恢复映射保留清单来源。
后续裁剪阶段须明确扩展格式和迁移路径，不能直接往此版本填入定量结果。
