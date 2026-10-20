# T-042 原图几何调研与实验

访问日期2026-10-17；问题：短膜被裁高门槛拒绝、倾斜被投影截断、首样本被Marker规则删除、单阈值丢弱泳道。研究使用8源图；参考图只在输出冻结后评分。本集合已用于诊断，属于回归集。

## 社区对照

| 原始来源 | 可借鉴能力 | 适用限制与决定 |
|---|---|---|
| [ImageJ Gel Analyzer](https://imagej.net/ij/docs/menus/analyze.html) | 泳道剖面与手工背景封底 | 依赖用户矩形/峰区域，不能直接解决本任务自动膜/Marker；保留为边界语义对照 |
| [GelJ维护者功能说明](https://sourceforge.net/p/gelj/wiki/List%20of%20features/) | 全局与逐泳道阈值 | 功能说明不证明本数据表现；借鉴局部阈值对弱带的支持，未复制代码/安装 |
| [GelGenie源码](https://github.com/mattaq31/GelGenie)、[论文](https://www.nature.com/articles/s41467-025-59189-0) | U-Net逐band分割、标注复核 | 可作为以后困难背景候选；加入模型/推理栈前需独立盲集证据；不能把凝胶论文结果外推为本WB正确率 |
| [GelGenie操作契约](https://github.com/mattaq31/GelGenie/blob/23fae2fb6ab2ade7149f4e7a76248dba7d9d23a9/qupath-gelgenie/README.md) | 检测归一化与定量分离、人工编辑 | 自动编号要求方向合适；体积求和不同于当前均值profile梯形公式，不替换现有定量 |
| [scikit-image Hough官方示例](https://scikit-image.org/docs/stable/auto_examples/edges/plot_line_hough_transform.html) | 多条直线方向证据 | 可比对上下边角度；当前已有明确单膜轮廓，先用稳健边线拟合，避免增加依赖 |
| [SciPy map_coordinates](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.map_coordinates.html) | 输出网格到输入坐标采样 | 仅检测副本；有效像素mask独立采样，原像素ROI测量 |
| [SciPy find_peaks](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html) | prominence/距离等局部峰证据 | 单一距离会漏弱峰或把宽峰边缘当多个band，不能单独决定N |

GitHub只读API核验GelGenie：main SHA23fae2fb6ab2ade7149f4e7a76248dba7d9d23a9，license Apache-2.0，pushed_at2025-07-13T17:19:50Z。网页LICENSE抓取超时，许可证标识来自GitHub元数据，未声称逐文件许可完成。仅研究，不引入其代码或模型。现有NumPy2.5.4/SciPy1.18.1/tifffile锁定不变。

## 最小实验与选择

本地`.local/t042/probe.py`只读旧首轮清单的源路径，未读参考几何。膜参数crop_height=2探针可重现8块膜；扩大局部边界后取连通轮廓，稳健拟合上下长边、检测副本逆映射拉正。检测中使用局部亮背景减原像素；目标行横向活动定位。

单一find_peaks对强弱交替、宽带内部双峰、接近饱和的平台均不稳定；增加平滑丢弱峰，降低prominence产生假峰，不能仅改一个阈值解决。改为全局/局部多阈值片段，按宽度过滤、中心聚类、跨阈值支持。一次原图探针形成8图的9/9/5/5/9/9/5/5个稳定中心（均含左Marker），另一个单阈值支持的噪点被过滤。第一中心纵向有2个独立峰，后续样本以目标行单峰为主；这提供去倾角后的Marker多行证据。

采用显式新策略source_geometry@2，旧策略可读取/重放；新增逐lane原图矩形和显示旋转框。确认不确定膜/方向/条带时返回失败/复核，不自动全图晋级。每次阶段记录候选中心、支持度、角度与失败理由；后续正式代码和8图评分才是修复证据，探针不算验收。

## 尚待验证

同一张图多目标行的身份不一定可由像素确定；白背景/多膜/折弯/缺失端部/不同仪器要另测。阈值集、角度一致性、ROI映射和旧项目读取需合成性质/回归/工作台端到端验证。8图不用于宣称泛化成功率。积分背景研究在裁图证据完成后开展。


## 积分背景支持实验

ImageJ Gel Analyzer 的封闭峰面积依赖背景线，不等于局部谷点之间面积。SciPy维护者的 [peak_widths](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.peak_widths.html) 按 prominence 相对高度求宽，不能直接证明端点属于背景；[issue 16350](https://github.com/scipy/scipy/issues/16350)也讨论平台与周围背景的区别。因此不修改冻结WBQuant源码；新增background_support@1，对原始均值剖面的检测副本平滑，要求连续背景支持，再以原始profile_integral@1积分。2.5%幅度/3倍二阶差分噪声门槛和3–10点支持是版本化工程策略，不是文献保证。峰内浅谷不再截断；多独立信号、背景不足保留诊断面积并标记quality_review，不进入有效信号/比值。显示插值仍不进入数值。

合成独立矩形面积、内部缺口、斜背景、双峰、平坦、截断宽峰测试均有明确预期。真实48泳道使用同一新几何，分别运行旧WBQuant和新策略，结果冻结在.local/t042/boundary-comparison.json。新策略21/48缺少充分背景支持；另外保留位深端点警示，总计7 valid、41 quality_review。不能将48个数值或数值增加当正确率。缺少独立逐lane背景真值，真实积分准确率尚不能给出；必须在工作台扩大/调整ROI及显式背景复核后才能报告有效测量。


兼容性补测：既有裁好的均匀背景场没有膜外轮廓，不能因此让旧工作台支持的输入全部失效。只有周界近均匀、声明极性存在显著稀疏信号（占比0.5%–35%）时采用明确的pre-cropped field路径，并记录没有轮廓方向证据；非均匀/多膜/空白仍拒绝。深色和浅色合成场、既有网页重开测试通过。此扩展不是任意无膜图全图回退，也未改变8真实图的膜分支。
