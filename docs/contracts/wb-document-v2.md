# WB 工作表文档 v2 与 OCR worker v1

`WBWorksheetDocument`保存source、独立revision、polarity、可空AnalysisRequest、可选ocr_source、原始OCRRecognition、Worksheet与已提交测量副本。
没有泳道时request为空，可识别Fig/行名及保存；定量入口仍要求至少一个泳道，AnalysisRequest/定量worker v1不放宽。
读取器`read_wb_document`按schema_version分派。旧WBDocument v1/schema快照保持原样；未知字段、重复JSON、未知版本和超过16MiB文档拒绝。
测量须匹配当前来源/极性/标注（仅允许草稿revision因名称修改递增），并通过与worker结果相同的一致性校验；OCR的源摘要、引擎/模型/预处理版本须一致。

单独拼图通过ocr_source引用保存的不可变资产。量化始终读取source；跨图不能按坐标自动配对，用户为工作表单元格显式指定lane/band。
重开重新验证两个资产并读取保存的关联、名称和测量；保存新草稿不会覆盖已完成run结果。

OCR worker入口`python -m bioimage_app --worker wb_ocr`，采用独立OCRStartFrame/OCRResultFrame及原有hello/accepted/cancel/failure/cancelled信封。
请求与结果携带来源SHA、revision、run/attempt/request ID；帧上限4MiB，严格UTF-8 JSON，重复/乱序/过期/取消后结果拒绝。
宿主确认PID、进程树退出、结果事务后才宣告完成。OCR只返回候选，不写工作区；日志转stderr。

布局`fig_heading_tracks_leading_labels_nearest_row@2`接受Fig前缀或短编号，标题横向漂移容限为图宽10%；先选横向主标签列并保留同行并排标签。
这是空间建议，无蛋白词典或生物身份猜测；倾斜/侧边文字可能不进入建议行，但原OCR证据完整保存且可查看。名称/确认/关联可修改，也可增加或删除表格行。
更改名称会撤回该行确认；更改同Fig名称同步其行。改ROI/边界清除当前测量表值，名称修改不改变已测灰度。
待确认、未绑定、缺测、排除与真实零值不同。Windows导出用同目录rename无覆盖发布，POSIX用link；未进行真实FAT设备验收。
