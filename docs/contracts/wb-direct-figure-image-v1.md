# 直接拼图TIFF/PNG v1

直接成图复用figure_original_geometry@1与bt601_uint16_div257@1：RGB uint8、左上原点、原裁剪几何、固定N和缺图占位、模板文字/边框/间距与完整PNG一致。原16位灰度整除257，8位不重映射，RGB沿已知整数BT.601；不做自动反相/对比度/平滑/缩放。DPI仅写输出标记，不重采样。全部行须已审核；项目schema1–6、原值裁剪和科学积分/归一化不变。

export_figure_image(project,sources,destination,cancelled=...)接受新.png/.tif/.tiff。PNG保存同一wb_provenance文本和DPI，仍64MiB文件预算；TIFF为单页RGB8、未压缩、contig、标准TIFF，ImageDescription保存同一ASCII JSON来源，Software=bioimage-wb figure_display@1，X/YResolution与ResolutionUnit=INCH保存DPI。完整图最多3200万像素/32768边长，TIFF文件128MiB、嵌入来源16MiB。TIFF不打包原图或运行资产；需要可恢复的完整项目使用ZIP。

量化输入load_tiff新增已知显示派生TIFF拒绝：Software标记或ImageDescription明确声明figure_original_geometry@1/display_only_not_quantitative时提示改用原图。OCR使用专用TIFF读取分支，保留同一像素/预处理身份并显示用途提示。该保护不判断未知第三方图片的来源；外部工具去掉来源标记后不能自动识别。不能按扩展名、_0/_1或位深推断仪器图身份。PNG继续仅用于OCR/显示。

写入前验证原图/字体摘要、声明字节数/尺寸/位深，使用生成的同目录临时文件；后台完成渲染/写入后关闭、fsync，再次核对实际像素/模式/DPI/来源文本，然后检查取消并无覆盖发布（Windows rename/POSIX link）。既有目标、坏源、未审核、超限、取消或写入/校验失败均不发布新文件，清理自有临时输出。发布先于取消时保留完成文件，不覆盖源图。

桌面单独“导出拼图 TIFF / PNG”，完整项目ZIP入口保持。精确保存修订后在WB后台工作，忙时禁止编辑；后到编辑/关闭/取消撤销待发布输出。来源文档仅作证据，不执行或自动替换当前项目。导出TIFF可从既有拼图OCR入口导入，再走真实worker、人工校正和明确关联；不自动确认蛋白对应。

T-041增加显式实验室标准显示策略，采用figure_segmented_geometry@2及standard_lane_ratio@1；RGB8显示映射之后可按泳道宽/行高使用Pillow LANCZOS重采样，manifest明确原ROI与输出框、尺寸及输出RGB摘要。旧原生策略保持无缩放；标准显示TIFF仍被load_tiff拒绝，原值裁剪/定量不变。参数和预算见wb-laboratory-layout-v1.md。
