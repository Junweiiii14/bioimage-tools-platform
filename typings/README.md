# 固定研究依赖的窄接口类型

这里只声明P015实际调用的TensorFlow2.21.0线程设置、csbdeep0.8.2 normalize和StarDist0.9.2模型接口。它们没有可执行实现，不替代真实模型测试；源码/安装版本在隔离研究环境核对。这样严格检查宿主和轻量工具时无需将约2GB研究依赖放入默认桌面环境。

Pyright保留三个`reportMissingModuleSource`警告，未设置ignore或降低严格模式；准确运行证据见P015。新增调用必须同步核验官方固定API及真实隔离进程。
