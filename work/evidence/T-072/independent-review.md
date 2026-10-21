# T072 提交绑定独审

独立审查者为非作者 `/root/t072_commit_review`，只读审查及独立临时合成实验，未改产品、测试或安装窗口。源码base `975942de14120bdbc07e811f12bee053f3f90621`。

## 初审阻断（保留）

head `bc0a90ed3d08f286c7fd0f551b1f81723d823f49`，产品同 `2726673`。两项P1：旧source单一最强候选仍吞近邻双排；膜9°、信号水平仍自动显示8.994820°。一项P2：native项目给B加角度时全局style改变，使已完成A摘要失效、保存被拒。独立25测试4.25s/0仍不能代替反例，故阻断。

修复预审另发现mixed支持的两个显示裁图caller仍按全局style，回存会not enough image data；已一并修复并增加同Fig无框同行和完整输出测试。更早guided四项P1反例也保留在专用回归，不以初稿13/19采纳率掩盖。

## 最终复审 Accepted

精确head `44a342ede883f05365437779b97bf751e74eab0b`。原两P1/一P2与衍生caller问题均消除；未发现尚未解决P0/P1/P2。工作树干净。

独立命令：

```text
uv run --locked --no-sync pytest tools/wb/tests/test_intake_automatic_crop.py tools/wb/tests/test_instrument_geometry.py tools/wb/tests/test_standard_display.py tools/wb/tests/test_crop_return.py tools/wb/tests/test_intake_output.py -q
51 passed in 10.31s；退出码0
```

另独立重跑原几何反例：双排无候选/不可自动，9°膜上水平信号角度0。mixed回存同Fig带框/无框行360×96、其他native Fig48×20，全局style仍native；完成A摘要、分析和像素保持。旧native灰度仅在ROI/输出尺寸匹配时补平移矩阵，否则拒绝不可靠映射。mixed manifest、TIFF显示产物准入及来源矩阵静态核对未见新增问题。

覆盖产品差异的应用、领域、预览/Web UI和打包静态路径及上述独立实验。未跑Qt全套或安装包；完整门禁、CI/PR、实际安装另验。科学真值、干净Win10和物理DPI不在Accepted证明范围。后续产品变化须重新审查。
