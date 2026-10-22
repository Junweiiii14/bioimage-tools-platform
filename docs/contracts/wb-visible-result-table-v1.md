# 可见结果表导出 v1（T077）

`intake_visible_table@1` 是仪器结果页的显示/导出投影，不改变定量、审核、归一化、项目 schema 或归档 `intake_table@1`。
`wb_tool.api.intake_visible_table` 接收清单及已核验的 ProjectTableCell，返回不可变 IntakeVisibleTable。

- 行沿清单 proteins 顺序（稳定 ID，同名蛋白不合并）；列为 Fig、蛋白、泳道 1..最大 N、状态，与结果页共用投影。
- 只取已提交且通过来源/请求/run/资产核验的 raw_integral。人工 reviewed 不是导出前置条件；原始积分不提升为归一化有效值。
- 缺失、失败、取消、旧输入或坏证据保留缺项，显示/导出为“—”；真实 0 保留数值。非 valid 且有原始积分时保留质量星号。
- XLSX 保留数字类型/精度、数值显示格式、质量星号格式、表头强调、右对齐、固定表头/身份列及列宽；状态/来源保留在第二表。界面主题不写入科研数据。
- CSV 按相同行列输出两位以内小数的可见文字、质量星号、状态及缺项。沿用 `wb_csv_text_prefix@1`、UTF-8 BOM；去掉恰好一个 `text:` 可还原文字。CSV 不表达颜色、字体或冻结窗格。
- 从最新保存后重新核验的运行证据导出，保留200000单元格/64MiB预算、取消、代际保护、无覆盖发布与旧归档字节核验。
- 最终结果项目保存后重建结果展示，再执行后续导出；不得只重置显示为待算。旧清单规划阶段保持原保存行为。

## 工具入口目录拖入

默认入口 WebWorkbenchWindow 工具平台首页，仅 WB 已安装。原生 QWebEngineView 接收 Explorer URL MIME，DOM 命中 WB 入口后连接既有 `start_from_images(... intake=True)`，不新增其他工具语义。

1–32个本机目录整批处理；普通文件、失效目录或远端URL使整批失败，相同路径去重。后台 ProjectSelectionJob 核验目录，复用 TIFF 扫描/解码、来源根、512图/4096目录预算与新项目分配；无可用 TIFF 不创建项目。多个根共建现有原图池，不自动配置实验身份。
始终返回 CopyAction，不请求移走输入。已有项目复用保存/取消/草稿保护，忙态拒绝并反馈。异步 DOM 回复绑定当前宿主/会话，项目切换后不接受旧拖入。

Qt6.12 API核验（2026-10-23）：[QWebEngineView](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineWidgets/QWebEngineView.html)、[QDropEvent](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QDropEvent.html)。本机 WebEngine/Qt URL事件及焦点子控件、真实后台存储/worker和文件验证见 T077；合成事件不等于物理 Explorer 鼠标或干净机/DPI验收。
