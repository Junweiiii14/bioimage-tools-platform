# P029 固定独审

**通过（pass）。** 本结论绑定 [PR80](https://github.com/Junweiiii14/bioimage-tools-platform/pull/80) 的 base `3103063d1abf116ef1d98694b9cc57f4dc70ae22`、冻结 head `506c96881c2e748ab9c2c1bb513a01914387f952`、研究内容 `69376e4e078928842988a889577021c5bc28969c`。2026-11-09，固定审查窗口，在独立 detached 工作树复核。远端分支与指定 head 一致。

**排期判断。** 公开材料支持将任务定义为从一种导出和一份签认 SOP 生成逐生物样本的相对表达表。保留需求候选、暂缓排期合理。进入开发前，需要用获准的脱敏逐孔导出、样本和板图记录及实验室现用计算表走查，以确定手工环节、配对方式、内参稳定性、效率、失效孔及校准规则。真实实验效果、学生需求与节时尚待现场验证。

**S2。** 从出版方重新下载工作簿，SHA256 为 `392883b5337f65c5099f04143bb160fa294492d438d1ebab49c7318ab6b18be3`。独立从 OOXML 读公式和数值，用标准库 Decimal 重算。原文说明两组各 6 个生物样本，每样本每个基因各 3 条技术 Cq。按样本归一后，以六个对照归一量的算术均值校准。T3 的原表公式 G30 采用 REF1 的 E30:E32，目标三孔为 D30:D32。三个基因的效率末行又分别被以 E40/C40/D40 引用，而表头是 C/D/E。核对两种口径如下。[独立回执](s2/receipt.json) · [论文图 2、图 4 和附件](https://bio-protocol.org/en/bpdetail?id=5729&type=0)

| 效率分组和引用 | Treatment 3 | 处理组均值 |
|---|---:|---:|
| 原工作簿的全部公式 | 5.92 | 2.27833 |
| 按表头重配基因和 Cq，沿用每基因全列效率均值 | 1.56 | 1.55500 |

两行均先舍入逐样本倍数再求均值，第一行全部 12 个显示值命中工作簿缓存。第二行使用全精度求处理均值为 1.55551836。两个结果都依赖各自的身份解释；原始孔身份和真实效应须由板记录等独立证据判定。

**N01，非阻断。** 报告第 27 行准确说明工作簿使用每个基因全部 36 项效率的均值。原论文图 2B 也采用全列，Result interpretation 段另写按每个基因、每个样本汇总技术重复。固定表头对应和六对照校准后，仅将效率改为每样本三个技术孔均值，Treatment 3 从 1.56268 变为 0.94166，跨过校准值 1。这个敏感性试算说明将来 SOP 要明确效率的汇总层级。公开数据无法判定应在用户实验中采用哪一口径。[交叉复算](primary/cross-check.json) · [原文](https://bio-protocol.org/en/bpdetail?id=5729&type=0)

**库和独立对照。** 核对 PyPI 4.1.4 wheel 与研究环境 43 个 qpcr Python 源文件。实际实现以 2x 为指数底数，所以已知扩增因子 F 时传 F/2。双内参几何均值由探针显式实现。按 Pfaffl 表 2 的 20 ng 数据 (2.09^5.283)/(1.99^-0.256) 得 58.592120675，与实际库输出吻合。原表 3 为 58.625，差约 0.056084%，原因未有独立证据。该点验证给定汇总输入下单内参的方向和计算，未包含原始孔级质控、样本方差或留出准确性。代码差异均在自研研究探针与证据范围，第三方算法、产品包和依赖锁无改动。[方法回执](method/receipt.json) · [Pfaffl 表 2、3](https://pmc.ncbi.nlm.nih.gov/articles/PMC55695/) · [qpcr 4.1.4](https://pypi.org/project/qpcr/4.1.4/)

**旧 RDML 与来源。** 独立下载固定 RDML，SHA256 为 `d77d72b962c94449d2844a071501d2ae920722f4a8816a967a49495a10eb4880`。读得 90 个反应、30 个样本×靶标组合、88 个数值 Cq；B10/B11 缺 Cq，首孔为 R-MoH9/HoxB1P1，Cq 25.4648305780052。厂商字段定义支持区分样本名、靶标、Task、排除与质量标记。本次没有本地仪器文件或真人走查。方法引用对效率校正与样本内归一的说明符合 MIQE 2.0。[RDML 回执](primary/cross-check.json) · [原 RDML](https://raw.githubusercontent.com/ramiromagno/rdml/fe484d11594735cfe2d65dcbcc1f58f9315a849b/datasets/rpa.rdml) · [Well Table](https://apps.thermofisher.cn/apps/help/MAN0010504/GUID-62A71BB6-471A-4BEE-BD91-978F4D1EDE42.html) · [MIQE 2.0](https://pubmed.ncbi.nlm.nih.gov/40272429/)

**复现与仓库状态。** 在独立工作目录，以指定研究环境 CPython 3.11.15 的 `-I -B` 重跑两支提交探针，均 exit 0。独立 S2 公式、RDML 与 Pfaffl 探针也各为 0。准确 base/head 的规则回执检查、policy 和差异空白检查均为 0。38 组文件内容比对确认 P027、P028 收尾与历史清单携带正确，P029 任务卡绑定研究内容。计划检查在 base 和 head 上均为 1，缺少受审 SHA 的同一历史集合是 P010、P021、P022、P023；本轮新增零项。未运行产品测试、仪器软件、Excel 重算或真实实验。合并和必需 CI 由规划窗口核实。[治理回执](governance/p029-governance-506c968.json) · [S2 探针输出](primary/probe.log) · [Pfaffl 输出](primary/pfaffl.log)

科学证据审阅方法参考 Kassis、Agarwal、He、Patel 与 Brueckner（2026）的 Scientific Agent Skills。[方法来源](https://arxiv.org/abs/2609.00065)
