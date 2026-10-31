# TIFF 资源预算与解码并发

问题：R02要求在像素解码前拒绝过量资源，保留原值、RGB/planar兼容和OCR。元数据中的可见像素是否足够？tifffile如何解释buffer及并发？

来源：2026-10-28读取[官方tifffile](https://github.com/cgohlke/tifffile)与[项目发布元数据](https://pypi.org/project/tifffile/)，实际决策按仓库uv.lock固定2026.9.20（工件上传2026-09-21），以本地安装的`TiffPage.asarray/segments`、`FileHandle.read_segments`源码复核。不升级依赖。

最小实验：真实4×4 deflate TIFF（不足1KiB）只改头部尺寸65535²；把asarray替换为立即失败探针，旧代码进入探针，新代码直接ImageInputError且调用0。另一例可见4×4、tile头65536²同样在解码前拒绝。未申请头部宣称的大数组。uint8/16 × 灰度/RGB/RGBA/planar均用12像素图验证阈值和不可变像素，原文件SHA不变。

备选：只查像素不能覆盖巨型padding tile；直接套PNG的64MiB压缩文件限额不反映TIFF展开成本；默认tifffile多线程解码使同时存活块数不稳定。流式处理或独立OCR进程不属本项必要变更，暂不引入。

决定：采用`wb-tiff-resource-admission-v1.md`中的双预算及可配置政策，单解码worker、16MiB读取分组。核验源码发现read_segments按`while bytecount <= buffersize`累加，可能多一个块，而且保留连续缓冲及切片列表；因此估算不是简单max(buffer, largest strip)，而是三倍有界分组含迭代切换余量。RGB工作副本和表达式临时量、不可变副本/OCR转换都计入。

限制：每次读取估算，不是进程总RSS/原生codec的硬上限；本机约16GB，默认2GiB读取缓冲预算。代表性员工机器/超大实验采集规模仍在R11；不以本例证明科学正确率或所有TIFF变体都支持。系统终止不在R01终态保证范围。

重新核验触发：升级tifffile/imagecodecs/NumPy、增加格式或第三方预处理、改变并发、调整默认资源预算、出现实测峰值超估算。科学公式/历史schema无变化。详细红绿命令和结果见`work/evidence/T-082/r02-tiff-admission.md`。

## 独审反证与压缩补丁

2fdbcfe独审实际用64KiB展开流冒充4×4，Deflate/LZMA/PackBits均成功读出小图，证明只按元数据预算不足。锁定fallback忽略out且后续reshape截断，并非未知codec小额scratch。补丁前6个无大分配探针全红；修复覆盖所有三个实际可用通道，未引入原生imagecodecs。

核验来源：[Python3.12 zlib max_length](https://docs.python.org/3.12/library/zlib.html#zlib.Decompress.decompress)、[LZMADecompressor memlimit/max_length](https://docs.python.org/3.12/library/lzma.html#lzma.LZMADecompressor)，2026-10-28查阅，实际CPython3.12.14。本机fallback PackBits先扩展Python整数引用列表，因此估算额外保留12个段大小；LZMA字典显式限制并计入预算。合法拼接LZMA流累计校验，完整末条带padding和位顺序保留。

为避免预检与实际解码之间的文件变化，按块保留摘要，并仅包装当前TiffPage的公开decode回调核对实际字节，退出恢复，不换全局codec。原始整文件SHA保护不变。大于默认LZMA字典的合法输入可经目标机验证后设置专用环境限额，但仍受总预算约束。
