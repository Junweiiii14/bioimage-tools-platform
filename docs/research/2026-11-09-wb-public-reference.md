# 哪些公开 WB 材料能检验现有路线？

2026-11-09，P026。**用 IOCBIO 检查原值读入和自动定位的失败行为，用 Butler S2 检查稀释响应与指标设计。两者都不是现成的逐带准确率基准。** P010 的本软件历史输出、T013 的已调参私图和 T082 的解析样例不充当外部参考。B007 已登记 IOCBIO 和 Zenodo 22092552；本次只对前者打开归档，不重复下载后者或 GelGenie 凝胶集。

## 一张真实抗体膜：哪里走通、哪里停下

Kütt 等，[BMC Biology 2023，Validation、Methods、Additional file 1](https://doi.org/10.1186/s12915-023-01734-8)，[确定 ZIP](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs12915-023-01734-8/MediaObjects/12915_2023_1734_MOESM1_ESM.zip)。出版方说明文章/图片 CC BY 4.0、数据默认 CC0，除非另有注明。归档中央目录仅一层目录与九张 TIFF，无单独许可/表/ROI 文件，ZIP 注释为空；不再分发像素。三张物理膜，各有抗体检测 GAPDH、LTCC 和总蛋白 Ponceau（后者不是特异抗体信号）。九张图不等于九个独立实验。

仅选择 gel1_GAPDH_expo1min.tif 解码：ImageQuant LAS 4000，标签曝光 1 min；暗帧及仪器校正已启用。单页 3072×2048、单通道 uint16、MINISWHITE。公开 load_tiff 返回未转换像素，范围 941–30497，两端 0/65535 命中均为 0；未触数字上限不证明曝光或抗体响应在线性区间，也不证明这是未经设备处理的传感器读数。归档 SHA256 及固定成员见[复现脚本](../../work/evidence/P-026/probe.py)，成员 SHA256 为 af35f27d9171f1699a8247611dc48683833f03eae1ed30a1e795ad5966ab3a64。

Windows，产品源码基线 e846a68。运行 uv run --locked --no-sync python work/evidence/P-026/probe.py <本机ZIP路径>，exit 0。原值高为亮信号的探索假设，固定 13 槽、高 30 px、左 Marker、默认阈值，不据结果再调。13 是探针参数，并非作者确认该图的样本身份。公开 suggest_crops 的 membrane_periodic_profile_candidates@1 返回 membrane_not_found、0 个候选，故没有可报告的自动积分/归一化。退出成功仅表示探针完成；此结果只适用于这个公开入口和配置，不外推到所有工作流。首次临时脚本未关闭 TIFF 句柄导致清理失败；已用上下文管理修正并复跑。

作者图 3 有三人用 IOCBIO Gel 与 ImageJ Gels 的比较；Methods 指明各图/人/软件按该图泳道均值归一化。ZIP 没有能和原图 SHA、泳道、选区、端点相连的三个操作者数值表。IOCBIO 可复用之处是保存泳道、背景及积分设置并导出作外部对照（[作者软件与手册](https://iocbio.gitlab.io/gel/)）；其沿宽积分和可选曲线/背景，与本项目沿宽取均值再作端点基线梯形积分不同。不能套用论文相关系数，也不引入代码或模型。GelGenie 的普通电泳条带 mask 可对照分割，不能给出免疫靶标、上样身份或定量参考（[已核源码及差异](2026-10-17-source-only-geometry.md)）。

## 有独立数值的稀释实验：缺哪一半？

Butler 等，[Misleading Westerns，2019，附表 S2](https://doi.org/10.1155/2019/5214821)，[Europe PMC 附件](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC6360618/supplementaryFiles)。开放文章按 Creative Commons Attribution 授权，本文仅记录少量事实和摘要。实际读取 5214821.f3.xlsx（43052 bytes，SHA256 fdb4ed8f4139d35d7b6a3fdeb38bc8ca282e18634f3b011300c601231590c57f，内部 ZIP CRC 通过）；五张工作表对应图 1–5。在 Figure 1 Data 的 B3:E14，硝酸纤维素膜化学发光、三张膜、11 档总蛋白上样量。膜 1（C 列）从 20 到 40 µg 时，作者 O.D. 从 1108907 降到 926268.8。总上样量翻倍不能当作条带密度必须翻倍的验收条件。独立数值是作者测量，不是靶蛋白绝对浓度；同表红外块另列，有空格不能作零。作者提供的是代表图与 PDF 面板；在已查来源未证实原始灰度帧能逐膜、逐次曝光连回这张表。未拿论文图反推像素或计算本软件误差。新增开发表；不当盲测。

另一个排除例：上游同日读取 Clegg [源图 v2](https://zenodo.org/records/21109968)图 1 TIFF 首 IFD（HTTP 206 文件头）：13868×2777、RGB8、Illustrator 25.1；[定量 v1](https://zenodo.org/records/17596792)首表 Fig. 1C. 内标 Figure 1B，给三个条件、三次重复的 pRab10/Rab10 比值。即使说明写明 ChemiDoc MP 与 Fiji，首层仍不能证明线性原值；不推及其他 IFD、文件或版本。仅引用上游核验，不二次下载。

## 最短补齐路径

工程上，若要判定 IOCBIO 失败在哪个阶段，先给 gel1 一份独立标注的原坐标膜框及泳道序号，复用现有显式膜框入口，分别记录自动定位与给定膜框后的结果。该膜已见，不再作留出。定量上，优先找 **同一物理膜** 的线性采集 TIFF、曝光/稀释及膜—泳道映射、相同端点定义的独立测量导出；或由独立操作者按预定 ROI、背景和积分单位重新标注。先定可比量、饱和/缺失处理与容差，再开封另一批按膜/实验分组的留出；不把同膜的不同曝光分到两组。未取得这些证据前，不估独立准确率、不授予 S1、不改算法。
