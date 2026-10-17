# Fig OCR / 自动写表的本地引擎与语义

用户要求首版必须拼图Fig/行名OCR和结果表自动写入；当前T-009后端子阶段，不是完整功能交付。
旧worksheet.py/ocr_jobs.py/table_export.py只读核对，来源摘要见work/evidence/T-009/reference-source.json。
旧版本3.9.2使用PP-OCRv6小模型，按标题/标签空间位置建议分组，复核后关联结果；不把OCR灰度拿去定量。

选[RapidOCR 3.9.2](https://pypi.org/project/rapidocr/3.9.2/)（2026-07-21，Apache-2.0），
与旧包一致，wheel包含三个模型，无需首次运行下载。所有模型加载前校验SHA256；缺失/损坏失败，
不让引擎自动下载补齐。[ONNX Runtime 1.31.0](https://pypi.org/project/onnxruntime/1.31.0/)固定CPU执行，
intra/inter线程各1；OpenCV5.0.0.93实测与NumPy2.5.4兼容。Windows内置OCR要求特定包身份/语言资源，
不作为当前便携交付路径；旧rapidocr-onnxruntime1.4.4只做安装比较，未作为产品依赖或降低模型版本。
读取/操作日期2026-10-14；新11项依赖由uv.lock固定，现有依赖没有升级。独立依赖diff审查仍待执行。

OCR以原TIFF快照生成专用8位输入，16位除257只发生在识别适配中；2048分块/256重叠/最多64块，
坐标平移回原像素，重叠同文字去重；块间与返回前可取消。ID为ocr_u16_div257_tiles2048_overlap256@1。
Fig标题显式匹配，行名原文不按蛋白词典改写；标题轨道/纵向分段与最近行建议关联，
歧义/多条带竞争不自动选一个；layout_id=fig_heading_tracks_nearest_row@1。名称和关系仍须复核确认。
来源不同的OCR图/测量图不按行序自动匹配，后续UI须提供显式跨图关系；默认输出 unconfirmed/unbound。

fill_worksheet只用有效signal写明确lane/band身份对应的单元格。失败/排除/未关联与真实零分开，
结果来源SHA须一致。两Fig四行、每Fig两个泳道的真实OCR+矩形解析面积测试，
填入3045/1995（对比145/95×21像素），没有额外乘宽度。socket连接被拒绝时实际识别仍通过。

软件内嵌XLSX导出遵循[SpreadsheetML结构](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-sheets)
和[inlineStr](https://learn.microsoft.com/en-us/dotnet/api/documentformat.openxml.spreadsheet.cellvalues?view=openxml-3.0.1)。
名称永远为字面文字，数值单独类型，空值留空；两表为WB结果/状态与来源，保留版本/单位/原因。
完整内存ZIP生成→临时文件/fsync→硬链接原子无覆盖发布；目前要求支持硬链接的输出文件系统，
FAT等需后续明确交付路径，不静默回退为可能覆盖的写入。已有目标、非法目录链接明确拒绝。
XML与ZIP反例、独立bundled openpyxl3.1.5读取值/Unicode标题通过；不把读取库引入产品写入依赖。

待做：OCR专用worker/取消与Qt复核表、文档v2与v1兼容、跨图拼图关联/显式编辑、GUI自动写入/导出。
真实样本标注/识别准确率与最终包态未验收，不能从六个合成标签外推通用准确率。
