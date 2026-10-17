# 直接TIFF/PNG成图的位深与来源

日期2026-10-14；T-020。问题：用户方案9.4、10–11节要求直接图像输出、模板排版与原图定量关联，现有产品仅能在ZIP中取得PNG。直接TIFF应复用完整显示结果，同时避免混合位深/文字被误称为原值矩阵。

## 来源与本机实验

- [tifffile维护者资料与源码](https://github.com/cgohlke/tifffile)，访问2026-10-14；锁定并实际使用2026.9.20。本机TiffWriter.write参数说明确认description/software为ASCII，resolution按单位标记像素数，resolutionunit支持INCH。使用metadata=None以避免额外自动shape JSON替代来源描述。
- [Pillow PNG格式文档](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#png)，访问2026-10-14；实际12.3.0。PNG文本通过PngInfo保存，DPI按像素/米整数写入；读取值可能与目标有舍入差。仅新PNG标签检查采用0.013 dpi误差限，来源是每米整数舍入半步0.0127 dpi；不是对科学积分放宽容差。
- 最小实验：np.arange(18,dtype=uint8).reshape(2,3,3)，RGB/contig/未压缩TIFF、metadata=None、ASCII JSON、Software标记、300 dpi/INCH。402字节；tifffile读回2×3×3 uint8、像素完全相等、标签和(300,1)分辨率正确；Pillow读RGB/(300,300)，像素完全相等。

## 决定

采用同一render_figure结果，TIFF单页RGB8未压缩，PNG保持现有编码。16位沿用整除257、8位不重映射；RGB沿用整数BT.601灰度，原图不反相、不拉伸、不调对比度。DPI仅是显示输出元数据，不重采样。嵌入同一来源JSON与版本化Software=“bioimage-wb figure_display@1”。直接TIFF/PNG不替代完整项目ZIP。

不采用伪16位合成：把8位文字或不同来源拉到16位不能恢复原测量意义。原值TIFF裁剪和原图资产继续单独保留。定量load_tiff拒绝已知显示Software或来源记录，OCR专用分支允许读取；未知第三方图像或被剥掉来源标记的图不能自动判源，不以扩展名/_0/_1推断。

导出后台写入自有暂存文件，关闭/fsync后重读核对完整像素/通道/位深/DPI/来源，最后检查取消并无覆盖发布；不把预览缩略图当输出。预算沿完整渲染3200万像素/32768边长，PNG64MiB、TIFF128MiB、来源16MiB。新增原图和字体声明字节数核对，不改变既有正确资产的渲染。

## 实际资料格式检查

用户组合图00060322.tif只读包装为一个完整902×1347画面，N=1仅作测试容器，几何确认仅表示全幅范围，不建立实验泳道/定量真值。输出1577×988 TIFF/PNG，完整像素/来源相同，画面内灰度与原输入的既有显示映射逐像素相等，原SHA保持。已知显示TIFF被定量入口拒绝，真实本地OCR得到17 token（含包装文字），全部未确认/未绑定。4.07秒为整段格式/OCR探针耗时，非性能基准。私有文件与脚本留在忽略的.local，不提交原图。

## 限制与复核条件

独立审查、实际实验对应/准确率、外部排版软件兼容矩阵、大项目内存/FAT/断电/最终包态均未由本实验证明。Pillow/tifffile升级、显示映射或来源schema改变、增加压缩/其他TIFF模式时须重跑标签与精确像素验证。产品契约见../contracts/wb-direct-figure-image-v1.md。
