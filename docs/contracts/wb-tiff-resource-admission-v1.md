# TIFF 读取资源准入 v1

策略标识 `tiff_resource_admission@1`，T082。只改变资源拒绝时机和解码并发，不改变图像科学方法、schema、位深、坐标、极性、BT.601 或导出像素。

## 入口与兼容

`load_tiff`（定量及后台预览）和 `load_ocr_tiff`（含显示拼图的OCR）共用读取适配器。仍须单页、左上原点、非空二维uint8/uint16；灰度MINISBLACK/MINISWHITE、RGB和不透明RGBA的contig/planar排列保持。方向、dtype、通道、体积/页数在像素解码前拒绝；透明度需读像素后判定，保持既有错误。

原值裁剪在初次公共验证、第二次原通道读取和写后核验使用同一准入。原文件读前/读后SHA检查、无覆盖发布和原通道导出保持。拒绝不缩放、不降位深、不产生有效零值；后台按既有失败回复排空，之后仍可处理正常小图。

旧项目JSON和已完成结果仍可读取，不迁移或重算。超过新资源预算的旧原图在再次处理时会明确失败；如需提高预算，应在目标机器验证后显式配置。所有入口采用同一配置，不能只放开预览而绕过定量检查。

## 默认值与配置

| 环境变量 | 默认 | 依据 |
| --- | --- | --- |
| `BIOIMAGE_TIFF_MAX_PIXELS` | 32,000,000 | 既有历史归档恢复支持上界及显示导出上界；不是从PNG压缩文件大小复制来的限制 |
| `BIOIMAGE_TIFF_MAX_PEAK_BYTES` | 2,147,483,648（2GiB） | `coding-standards.md`的16GB/单计算任务起点；本机CIM实际16,496,738,304字节，单图缓冲预算约物理内存的13%，为UI、OCR模型、其他任务和系统留余量 |

可在启动进程前设置十进制正整数（不超过有符号64位上限）；未设置使用默认值，空值/负数/非整数失败，不静默回退。策略每次读取时取值，子进程继承启动环境。像素和内存两个条件必须同时满足；32M像素不是所有编码/通道组合均可读的承诺。

默认值是此16GB基线上的保守工程政策，不是所有员工机器或实验采集规模的性能结论。R11记录目标机能力；若需要更大原图，应带实际格式/尺寸与内存测量另行调整配置，不能通过自动重采样绕过预算。

## 缓冲估算

设 `P=width*height`、`B=sample dtype字节`、`C=源通道数`。使用Python整数，不发生32位乘积溢出。解码前要求元数据shape/nbytes与 `P*C*B` 相符。

像素路径的估算为：

`P*C*B + P*(2*B + 7 + (RGB ? 24 : 0)) + 3*S + 3*G`

- 原始解码数组 `P*C*B`。
- 灰度/不可变bytes副本 `2*P*B`，饱和或alpha检查布尔数组 `P`，OCR uint16除法/uint8及不可变转换保守预留 `6*P`。
- RGB额外 `24*P`：uint32三通道工作副本及运算中间量；有些阶段互斥，仍相加以避免低估。MINISWHITE不反相。
- `S` 为单个最大解码块：tile采用完整padding后的width/length，strip采用图宽和`min(height, rowsperstrip)`；planar每块一个通道。三倍覆盖解码输出、临时工作和迭代时尚存的前块。拒绝非正块或3D tile。
- `G=min(sum(databytecounts), 16MiB + max(databytecounts))`。锁定tifffile读取分组可能超出名义buffer一个块，并同时保留连续读数据、切片列表及下一组；三倍预留。小文件不假定实际分配完整16MiB。

调用 `page.asarray(maxworkers=1, buffersize=16MiB)`，禁止默认多线程同时解码大块。巨大tile/strip或编码字节声明同样参与预算，不能只检查可见像素。

这是本读取路径可变图像/编码缓冲的保守估算，非进程RSS上限或操作系统隔离；Python/Qt/模型基线、TIFF元数据解析及第三方codec内部实现不是硬限制。受控异常由R01终态保护；系统终止/OOM killer不在必定回复承诺内。没有运行真实OOM实验。

## 验证与来源

`tools/wb/tests/test_tiff_admission.py`使用小数组和写入的异常头部，断言超限时asarray次数0，包含像素/内存阈值、uint8/16、灰度/RGB/RGBA/planar、压缩小文件大展开尺寸、巨大padding tile、通道/体积/页数及无效配置；真实后台验证拒绝后正常小预览和关闭。既有数值/原值裁剪/OCR回归保持。

官方实现：[tifffile](https://github.com/cgohlke/tifffile)。本轮核验锁定2026.9.20的`TiffPage.asarray/segments`和`FileHandle.read_segments`源码，确认maxworkers、buffersize及分组超限语义；不是凭当前在线最新版推断锁定版本。可重复核验：`uv run --locked --no-sync python -c "import inspect,tifffile; print(tifffile.__version__); print(inspect.getsource(tifffile.FileHandle.read_segments))"`。
