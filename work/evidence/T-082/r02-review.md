# R02 独立复核

2026-10-28，非作者，基线c55a157→2fdbcfe4ffd3e0575b42ac2e7781ecd1c67fdfae：**Request changes**。独立受影响65项通过，但发现P2压缩流实际展开可绕过元数据预算。

锁定tifffile._imagecodecs的Deflate/LZMA/PackBits忽略out，上层reshape截断多余数据。独立受控实验均64KiB：声明4×4，Deflate/LZMA预算1024字节、PackBits预算4096字节，实际展开65536字节但返回成功。不是可以忽略的原生scratch误差。LZW在当前环境缺依赖、ZSTD为当前Python不可运行的stub，未虚称复现。

作者已补三个通道的有界预检、LZMA字典内存与摘要保护，新增6个旧码必失败探针；压缩补丁准确提交需要再次独审，此记录不提前Accepted。原R02证据与失败保留，未改科学/历史定义。
