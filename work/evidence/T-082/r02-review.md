# R02 独立复核

2026-10-28，非作者，基线c55a157→2fdbcfe4ffd3e0575b42ac2e7781ecd1c67fdfae：**Request changes**。独立受影响65项通过，但发现P2压缩流实际展开可绕过元数据预算。

锁定tifffile._imagecodecs的Deflate/LZMA/PackBits忽略out，上层reshape截断多余数据。独立受控实验均64KiB：声明4×4，Deflate/LZMA预算1024字节、PackBits预算4096字节，实际展开65536字节但返回成功。不是可以忽略的原生scratch误差。LZW在当前环境缺依赖、ZSTD为当前Python不可运行的stub，未虚称复现。

作者已补三个通道的有界预检、LZMA字典内存与摘要保护，新增6个旧码必失败探针；压缩补丁准确提交需要再次独审，此记录不提前Accepted。原R02证据与失败保留，未改科学/历史定义。

## 补丁独审

159a51ec5c86155b9567b9e3e750ba9711ba81a9（补丁基线2fdbcfe，累计c55a157）：**Accepted，限定R02**。原P2已闭合，无新增阻断。非作者独立67项4.26s/exit0；额外实测精确尺寸、拼接第二流超限、真实BytesIO字节变化、文件位置恢复、uint16多条带、两个页面嵌套读取、RuntimeError/KeyboardInterrupt传播及回调恢复全部通过；全局codec身份保持。原像素/科学/历史schema/导出语义无变化。

独审未改文件、未跑全门禁/真实OOM；不代表总RSS硬限、全部TIFF变体或目标机验收。末次核对只有R04 JS dirty，受审R02文件未变化。
