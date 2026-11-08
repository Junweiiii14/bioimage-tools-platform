# qPCR 相对表达要不要排入开发

**2026-11-09 决定建议：保留需求候选，暂缓产品排期。** 已有公开证据足以定义“一次导出到逐样本表达表”的窄任务，也能实际算出数值。缺口是本地实验室使用哪一种仪器导出、沿用什么 SOP、如何认定独立样本与有效孔，以及学生是否真的花时间在这一步。先由用户协调一位学生拿一批获准使用的脱敏导出、板图/实验记录、使用中的计算表与期望图做一次走查。观察从哪一步开始手工抄值，记录完成时间、对照结果和首次失败。若现有软件导出的样本表已够用，收束候选。付费意愿另由用户核实。

[旧 B007](../../work/evidence/B-007/supplement-qpcr-dataset.md) 已查清鸡胚 RDML 的孔位、缺失和设计限制。本次按原 SHA 重新下载并解开文件，首反应 R-MoH9 × HoxB1P1 的 Cq 为 25.4648305780052。沿用其 B10/B11 缺 Cq、90 孔仅 88 个数值的阴性用例。原作者开放数据声明 CC0。三个技术孔不能补出独立生物重复，文件也不足以选择校准样本或填效率。本轮增量在另一份含生物样本和效率的工作表。[固定 RDML](https://raw.githubusercontent.com/ramiromagno/rdml/fe484d11594735cfe2d65dcbcc1f58f9315a849b/datasets/rpa.rdml) · [数据论文](https://doi.org/10.1186/s13104-017-2533-9)

## 学生应拿什么，交出什么

候选任务为把一次处理/对照实验整理成导师可追查的样本表达图。厂商 Well Table 有 Well、Sample、Target、Task、Ct、Ct Mean/SD、Amp Status、Cq Conf、Omit 与 Flags。Task 可为 Unknown、Standard、NTC，不能据它判断处理组。导出列可选，需保留原文件、软件版本、运行/板号、阈值与基线设置以及原始行号。只有组均值或截图时无法核对孔身份。这里核的是字段定义，未实测本地 QuantStudio 文件兼容性。[Thermo Fisher Well Table](https://apps.thermofisher.cn/apps/help/MAN0010504/GUID-62A71BB6-471A-4BEE-BD91-978F4D1EDE42.html) · [厂商导出设置](https://apps.thermofisher.com/apps/da2/help/GUID-F6C72E83-927D-4AC1-9C4C-39463C0E5906.html)

| 须由记录提供 | 用途与信息不足时的处理 |
|---|---|
| 板/孔/assay → 提取物、RT 批次、生物单位 ID、分组、配对/重复测量关系 | 同一材料的技术孔先按 SOP 汇总。同一个体再次上板不增加生物 n。重复孔顺序不代表配对；身份冲突停在逐孔清单。跨板须有明确可比性与板间校准，本候选只考虑单次可比运行。 |
| 每个靶标的身份、内参组合和在该处理条件下的稳定性依据 | 同一样本先求目标量，再用同一样本的内参量归一；多个经验证的内参按指定方法合成。缺内参或未验证则标状态，不出正式倍数。 |
| 校准样本或校准组、组内如何取代表值、对照方向 | 下例取六个对照归一量的算术均值。单校准样本、平均 Cq 与平均归一量有不同含义；须记录方法版本。 |
| 各 assay 每周期扩增因子及来源、单位、验证范围 | 记录标准曲线斜率、稀释与有效范围，或保留曲线方法及效率输出。标准曲线的因子 F=10^(-1/slope)，效率百分数为 100×(F−1)。只有 Cq 不能补算真实效率。 |
| 原始数值或未检出标志、NTC/no-RT、适用的熔解/特异性、LoD/LoQ、排除原因与最少有效技术孔 | 区分空值、无扩增、可疑扩增、人工排除和低于定量范围。保留总孔数、有效孔数与技术离散度；异常按实验 SOP 处置。对照异常或剩余孔不足时给原因，不能填 0、循环上限或自动删孔继续。 |

输出按生物单位 × 靶标一行，含组、配对 ID（如有）、技术孔有效数/总数、目标与内参 Cq 汇总、因子/来源、归一量、校准定义、无量纲倍数、状态、原孔索引。另给各组计划/有效生物 n、汇总尺度与误差定义。图以组为横轴，纵轴为相对校准的表达倍数，每个有效生物样本一个点，1 为校准参照线，若有真实配对关系才连线。缺失样本在表中留行并在图注说明。统计模型、置信区间和显著性需要设计与样本量支持。示例按表头方案得到 TARGET 的 Control 1 = 0.93、Treatment 3 = 1.56，各有三条目标 Cq 与每内参三条 Cq，分母为六个对照；附件无仪器逐孔质控字段，均只标“演算”。

MIQE 2.0 建议用效率校正量、先在生物样本内归一再比较组。复现明确指定的历史 Livak 方法时才使用其近似等效率、近倍增等适用前提与校准方向，同时保留 SOP；不以 2 的默认值救活缺效率的实验。[MIQE 2.0，2025，数据分析章节](https://academic.oup.com/clinchem/article/71/6/634/8119148) · [Livak & Schmittgen，2001](https://doi.org/10.1006/meth.2001.1262)

## 实文件与数值证据

Müller 与 Tiret (2026) 的 S2 为已预处理的匿名真实数据。实开仅有 Efficiencies、TARGET 两张表；两组各六个生物样本，每样本三条 Cq × 三个 assay，并有对应效率列。读取附件公式及缓存，两者分别用于追踪引用和对照结果。论文标 CC BY-NC 4.0，本次只在本机研究核查，库内提供下载位置、哈希与自行编写的探针，不随产品分发附件。文章未单列附件的商业再分发授权。[原文、图4和附件声明](https://bio-protocol.org/en/bpdetail?id=5729&type=0) · [S2 文件](https://cdn.bio-protocol.org/journal/static/5729_qPCR%20validation%20dataset.xlsx?v=1051)

每个 assay 用该列 36 个效率因子的均值 F；逐样本对三个技术 Cq 求平均，以 qpcr.Analyser 得 Q=F^(−mean Cq)。两个内参量取几何均值，目标除以内参后再除以六个对照归一量的算术均值。qpcr 4.1.4 的 Assay.efficiency(x) 实际使用 2x，此处明确传 F/2。附件先将每个倍数舍入至两位，再求处理组均值。实际发现两处身份冲突：

| 实际计算口径 | Treatment 3 | 处理组六点均值 |
|---|---:|---:|
| 忠实重放 S2 公式，12 个样本显示值均与缓存一致 | 5.92 | 2.27833（图4约 2.28） |
| 按原列标题一一对应，目标始终取目标 Cq | 1.56 | 1.55500（先用全精度平均则为 1.55552） |

Efficiencies!C3:E3 依次写 TARGET、REF1、REF2，TARGET!G:I 的公式却依次取 E40、C40、D40。另在 TARGET!G30 把 Treatment 3 目标的 Cq 引到 E30:E32（REF1），该目标 Cq 实在 D30:D32。仅作者或原始板记录能确认实际身份。两个数分别说明公式复现与表头解释，均不认证生物学真值。S2 也缺原始板位、逐孔 flags、曲线和独立的内参稳定性资料。不能把 2.28 作为今后工具必须命中的金标准。

独立于软件的数值参照取 Pfaffl (2001) 表2/3，高输入 20 ng 同量条件，TyrA 与 Gst 的 control/sample 平均 CP 及因子输入 qpcr.Analyser + Normaliser，control=1，sample=58.592121，表3为 58.625（差约 0.056%）。论文展示数位有限，差异原因未独立确认。该比较仅覆盖已汇总行的单内参效率校正、分子分母及方向，不能重建独立生物样本、方差或检验。它也没有验证 S2 的原始条件。[Pfaffl 表2和表3](https://pmc.ncbi.nlm.nih.gov/articles/PMC55695/)

## 复用和下一步

实跑的 Python qpcr 4.1.4（GPLv3）提供按 assay 的指数转换和单内参归一，研究环境可独立运行。S2 的双内参几何均值及校准在探针中显式执行。输入必须先按身份对齐，不能依赖行序或库的默认效率。只核本机隔离运行；若以后分发，须确认 GPL 义务和项目交付方式。一个实际备选是原作者 S2 的表格工作流，学生可看公式，公开样例却有上述引用问题、固定范围与商业复用许可限制，故不直接选为交付模板。未引入项目依赖。[qpcr 4.1.4 发布与许可](https://pypi.org/project/qpcr/4.1.4/) · [处理接口](https://qpcr.readthedocs.io/en/latest/qpcr.main.html)

若走查确认需求，再以**一种导出、一种签认 SOP、一份独立算例**评估适配。沿用平台已有的输入快照、模板参数、结果表/图和保存重开；样本映射、孔质控和效率方法归实验工具。事先与负责人约定样本身份一致、失败样本保留、独立样本结果及容差，再用未参与设计的另一批数据验收。用户尚未提供实地反馈、授权样本或购买意愿。本轮未开发入口、收费功能，亦未替换安装。

### 复现

Windows，CPython 3.11.15，项目外 venv。以下在仓库根执行，两支探针均实际退出 0；未运行仪器软件、LinRegPCR 或 Excel 重算。S2 的 SHA-256 由脚本核验；完整环境版本见[版本清单](../../work/evidence/P-029/research-versions.txt)。

~~~powershell
$d = Join-Path $env:TEMP p029-replay
uv venv --python 3.11.15 "$d/venv"
uv pip install --python "$d/venv/Scripts/python.exe" -r work/evidence/P-029/research-versions.txt
curl.exe -fsSL 'https://cdn.bio-protocol.org/journal/static/5729_qPCR%20validation%20dataset.xlsx?v=1051' -o "$d/s2.xlsx"
& "$d/venv/Scripts/python" work/evidence/P-029/probe.py "$d/s2.xlsx"
& "$d/venv/Scripts/python" work/evidence/P-029/pfaffl.py
~~~
