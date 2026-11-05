# 最小实验预声明

2026-11-05，在下载和读取任何 BBBC039 图像/标注之前固定。本实验不是产品科学准入，也不估算学生需求。

- 数据：BBBC039v1，官方 CC0；原图/人工标注/官方划分分别来自 https://data.broadinstitute.org/bbbc/BBBC039/ 的 images.zip、masks.zip、metadata.zip。原始归档保存到仓库外 p013-research-data，不提交。
- 使用官方 validation 列表按文件名排序前 3 张做读取和实现核对，test 排序前 12 张作留出；不用 train，不调整参数追逐测试结果。小样本、同一高通量实验，不代表跨实验或全数据集表现。
- 方法 v1：原生 uint16 转 float64；Gaussian sigma=1 px；全局 Otsu；去除面积小于 30 px 的前景；填洞。基线为 8 连通域；候选为 EDT 距离峰（min_distance=8 px、exclude_border=False）作为种子的负距离 watershed。无尺度时所有尺寸仅为像素，不解释为细胞直径。
- 原始强度按各预测区域的原生 uint16 计算 float64 均值/积分，单位 ADU，不扣背景、不转 RGB8；这是计算演示，没有独立强度真值，也不能称 IF 蛋白表达。
- 标注解码依官方说明，取 PNG 第一通道，按相同值的 8 连通区域生成实例标签（背景 0）。不把全部非零颜色合并后标记。执行时记录实际颜色与对象数量；与官方示例语义不一致则停下诊断。
- 指标：逐图 GT/预测核数、绝对计数误差及相对误差；实例 IoU > 0.5 一对一匹配，汇总 TP/FP/FN、micro F1。以严格大于避免半面积平局，同一对象不能重复匹配。无 GT 时相对误差为 null。记录分割耗时（不含导入/下载/评价）和运行平台/依赖；不是产品性能预算。
- 原始数据质量仅记录 dtype/shape/饱和像素，边界对象不排除；空图/错误不改成通过。输出逐图 CSV、原始强度表、环境/方法/文件摘要 JSON；重复运行核对非时间数据一致。保留失败图及两个方法差异，不根据结果改判据。
- 探针验收：12 张留出可读、评价完成、数据不覆写、重复运行数值一致；准确率不设虚构临床/实验室合格线。若误差明显，则明确方法不足并建议下一轮针对性研究，不能以运行成功推荐正式定量。
- 仅隔离研究环境使用 scikit-image 0.26.0（Python >=3.11，BSD-3-Clause 总许可，thresholding BSD-2-Clause）；核验于官方 PyPI 和 v0.26.0 LICENSE.txt。固定全部实际安装版本，正式 pyproject/uv.lock 不变。

方法来源：https://scikit-image.org/docs/0.26.x/auto_examples/segmentation/plot_watershed.html；标注解码说明：https://gist.github.com/jccaicedo/15e811722fca51e3ae90e8b43057f075 。独立编写探针，不复制未声明许可的 gist 代码。

执行前后差异：首次下载检查误读 __MACOSX 资源分叉的 txt（UnicodeDecodeError，退出1），改为明确读取官方 metadata 路径；没有改变划分。首轮探针在第一张 validation 图上因假设 RGB 三通道断言失败（退出1，尚未评价 test）。实际为 RGBA，alpha 恒255；修正输入断言允许不透明 RGBA，仍只取红通道按原声明解码，方法/参数/样本/指标均未改变。该版本化文档路径访问失败，使用官方 stable 例页（页头显示0.26.0）；可执行依赖仍固定0.26.0。
