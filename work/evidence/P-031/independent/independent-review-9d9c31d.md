# P031 固定独审

**通过（pass），绑定最终候选 `9d9c31dd4457f0e175c627c6a9c230e3effe4c62`。** 基线 `3b8de00eaa14901ababf129f5a110e1b0a8e7a8c`，研究内容 `bef2475d959067535457c793ab8e3ae438bfc8e3`。研究与方法复验在初次派审的 `e50e740dffa044391260270824a57163de620113` 独立 detached 工作目录完成。初次候选的规则检查 exit 1，R01 的触发条件是 P030/P031 两份规则回执同时出现却缺少历史来源映射。新候选唯一增量是集成清单，准确规则检查 exit 0；研究报告、程序、图及数值证据逐字节相同，R01 已关闭。2026-11-09，Windows。[PR82](https://github.com/Junweiiii14/bioimage-tools-platform/pull/82) · [两个提交的治理回执](governance/p031-governance-9d9c31d.json)

**资料配对。** 以 Zenodo 固定记录 4593510 核整包 478,985,743 字节，发布方 MD5 `1d45b5a3bd7c50c80e628ab4cb664445`，独立 SHA256 `c47abdf9004e19e1de1b1634ba07bbbfa423329444c38855adf4c5a07347ea3f`。归档 16 个 TIFF 均有同名的 GT 和 3 个扫描图观察者坐标文件。自然排序前三个符合条件的 ID 正是 T47D-0412-C1/C2/C3。0412 可确认为共同 ID 前缀；同一生物批次及重复设计不能只据文件名确定。发布者以 >50 个细胞定义可计克隆，三位受训观察者互不知对方结果，另有一位独立观察者建立显微 GT。坐标两列按 x,y 表示每个标记克隆的位置，未标区域缺少逐对象阴性裁定和像素边界。16 张扫描图的逐瓶处理、接种数和配对对照均未由这些点文件给出。[归档与许可回执](source/receipt.json) · [Zenodo 数据说明](https://zenodo.org/records/4593510) · [Arous 等原论文](https://doi.org/10.1080/21681163.2022.2035822)

**原实现。** SoftCount 1.0.2 的实际 CLI、I/O 和引擎源码与固定上游提交 `4c4c3de0521dda51f4bc0cd466bc4ded1003488c` 一致。三个原始 TIFF 都是 2125×2985、每通道 16 位 RGB；实际给引擎的 RGB 为 uint8。直接核对 TIFF 条带，本组三图的每个通道均保留了高 8 位。默认全图 CLI 未调参。还核对了灰度、CLAHE、阈值并集、开运算/膨胀/闭运算及对外轮廓的严格面积门槛 525 < A < 15000 px²。独立运行 CLI exit 0，CSV 全字段匹配；独立重算分割末级 mask 与原引擎逐像素一致。固定上游源码及产品依赖无改动。[方法运行回执](method/run-1/receipt.json) · [SoftCount 源码](https://github.com/Nima-Sarfaraz/SoftCount/tree/4c4c3de0521dda51f4bc0cd466bc4ded1003488c)

| 培养瓶 | 显微 GT | 扫描图观察者 | 自动计数 | 自动减显微 GT | 接纳的轮廓中含 0 / 1 / 2 个 GT 点 |
|---|---:|---|---:|---:|---:|
| C1 | 37 | 40 / 37 / 33 | 28 | −9 | 6 / 19 / 3 |
| C2 | 48 | 48 / 50 / 46 | 30 | −18 | 2 / 27 / 1 |
| C3 | 45 | 48 / 44 / 44 | 34 | −11 | 3 / 31 / 0 |

**计数差异的含义。** 三瓶净偏差的绝对值均大于该瓶三位观察者计数的极差（7、4、4）。C1 的 240 px² 轮廓含一个指定 GT 点而低于下限；另一个外接框覆盖画幅的 829351 px² 轮廓含三个 GT 点而高于上限。C2 的两个指定点位于同一 2562.5 px² 获计轮廓内，距外轮廓边界约 16.9 和 13.0 px，原坐标零基/一基的不确定性不影响此例。在阈值并集阶段已同处一条外轮廓，无法单指后续某次膨胀或生物学融合。C2 有 19 个 GT 点在所有获计外轮廓之外，另有 2 个获计轮廓内无 GT 点；18 是相对显微参考的**净计数差**。这些空间对应关系不足以将无点轮廓全部判为假阳性。报告插图与所述原尺寸叠图区域的最近邻放大逐像素一致，绿圈表示算法的计数标记。[独立点与轮廓复算](independent/counts-and-sf.json) · [冻结研究报告](https://github.com/Junweiiii14/bioimage-tools-platform/blob/bef2475d959067535457c793ab8e3ae438bfc8e3/docs/research/2026-11-09-clonogenic-count.md)

**独立协议算例。** Rafehi 表 1 的 Manual (digital image) 对照及 4 Gy 两行均为五皿，每个对照皿接种 100、每个 4 Gy 皿接种 1,000。复算对照 PE=116/500=0.232，处理克隆形成比例=179/5000=0.0358，SF=179/1160=0.1543103448…，按两位小数为 0.15；论文列 0.16。原文使用 FEP‑1811 细胞，不能为这三瓶 T‑47D 提供缺失的实验记录。来源数据足以支持报告保留该数值差和排期边界。[协议表 1](https://pmc.ncbi.nlm.nih.gov/articles/PMC3197314/) · [精确分数](independent/counts-and-sf.json)

**排期与许可。** 本研究支持暂缓按此默认参数从整瓶扫描图直接出自动计数报告。可追溯点位复核与逐皿汇总的优先级仍取决于本地 SOP、含疑难样本的授权图像、逐皿接种和对照记录、独立人工标点与学生实际耗时。使用未见批次前确定偏差容差与人工复核成本。资料为 CC BY 4.0，改绘图已署名、链接并说明裁切和放大。SoftCount 固定版本为 MIT，备选 countPHICS2 为 GPLv3，ColCounter 的代码许可仍未核实。[资料记录](https://zenodo.org/records/4593510) · [SoftCount 许可](https://github.com/Nima-Sarfaraz/SoftCount/blob/4c4c3de0521dda51f4bc0cd466bc4ded1003488c/LICENSE) · [countPHICS2 许可](https://github.com/Gaorav-Gupta-Lab/countPHICS2/blob/bef5f4e47a95182a6b93ccd2bf3a222a7a298576/LICENSE)

**核验记录。** 独立源码/资料核验、SoftCount 重放及 `python -I -B .local/independent/counts_and_sf.py` 均 exit 0。P030 收尾绑定既有受审提交，20 组归档与研究材料的 Git 内容比对通过。最终准确规则检查、policy、git diff --check 均通过。计划检查在 base 与最终 head 均 exit 1，首错为 P010，缺少受审 SHA 的集合均为 P010、P021、P022、P023。未跑无关产品测试，必需 CI 和合并由规划窗口核实。
