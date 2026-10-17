# WB 首个桌面闭环

范围：工作区/原始TIFF导入、显示画布的原像素ROI、条带闭区间与人工基线、原始剖面/结果状态、
后台计算与不可变结果、保存/重开/关闭。科学定义沿用 profile_integral@1 与 dtype_limits_review@1。
用户明确要求首版必须包含拼图Fig/行名OCR和结果表自动写入；本阶段不是完整首版退出。

预览在WB专用QObject线程读取；16位转8位只是显示DTO，最大边约2048采样点。
QImage从独立bytes建立且copy保持生命期；QPainter只画显示，不调用定量或写库。
来源：[Qt QImage](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QImage.html)，访问2026-10-14。
手工拖选将显示位置转换回原像素半开矩形；显示倍率与图像宽度不能改变积分定义。

WB owns view/background/document model；apps只通过wb_tool.api显式装配与储存通用资产。
WB v0.5.0新增tool-contracts（现有本地包）和可选Qt依赖，没有新增第三方版本。
根安装选择bioimage-app[wb]，独立core WB wheel仍不加载Qt；通用宿主wheel仍不加载WB/NumPy。
schema漂移、strict JSON/错误来源、实际Qt拖选→worker→保存重开及uint16原文件保持已测试。
QtBot鼠标转用Qt原生QTest，避免pytest-qt的未完整类型声明；未增加类型忽略或降低检查。

一个静态app入口处理desktop/--worker wb；编译后命令以自身可执行文件进入注册worker。
目前只测源码与已安装wheel，没有本阶段standalone/目标机验收证据。
合成图的widget抓图已人工查看，页面可读，曲线/边界/基线与状态表可见；不等于真实样本准确率。

## 收尾生命周期复查

一次最终pytest在首次GUI用例附近发生原生Aborted；诊断重跑191通过，23个Qt组合用例与20次
窗口开关/垃圾回收通过，没有捕获可独立重放的唯一根因，不用成功重跑抹去首次失败。
[Qt QThread文档](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html)指出 finished 与
isFinished 不保证线程本地析构结束，Windows/Linux需确认wait返回true。
关闭路径因此补零超时wait(0)探测，未完成则QTimer回事件循环重查，不阻塞GUI；
存储、解码、预览三个线程都确认后才报告关闭。新增注入延迟join反例验证closed不能提前发出。
最终192完整门禁及相关Qt6用例通过；偶发中止仍须后续稳定性/独审复核。
