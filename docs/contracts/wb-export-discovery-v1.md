# 仪器导出识别与集中复核 v1

T061：算法/报告 `export_signal_regions@1`，`ExportDiscovery.schema_version=1`；嵌入 `IntakeManifest.schema_version=2`，顶层项目沿用10–14阶段。旧清单v1的序列化字段和摘要输入不变；旧读取器拒绝清单v2，不能宣称向旧程序兼容。新读取器保留旧清单和各阶段语义。没有迁移或覆盖原图/历史结果。

## 公开边界

`wb_tool.api`导出 `discover_exports(project, sources, cancelled=...)`、`ExportDiscovery/ExportObservation/SignalRegion/ExportSelection`、`install_export_discovery(..., expected_digest=...)`与`accept_export_selections(..., expected_digest=...)`。识别器只读摘要匹配的资产，纯图像检测留在domain，路径和分组留在adapters。宿主通过已有后台WBJob执行识别，不在GUI线程解码大图。

观察绑定source_id/SHA/group_id，记录角色、原因、原坐标候选、N候选、角度和错误；无测量值/可信百分比。编号后缀不决定角色，三联图仅为同一采集组候选；横条成品仅标参考待验。RGB按已有TIFF输入契约转换并记录，不伪装16位灰度。白光辅助需要同组三联/等尺寸，轮廓和信号共同生成候选；这不构成坐标配准真值，必须在信号原图审核，重采样检测数组绝不定量。

## 确认和失效

识别报告写入v2清单，清单确认撤销；不会自动分配、填N、确认ROI或产生结果。集中建立只接受空清单，用户逐组勾选来源并填写Fig/蛋白/N；目标可选择候选或留待原图框选。同Fig的N必须一致，稳定ID不使用显示位置。报告中的错误/成品参考不作为集中分配原图。

已选候选仅作为后续固定N裁剪建议，仍未reviewed；N改变后不复用旧选择。用户原图框选通过既有review_intake_crop与事务阶段完成后，才发布原值裁剪。保持独立灰度/OCR及所有现有人工入口。失败/取消或旧会话回复不能安装报告，保存采用现有CAS及generation/session检查。

## 本地案例与评估

`python -m wb_tool.discovery --root DIR [--root DIR] --output NEW_DIR`生成本地图册/JSON/项目草稿；可选`--baseline`仅首次记录旧算法基线。只创建新目录，禁止写在输入目录下。私有原图、缩略图及绝对路径报告不提交Git。

按完整采集组与同标签参考冻结前瞻划分，精确重复内容并组，三联图不跨集合。当前用户明确N/目标未知、参考部分可靠；全部标记unverified，准确率为null。当前图册展示所有数据，不能再声称该批是盲测留出；若未来调整使用留出，应转开发证据另补独立样本。本轮没有监督训练标签，不训练或新增模型依赖。

## 必要验证

新增4个核心参数化/保护/RGB用例、1个Web集中确认与回执草稿用例、1个真实后台/存储重开用例；复用现有主链完整测试。开发仅针对失败修复和受影响路径复验，最终一次完整门禁；保留必需CI。未新增压力/极端组合、不削弱已有检查。
