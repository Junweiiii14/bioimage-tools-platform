# P014 成熟荧光核计数直接调用研究（已完成研究验收）

问题：在本机CPU上直接复用哪一个成熟实现，能在小型公开人工标注集上形成可复验的核计数/实例分割证据？本轮不开发产品或分割算法。访问日期2026-11-06。

## 已核来源与当前决定

- [CellProfiler稳定发行](https://cellprofiler.org/releases)及GitHub最新release均为4.2.8；现有官方安装版本命令实测一致。exe SHA与真实官方示例运行见[smoke记录](../../work/evidence/P-014/official-smoke.json)。从[官方示例页](https://cellprofiler.org/examples)取得Human示例，原pipeline版本5/DateRevision400、14模块，未经修改执行成功。示例README声明图像CC0。此处只验证官方程序执行，不把示例核数289当人工真值，也不把附带细胞/强度输出当本轮科学验收。
- 原有安装不修改，子进程APPDATA/LOCALAPPDATA/TEMP/TMP全部定向仓库外p014-research。第一次版本探针因宿主缺PROCESSOR_ARCHITECTURE报错；以platform.machine()实际AMD64补入子进程后成功。一次下载后枚举cppipe误读__MACOSX资源叉导致解码错误，未改变正式pipeline，执行明确指定ExampleHuman/ExampleHuman.cppipe。原始失败日志保留仓库外。
- [StarDist 0.9.2 README](https://raw.githubusercontent.com/stardist/stardist/0.9.2/README.md)明确2D_versatile_fluo适合单通道荧光核、训练于DSB2018子集。固定版本[模型注册表](https://raw.githubusercontent.com/stardist/stardist/0.9.2/stardist/models/__init__.py)指定v0.1权重，SHA256为4ad678d0758eed6e55625f1b5ae30771e59adb79f1239e09b9772eac8846c3dd。GitHub资产元数据5320433字节、创建2020-07-08。代码及[官方权重仓库](https://github.com/stardist/stardist-models)均BSD-3-Clause，下载前已分别核验。选择此小模型，暂不引入Cellpose大型基础模型。后续已完成隔离安装与CPU推理，实测成本和适用边界见下文。
- [TensorFlow官方安装说明](https://www.tensorflow.org/install/pip)提供原生Windows CPU路线。将用单独环境并固定实际解析版本，不改变产品锁文件；记录运行时完整依赖体积，不能只用5.3MB权重代表部署体积。
- [BBBC038](https://bbbc.broadinstitute.org/BBBC038)即DSB2018，[BBBC039](https://bbbc.broadinstitute.org/BBBC039)明确其中部分图片重叠。因此P013已见12test不作新独立评估；本轮不靠改名或另一个split声称消除预训练泄漏。
- 候选数据采用Kromp等2020的[S-BIAD634](https://uk1s3.embassy.ebi.ac.uk/bia-integrator-data/pages/S-BIAD634.html)（原S-BSST265）。[原始README](https://ftp.ebi.ac.uk/biostudies/fire/S-BIAD/634/S-BIAD634/Files/dataset/readme.txt)明确CC0，并区分完整groundtruth和仅每test类别抽25个核的singlecell_groundtruth；评估使用前者。BBBC020有官方不完整核标注警告，不作为本轮主要评价集。Nature原论文网页/PDF访问跳转失败，不声称已读全文；数据来源说明以作者README和EBI元数据为证。

## 预先冻结与证据边界

[分组清单](../../work/evidence/P-014/dataset-plan.json)先于任何选中原图/掩膜下载和候选预测冻结：3幅官方train作开发，10幅官方test作评估，按已发布制备、倍率和信噪比元数据有目的抽样。不是随机总体抽样；同一患者/细胞系可能跨组，患者层面独立性未证。数据发表晚于权重不证明采集/训练无重叠；未取得完整训练像素清单逐像素核对，不称独立泛化。

开发阶段只允许使用3幅开发图检查格式、核尺度及官方配置。评估组不得用于选参数；正式候选参数、前处理、输出标签转换和评价代码将在首次评估前另行固定提交。复用P013已审计IoU实例匹配评价；不修改watershed基线。性能记录须区分启动/推理耗时与实测内存定义，失败单列不得填零。

真实推理、CP配置冻结、逐图评价和选型已完成，详见下文；独审、必需CI及PR65集成已完成，收据见P014/final-delivery。更新版本/权重、数据来源或接入产品时重新核验。

## 首轮开发执行更新

本段记录开发阶段：730dd50后才下载3开发图与模型，当时10评估图仍未下载。隔离环境安装成功（完整依赖见requirements-development.txt），StarDist首图CPU推理成功，409核、1.203秒预测时间，不含首次导入/启动。CP开发3图成功，计数423/328/868且CSV与npy标签一致；原始GT第一图300核、第二图30核，提示当前配置过分割，不据此宣布可接入。官方加载后的pipeline从Experiment.csv的Pipeline_Pipeline字段提取（DateRevision428），不用猜测迁移参数。CLI虽然接受末尾measurements.h5参数却没有生成该文件，实际证据是CSV和npy，不宣称存在H5。TIFF解码首次缺imagecodecs报错；Pillow读取并核对TIFF头部形状/位深成功，组织图三通道逐像素完全相等，可无损选单通道；后续输入适配仍须逐图校验。

## 冻结评估结果与选型

1866b47冻结参数后下载10评估图；687e34a在首次评估运行前仅补权重阈值完整精度及成员摘要，实际阈值始终读取原权重。随后运行10评估图；没有测试后调参。两程序退出0、10/10结果齐全，CP实际加载pipeline与冻结文件全文一致，CSV核数与npy实例数逐图一致。不存在运行失败填零；指标中的0 TP是真实匹配结果。完整20行见[evaluation-metrics.csv](../../work/evidence/P-014/evaluation-metrics.csv)，参数与复现见[P014 README](../../work/evidence/P-014/README.md)。

| 固定管线 | 逐图平均F1 | 逐图平均计数相对误差 | TP / FP / FN | 整批进程墙时 | 采样进程树峰值RSS |
|---|---:|---:|---|---:|---:|
| CP 4.2.8，Global Otsu/自动declumping | 0.2155 | 1315.03% | 1098 / 4450 / 570 | 9.58秒 | 421.6 MB |
| StarDist 0.9.2，versatile_fluo，scale=0.5 | 0.8600 | 11.59% | 1488 / 191 / 180 | 12.72秒 | 535.7 MB |

以上是本次小样本/这两个冻结配置的结果，不能推断所有CellProfiler管线不适用。CP在尺度大、背景复杂的图上严重过分割，统一8–160像素范围和两种阈值的有限校准没有解决；normal_34计数827对833看似接近，但仍有138 FP/144 FN，说明只看计数会掩盖分割错误。原始方法不因这些结果重新调参。

StarDist最差计数相对误差为Neuroblastoma_13的38.46%（18对13），最低F1为低信噪组织图Ganglioneuroblastoma_10的0.6429（27 TP、19 FP、11 FN）。otherspecimen_5计数完全相等20对20，仍有4 FP与4 FN，F1=0.8。不能把平均0.86或单图正确计数写成普遍可靠。总GT1668核，重叠/患者独立性限制仍保留。

**选型：优先将StarDist作为下一步研究适配候选，保留CP作为可配置比较工具；本轮不直接授予默认自动核计数产品准入。** 它在本子集明显减少过分割且CPU可运行，代价是完整研究环境约2.02 GB（包含TensorFlow及科学计算依赖），对照已有CP安装约0.827 GB；5.3 MB仅权重压缩包。磁盘为逻辑文件字节、内存为50ms采样进程树RSS，不是精确独占峰值；单机单次运行/缓存状态未控制，时间不作跨设备承诺。

下一最小任务建议：仅建立独立核实例分割研究适配器，固定模型及预处理版本；输入只接受可证明单通道的2D原始数据，输出原坐标整型标签、核数、方法/权重/参数摘要和显式失败；由宿主进程外执行、支持取消和资源限制，不把TF放进平台领域层或GUI线程。先复用本公开复现材料测试接口/坐标/取消/错误，不做IF强度、全细胞、自动科学准入或安装器发布。真实实验室未见图、原始位深范围、用户可接受误差和尺度选择仍需后续证据；不能根据本8bit公开样本接受所有16bit数据。

本轮未新增产品/正式依赖，未覆盖原图、旧结果/安装或dirty树。已完成绑定候选独审、必要CI与正常PR65集成，正式回传记录见任务卡。工程验证不能代替上述科学限制。
