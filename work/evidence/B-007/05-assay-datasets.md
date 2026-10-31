## 六类实验的公开开发数据：具体记录、可用范围与缺口

核验日期：2026-10-31。机器可读台账是同目录`assay-datasets.json`，七条覆盖克隆、划痕、qPCR、ELISA、IHC、流式，其中流式保留访问失败记录并新增实际下载成功的RepOD样例。记录“候选”表示已找到具体数据对象和证据，不表示已经跑通算法或通过科学准入。本轮未下载大数据、未解压归档、未安装这些分析软件、未训练模型；另将一个3.7 MB公开FCS核对头与校验和后保存到本地交付目录，并附来源文件。网络读取失败也如实保留。下面每个数据集的工程安排是本项目拟议设计。

### 一眼可用的选择表

| 场景/台账ID尾部 | 实际对象与取得入口 | 已核实内容 | 首次开发用途 | 阻止过度结论的限制 |
|---|---|---|---|---|
| 克隆：4593510 | [Zenodo记录4593510](https://zenodo.org/records/4593510)，`Dataset1_T47D.zip` | 16张T-47D染色培养瓶扫描图，多个观察者坐标；归档479.0 MB；原网页明确CC BY4.0 | 扫描图读取、坐标对应、菌落/克隆计数误差观察 | 不是多孔板定位集；观察者点坐标不是逐像素面积真值；归档内例外尚未检查 |
| 划痕：21779854-V2 | [Zenodo v2记录](https://zenodo.org/records/21779854)，[作者精确数据说明](https://github.com/nykemariotto/scratch-assay-segmentation/blob/main/dataset/README.md) | 作者说明1,363张PNG、COCO/YOLO多边形与采集分组CSV；3.7 GB | 缝隙分割、完全闭合负例、按采集单元留出 | v2元数据由作者仓库核验，Zenodo页面工具未取到；尚未下载。旧v1存在泄漏，禁止混用 |
| qPCR：RAS002-1.1-2 | [归档7009124](https://zenodo.org/records/7009124)，`PCRedux-1.1-2.tar.gz` | 固定软件包8.1 MB；维护者手册说明RAS002扩增曲线及类别标签 | 曲线读取、QC状态、特征/标签对应 | 不是完整相对表达实验设计；不能自动充当ΔΔCq生物样本验证集 |
| ELISA：0.1.8-EXTDATA | [固定命名分支的extdata目录](https://github.com/BULQI/ELISAtools/tree/ReleaseV0.1.8/inst/extdata) | 已读板读数、实验设计、两板注释与标准浓度文件 | 多板导入、孔角色绑定、拟合/排除/倍数重算 | 标准品单位、未知样本真实浓度与来源不完整；是软件分发示例，不能称为临床验证集 |
| IHC：OS-2-NDPI | [原站具体文件元数据](https://openslide.cs.cmu.edu/download/openslide-testdata/Hamamatsu/index.yaml)，`OS-2.ndpi` | Ki-67明场切片，931.42 MB，官方SHA256和自由使用分发条款 | 切片/金字塔读取、分块定位、取消、人工区域工具 | 一张切片，无已核实阳性细胞真值；不能按patch拆出独立病例测试 |
| 流式：FR-FCM-ZZJ7 | [FlowRepository具体记录](https://flowrepository.org/id/FR-FCM-ZZJ7) | 两个FCS和两个附件，供API/库测试 | FCS读取、门树成员与统计、表格导出 | 原站直开502，下载直链未取得；许可unknown；无完整补偿和自动门控真值证据 |
| 流式首选工程样例：JOLWGT-V2-FILE96794 | [RepOD具体文件96794](https://repod.icm.edu.pl/file.xhtml?fileId=96794&version=2.0)，DOI10.18150/JOLWGT V2 | 实际HTTP200读取3,870,980字节；FCS3.1；MD5与原站一致；文件级CC BY4.0 | FCS读取、已解混状态、通道/门控交互及统计 | 无已核实供者级真值；已解混文件不能默认再次补偿；一文件不是科学留出集 |

### 克隆：点标注可验证计数，不能假装面积金标准

[原始记录](https://zenodo.org/records/4593510)提供的扫描信息包括48-bit RGB、2125×2985、1200 dpi，以及观察者对超过50个细胞克隆的坐标。已发现[指定归档下载链接](https://zenodo.org/records/4593510/files/Dataset1_T47D.zip?download=1)，但二进制读取返回cache miss；文件清单中的MD5是来源声明，尚未与本地文件比对。网页文本提取曾漏掉许可，根代理后续直接读取原HTML的rights、许可链接和JSON-LD确认CC BY4.0，证据在`license-html-probe.json`。采用时核验归档内有无文件专用例外、实际图像扩展名、轴与每个观察者坐标的一一对应，再选整瓶图作回归样本。容差需由标注差异和实际比例确定，不能提前指定“100%识别正确”。

开发集保留完整原图和所有观察者标签，派生缩放/裁块都回指同一瓶。同一实验日期、同一瓶全部派生物留在同一分区；16张图的图像数不能当独立实验数。首个工程验收可检查单个标注点经显示缩放后仍定位原坐标；计数算法的匹配半径必须绑定像素尺度。面积法另需人工复核的区域mask、多孔板定位另需整板图。ColonyArea作者原先链接的[B2SHARE记录](https://b2share.eudat.eu/records/39fa39965b314f658e4a198a78d7f6b5)本轮返回404，不能列为已可下载资产。

### 划痕：只采用修正泄漏后的v2，并保留原采集分组

[作者数据README](https://github.com/nykemariotto/scratch-assay-segmentation/blob/main/dataset/README.md)明确说旧版[20298130](https://zenodo.org/records/20298130)按图像划分，导致同一采集视野帧跨集合，已被v2替代。新版本给出[真实下载地址](https://zenodo.org/records/21779854/files/dataset.zip)，并公开分组与标签结构；不要把旧版图像数或640像素输入配置移到新版。图像/COCO声明CC BY 4.0，模型及依赖的授权单独核验，不能因为仓库显示MIT就把Ultralytics相关模型一并按MIT使用。仓库当前仍称论文为2026年投稿稿。

拟先用作者仓库列出的四张带标注小样完成解析/叠图，再在授权和文件核验后取完整归档。固定v2与代码commit、文件SHA256和划分表；保持`split_key`闭包，若可得供者、板和孔信息进一步升格到这些层级留出。已经看过的公开测试集用于调阈值后就不再是本项目盲测集。采集时间/视野配对须从映射文件确认，缺这些字段时数据只支持单图分割，不承诺闭合率整链。漂移校正还需人工地标或合成已知位移验证；“分割IoU高”不能替代“同一观察窗闭合率正确”。

### qPCR：曲线QC公开数据和相对表达实验必须分开

[Zenodo固定归档](https://zenodo.org/records/7009124)可追溯至PCRedux 1.1-2，[维护者手册](https://pcruniversum.r-universe.dev/PCRedux/doc/manual.html)明确`RAS002`来自`RAS002.rdml`，`RAS002_decisions`来自`decision_res_RAS002.csv`。归档8.1 MB和MD5已读取；[精确归档入口](https://zenodo.org/records/7009124/files/PCRedux-1.1-2.tar.gz?download=1)未下载。根代理直接原HTML探测确认记录声明CC BY4.0，软件代码另声明MIT；两种范围不能混为一项。归档内文件专用例外和原始实验身份尚未检查，准入时保留两层声明并核对实际文件，不能单凭软件MIT推断数据授权。

拟先将可核对的曲线、周期、标签规范化为有原始引用的表，检查标签与曲线ID错位会被拒收；不拿某软件计算的Cq自身作为新算法的唯一真值。以后开发原始曲线Cq/效率算法需独立方法比较与失败边界。首版相对表达流程采用仪器导出Cq时，还必须补一套包含处理组、内参、参照样本、技术/生物重复身份的真实实验，和一套可手算的构造夹具；两者在报告中分别标为实验数据、算术测试。缺失这些身份时不自动推断一个“控制组”。整板/原始实验留出，同一曲线的40个周期绝不能拆成训练和测试样本。

### ELISA：已有具体板级示例，独立QC仍是缺口

已读取[设计文件](https://github.com/BULQI/ELISAtools/blob/ReleaseV0.1.8/inst/extdata/design.txt)、[两板角色映射](https://github.com/BULQI/ELISAtools/blob/ReleaseV0.1.8/inst/extdata/AnExp_2plate.txt)、[标准浓度文件](https://github.com/BULQI/ELISAtools/blob/ReleaseV0.1.8/inst/extdata/stdConc.txt)和[Assay_11_and_12原始导出正文](https://github.com/BULQI/ELISAtools/blob/ReleaseV0.1.8/inst/extdata/Assay_11_and_12.txt)。读数文件有96孔坐标及450/620 nm端点吸光元数据；设计含三个运行文件、两个batch和共五板声明。相比只给几行XY标曲，这些材料能检验实际孔身份和配套文件装配。标准数值有0，但文件未给充分单位，导入时需标为unknown待绑定，不能猜作ng/mL。

拟将示例原文件、规范化OD、角色板图、标准回算和未知浓度输出组成一套可比较工程夹具。必须先确认读数文件已有变换/背景处理标签，避免重复扣参考波长。软件文件内名叫Control不自动证明它是有证书浓度的独立QC；没有已知QC值，不得声称LLOQ/ULOQ已经验证。示例批次可测试跨批显示与来源闭包，但是否能科学纠正批次效应另走方法验证。整运行/板留出；同一试剂标准和同一标本的重复不得跨开发/保留集。命名分支可变，后续下载需固定commit或固定CRAN版本归档。

### IHC：OS-2是读取与界面的现实大图，不是病理效能验证集

[OpenSlide原始索引](https://openslide.cs.cmu.edu/download/openslide-testdata/Hamamatsu/)写明OS-2是Ki-67切片，并给自由使用、分发、允许修改的说明；[YAML](https://openslide.cs.cmu.edu/download/openslide-testdata/Hamamatsu/index.yaml)给出SHA256。精确[NDPI入口](https://openslide.cs.cmu.edu/download/openslide-testdata/Hamamatsu/OS-2.ndpi)返回image/tiff类型，文本工具不能解析；未下载931.42 MB。来源不是CC0，不把QuPath软件的GPL或文档CC BY套在该切片上。[QuPath许可来源表](https://qupath.readthedocs.io/en/stable/docs/intro/acknowledgements.html)提供交叉印证。

未来最小开发步骤是验证图像尺寸/金字塔/物理尺度→框选区域在全片和局部视图定位一致→分块任务取消可恢复→导出区域坐标与mask。若要评估阳性面积或细胞端点，应为少量区域另建有审核记录的注释，标出折叠、坏死、背景等范围，且把面积与细胞标签分开。单片只能用作工程回归；科学留出必须补新病例、染色批和扫描仪，并以病例为最小分组。

### 流式：具体FCS记录可追溯，当前访问与许可均需补核验

[FR-FCM-ZZJ7官方记录](https://flowrepository.org/id/FR-FCM-ZZJ7)的搜索索引和[Bioconductor官方说明](https://bioconductor.riken.jp/packages/3.13/bioc/vignettes/FlowRepositoryR/inst/doc/HowTo-FlowRepositoryR.pdf)均指向两个FCS及`about.txt`、`ExampleGate.png`；它本来就是FlowRepository API和R库的轻量测试数据。直接记录页本轮返回502，因此JSON的`download_url`为null，而非编造下载API。官方说明有`flowRep.get("FR-FCM-ZZJ7")`之后按文件下载的路径，但本轮没有执行或保证当前成功。公开可见不等于商用授权，许可保持unknown。

未来恢复访问后先确认FCS版本、字节序、事件数、通道、补偿来源和附属说明；将一个经人工核对的小门树保存成工程预期，分别检查父门改变、门坐标空间改变和空父群的统计。门示例PNG只能辅助目视比对，不能替代完整机器可读参考门。这个两文件子集不足以验证新自动门控、补偿或临床判别。按供者及其所有时间点分组，事件级随机拆分会把同一样本分布同时泄漏到训练和测试中。

### 流式补充：已实际取得的RepOD文件可启动工程

[原始数据集DOI10.18150/JOLWGT V2](https://repod.icm.edu.pl/dataset.xhtml?persistentId=doi:10.18150/JOLWGT)来自Mossakowski Medical Research Institute PAS，描述17色光谱流式PBMC及PBMC–GSC共培养数据，并列FMO与滴定文件。选取其[具体文件96794](https://repod.icm.edu.pl/file.xhtml?fileId=96794&version=2.0)：`Fig.3A_Discrimination of PBMC from GSC_Unmixed.fcs`，发布2026-03-02，文件本身明确CC BY4.0，不依赖软件代码许可证推断。文件页公开[下载端点](https://repod.icm.edu.pl/api/access/datafile/96794)。

2026-10-31以Windows正常HTTPS证书校验，未登录读取返回HTTP200，实收3,870,980字节。MD5为`859e65ad411ff209256468b200f94311`，与原站完全一致；本次计算SHA256为`3f208d4dbc3fd1945634a591e6f19c794db913fca6c8c10117a8dc9d59cc9a86`；58字节头识别为`FCS3.1`。命令退出0，随后再次核对并将原字节保存为`.local/deliveries/B-007/development-samples/Fig.3A_Discrimination of PBMC from GSC_Unmixed.fcs`，附`flow-repod-96794.provenance.json`，不提交源数据。先前Python路径因本地CA链校验失败退出1，没有关闭TLS验证；后改用系统信任存储成功。尚未解码事件、统计通道或执行门控，因此不能宣称解析器已经通过。

工程优先以这个文件完成下载校验→FCS头/TEXT/DATA有界解码→通道表与散点→模板门/可选接管→父门及布尔依赖重算→结果表。它是实际实验文件而非理论模拟，但`Unmixed`处理状态必须记录，不能默认再施加传统补偿；是否可用于某一生物门模板取决于通道和前处理核验。CC BY要求保留作者、DOI、许可及修改标识。门控预期需另建经审阅的小样标签；患者/供者身份、同实验跨文件对应尚未确认，不拿单文件事件随机切分证明跨供者泛化。这一记录解决“有可取文件和数据许可”的开发启动条件，保留旧FlowRepository访问失败证据，不把它静默替换成成功。

### 入库后的可执行动作与成果边界

每个数据包在真正取得后输出`source-record.json`、原文件清单/校验和、许可证快照、身份映射、可用字段与缺失表、不可变划分清单。再产生最小规范化样本和与原文件相互定位的预览，不把大原图提交仓库。下载/读取状态从“记录已核验”逐级升为“文件已核验”“格式已解码”“标签已审阅”“方法适用”；任何一层都不能代替下一层。

这些数据可以启动工程，尚不能合起来宣布六类实验已通过。上线某模板前，仍须补该模板对应的格式、仪器、独立实验和失败样本；公开数据找不到完整闭环时记录具体缺字段，保持研发可推进，并把正式数据适用范围收紧。正常自动运行和可选接管的验收案例，使用上述真实数据能支持的部分；精确算术、取消竞态和身份错误使用明确标注的构造夹具补足，绝不把合成示例包装成真实实验成功。
