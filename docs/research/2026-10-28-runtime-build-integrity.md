# Windows构建输入完整性

日期2026-10-28，范围T082/R06。问题是正式私有CPython构建入口未强制消费既有工具锁、第三方依赖导出丢弃哈希；不改变已交付产品的科学定义或发行身份。

采用固定来源工具/运行库基准、依赖分两段安装。uv官方[CLI说明](https://docs.astral.sh/uv/reference/cli/#uv-pip-install)说明require-hashes要求每项有哈希且为精确版本/URL；特定本地wheel可以有哈希，项目目录不能直接套用。工作区导出排除本地成员但保留它们的远程依赖，避免盲目删除no-hashes后原混合命令失效。四产品wheel随后用file-URI加哈希、no-deps/no-index安装，已有固定内置uv_build不引入新构建后端。

信任基准取自[uv0.13.0](https://github.com/astral-sh/uv/releases/tag/0.13.0)、[python-build-standalone20260825](https://github.com/astral-sh/python-build-standalone/releases/tag/20260825)、[winlibs15.2.0r6](https://github.com/brechtsanders/winlibs_mingw/releases/tag/15.2.0posix-13.0.0-msvcrt-r6)及[Inno6.7.3](https://github.com/jrsoftware/issrc/releases/tag/is-6_7_3)官方资产digest。下载/既存归档先对官方SHA，再取内部文件/树；Inno结合有效发布者签名、官方tag的[def02公钥](https://github.com/jrsoftware/issrc/blob/is-6_7_3/def02.ispublickey)和脚本文本对照。[官方下载页](https://jrsoftware.org/isdl.php)给出6.7.3资产及Pyrsys B.V.发行者说明。

详细摘要与版本、可复验小实验和失败记录见[T082来源证据](../../work/evidence/T-082/r06-provenance.md)及[工程验证](../../work/evidence/T-082/r06-build-integrity.md)。未选择自动下载后信任、单纯工具存在检查或当前文件hash自动入锁；旧T081临时preflight的观察值单独不足以建立信任。

限制：完整性与来源不等于上游供应链安全审计；没有执行新的正式产品构建/安装。升级工具、改变Python发行来源或活跃通道时重新核验，并通过独立diff审查。保留原有发行配置，本次无需按文件数量强行抽象。
