# T072 目标唯一性与方向的最小实验

问题：取消逐图确认必须有可核验依据；膜方向是否可以代替条带方向？旧source只返回一个最强候选是否表示唯一目标？结论均为否。

备选：直接接受旧候选，或使用同组白光角度，都会在独立合成反例中误采纳。采用两路径共享的原信号组件方向拟合和多目标/最终槽位交叉检查；弱证据暂停，不推断实验身份。

来源：既有source_geometry@2、export_detection、原像素积分契约；2026-10-21核验[SciPy map_coordinates](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.map_coordinates.html)及[Pillow Image.transform](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.transform)。锁定SciPy1.18.1、Pillow12.3.0；在线stable版本不能代替本地锁版本。重采样仅服务显示/检测，原始坐标TIFF用于积分。

复现：tools/wb/tests/test_instrument_geometry.py 与 test_intake_automatic_crop.py。300×700原值16位，五泳道x254/302/350/398/446，信号0/±3°、轮廓0/3/6/9°；原实现沿轮廓误转，修复沿信号。双排y144/156、多膜y100/290、显式上排但标准高度吞下排皆应暂停。独立预审先在guided发现四项，再在source发现两项，均保留为回归；不能用初稿通过数掩盖失败。

参数与版本见[自动裁图v2](../contracts/wb-intake-automatic-crop-v2.md)。残差/组件阈值和±10°是工程门槛，解析几何及本机数据回归不构成科学准确率。当前19组为已见参照辅助开发数据，修复后4组自动，15组依现有人工范围继续；无科学留出或生物配对推断。

显示版式兼容最小实验：先完成native Fig A，再给B添加方向框，A摘要/图像/分析不应变化。原全局切style会使A失效，改按Fig决定显示尺度；混合图、单独回存和输出裁图必须一致。test_standard_display中旧“native不支持frame”预期因此明确改为版本3局部支持，并新增完整输出、同Fig无框同行和原图不变断言；未更改数值容差或门禁。

重新核验触发：检测阈值、图像角色、预处理、像素坐标或显示策略变化；新增真实科学真值时独立评估，不能据开发集调整阈值后宣称留出。
