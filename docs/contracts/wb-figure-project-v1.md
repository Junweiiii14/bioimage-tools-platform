# WB 多原图与 Fig 项目 v1

wb-tool0.9.0，bioimage-app0.4.0。公开入口 WBFigureProject、FigureRow、FigureTemplate、plan_figure_layout、render_figure、export_figure_bundle。

## 文档与原图身份

这是独立的 `document_type=wb_figure_project/schema_version=1` 文档，平台 tool_id 为 wb-figure；不把旧单图文档改成多图。旧 WBDocument v1/WBWorksheetDocument v2 和 read_wb_document 保持兼容。共同 strict JSON 读取器改名为 DocumentIO，重复字段/未知字段/布尔修订/超16MiB仍拒绝。

每行独立 row_id、原图 AssetRef、原文件名、原始尺寸/位深、Fig、蛋白、N、empty_lanes、半开整行 ROI、reviewed 和备注。重复蛋白名不合并；重复导入按原文件 SHA 跳过。坐标必须在原图内且宽度至少 N。空泳道保留 fixed_count_integer_partition@1 的原位置。缺图行没有资产、尺寸或 ROI，显示叉线占位且不能定量。未复核行的 quantitative_lanes 同样拒绝，不把缺图/待确认转成零。

Fig 顺序是明确的完整无重复列表；组内行按 rows 顺序，可上移/下移。来源、几何、标签、N、备注的表格修改撤回该行审核；模板排版不修改源像素。同 Fig 必须 N 和裁剪宽度一致，所有裁剪高必须等于模板 crop_height。宽度不符时拒绝合成，不能通过隐式缩放修补。缺图 Fig 至少需要一张实际原图确定宽度。只给建议/未确认的草稿可预览，正式导出必须每行审核。

## 版式与显示

`figure_original_geometry@1`：模板保存标签左右位置、字体/字号、标签区宽、行高/间距、组间距、留白、边框、每排 Fig 数和 DPI。样例提供布局特征，默认数值是可编辑起点，不声称精确复刻实验室模板。组按指定顺序逐排放置，组内原图行等宽对齐，组间允许不同宽度。边框在裁剪之外，不覆盖条带像素。长文字超出留白会提示调整，不截断或压缩标签。

合成是 RGB8 显示派生图：`bt601_uint16_div257@1`，复用整数 BT.601；16位原灰度整除257，8位不重映射，无自动对比度、反相、平滑或几何重采样。MINISWHITE数值保持原样且记录警告。原图的彩色/16位样本保存在原图和原值裁剪中。显示合成不能作为原图定量替代品。本阶段项目界面没有合成像素定量入口。

最大输出3200万像素、单边32768；后台预览以最近邻缩至最大边2048，仅影响界面预览。DPI是输出标记，不改变像素尺寸。Pillow12.3.0内置拉丁字体为默认，非拉丁标签需显式导入字体；TTF/OTF/TTC最多32MiB，字体作为不可变工作区资产保存并核对摘要。模板随项目保存，可复用当前模板新建空项目。跨工作区独立模板库尚未实现。

## 保存、异步和输出

入口：原WB窗口的“多原图 / Fig 拼图项目”，或 `python -m bioimage_app --figure-project`。项目窗口使用自己的工作区连接；同一工作区仍受既有独占锁保护。批量导入、原图读取、字体摘要、编码、渲染/导出均在存储或WB后台线程；同一窗口一次操作，忙时冻结编辑。切换项目清空旧画布/选择，防止在旧原图上编辑新行。保存冻结项目并经CAS；关闭取消当前任务、保存已完成编辑，再等待两个线程真实退出。

导出新 ZIP：figure.png（内嵌 wb_provenance）、manifest.json、project.json、crops/0001.tif 等原值裁剪、assets/<SHA> 原图及自定义字体。manifest逐行保存 source SHA、原ROI、输出矩形、行身份、Fig/蛋白/N/空位、审核状态、对应crop_file、显示摘要/映射、原photometric和警告。跨源行用独立边框与间距分开。裁剪沿用 original_sample_crop@1，原颜色/位深/数值不变。归档原始资产逐个写入前后核对SHA。

同目录临时文件关闭/fsync后无覆盖发布（Windows rename，POSIX link）；取消检查到行、原图读写块和发布前，取消/失败清理临时输出，不覆盖已有文件。原工作区项目可重开；ZIP独立导入向导、直接TIFF成图、自动归档关联当前未实现。

本阶段未实现自动膜/Marker/行候选，也没有把多原图项目接入现有单图OCR/工作表与定量运行。它们属于后续完整产品必需项；不能把此手工多图流程视为自动化首版完成。
