# 固定网格与原像素裁剪 v1

`fixed_count_integer_partition@1`：输入原图半开矩形、已知N（1–96）和左右排除像素宽度。剩余宽度W至少N，边界为left+floor(i*W/N)，覆盖全部剩余列、不重叠，宽度最多差1像素。无强度阈值，不按亮度删除或合并空泳道。Marker排除宽度由用户给出，此阶段不自动识别膜/Marker。

Qt选择固定网格后拖框，追加N个可独立编辑泳道；单框模式可框整行条带。新图导入默认不重建已存坐标。生成坐标/稳定身份保存到已有v2 request，网格数量/排除值是下一次绘制参数，不是覆盖旧ROI的参数。当前不保存完整生成参数或自动建议历史；后续自动候选需独立版本化快照。

`export_crop(source, CropRequest, destination)`只导出所选矩形。后台从工作区原图资产解码，原SHA/修订/半开ROI冻结在请求中；先复用单页TIFF校验，再读取原样本（不使用灰度转换或预览数组），读取前后校验原文件SHA。8/16位、RGB/不透明RGBA、MINISWHITE和planar RGB适用；输出planar规范化为YXC连续通道，不改变样本值。没有旋转/平滑/缩放/对比度/反相。

新TIFF保留样本位深、photometric、alpha定义和XY resolution/unit；不复制仪器私有元数据或注释，不能视为仪器原始文件的完整备份。ImageDescription存ASCII JSON：schema_version1、operation `original_sample_crop@1`、source_sha256、source_revision、source_shape_yxc、roi（含lane_id）、coordinate_system、shape、dtype、pixel_sha256、photometric和空transforms。pixel_sha256是按记录dtype、C顺序的样本字节摘要，不是TIFF文件摘要。

先写唯一临时文件并fsync，再无覆盖发布：Windows rename、POSIX link；已有文件/别名拒绝，不覆盖源和历史结果。错误不生成目标文件，临时文件清理。未做物理FAT验收。裁剪是派生资产，不自动替换定量来源；蛋白/样本身份不从强度推断。

此阶段为手动复核裁剪与固定网格；自动候选、整行多图组织/模板合成和批处理待实现。ROI/条带积分定义与文档v1/v2未变化，不引入第三方依赖升级。
