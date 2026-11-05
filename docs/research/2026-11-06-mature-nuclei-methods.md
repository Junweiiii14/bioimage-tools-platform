# P014 成熟荧光核计数直接调用研究（进行中）

问题：在本机CPU上直接复用哪一个成熟实现，能在小型公开人工标注集上形成可复验的核计数/实例分割证据？本轮不开发产品或分割算法。访问日期2026-11-06。

## 已核来源与当前决定

- [CellProfiler稳定发行](https://cellprofiler.org/releases)及GitHub最新release均为4.2.8；现有官方安装版本命令实测一致。exe SHA与真实官方示例运行见[smoke记录](../../work/evidence/P-014/official-smoke.json)。从[官方示例页](https://cellprofiler.org/examples)取得Human示例，原pipeline版本5/DateRevision400、14模块，未经修改执行成功。示例README声明图像CC0。此处只验证官方程序执行，不把示例核数289当人工真值，也不把附带细胞/强度输出当本轮科学验收。
- 原有安装不修改，子进程APPDATA/LOCALAPPDATA/TEMP/TMP全部定向仓库外p014-research。第一次版本探针因宿主缺PROCESSOR_ARCHITECTURE报错；以platform.machine()实际AMD64补入子进程后成功。一次下载后枚举cppipe误读__MACOSX资源叉导致解码错误，未改变正式pipeline，执行明确指定ExampleHuman/ExampleHuman.cppipe。原始失败日志保留仓库外。
- [StarDist 0.9.2 README](https://raw.githubusercontent.com/stardist/stardist/0.9.2/README.md)明确2D_versatile_fluo适合单通道荧光核、训练于DSB2018子集。固定版本[模型注册表](https://raw.githubusercontent.com/stardist/stardist/0.9.2/stardist/models/__init__.py)指定v0.1权重，SHA256为4ad678d0758eed6e55625f1b5ae30771e59adb79f1239e09b9772eac8846c3dd。GitHub资产元数据5320433字节、创建2020-07-08。代码及[官方权重仓库](https://github.com/stardist/stardist-models)均BSD-3-Clause，下载前已分别核验。选择此小模型，暂不引入Cellpose大型基础模型。尚未安装或推理，不能写成可部署结论。
- [TensorFlow官方安装说明](https://www.tensorflow.org/install/pip)提供原生Windows CPU路线。将用单独环境并固定实际解析版本，不改变产品锁文件；记录运行时完整依赖体积，不能只用5.3MB权重代表部署体积。
- [BBBC038](https://bbbc.broadinstitute.org/BBBC038)即DSB2018，[BBBC039](https://bbbc.broadinstitute.org/BBBC039)明确其中部分图片重叠。因此P013已见12test不作新独立评估；本轮不靠改名或另一个split声称消除预训练泄漏。
- 候选数据采用Kromp等2020的[S-BIAD634](https://uk1s3.embassy.ebi.ac.uk/bia-integrator-data/pages/S-BIAD634.html)（原S-BSST265）。[原始README](https://ftp.ebi.ac.uk/biostudies/fire/S-BIAD/634/S-BIAD634/Files/dataset/readme.txt)明确CC0，并区分完整groundtruth和仅每test类别抽25个核的singlecell_groundtruth；评估使用前者。BBBC020有官方不完整核标注警告，不作为本轮主要评价集。Nature原论文网页/PDF访问跳转失败，不声称已读全文；数据来源说明以作者README和EBI元数据为证。

## 预先冻结与证据边界

[分组清单](../../work/evidence/P-014/dataset-plan.json)先于任何选中原图/掩膜下载和候选预测冻结：3幅官方train作开发，10幅官方test作评估，按已发布制备、倍率和信噪比元数据有目的抽样。不是随机总体抽样；同一患者/细胞系可能跨组，患者层面独立性未证。数据发表晚于权重不证明采集/训练无重叠；未取得完整训练像素清单逐像素核对，不称独立泛化。

开发阶段只允许使用3幅开发图检查格式、核尺度及官方配置。评估组不得用于选参数；正式候选参数、前处理、输出标签转换和评价代码将在首次评估前另行固定提交。复用P013已审计IoU实例匹配评价；不修改watershed基线。性能记录须区分启动/推理耗时与实测内存定义，失败单列不得填零。

尚欠：真实StarDist推理；适用核计数CP流程与参数冻结；逐图评价、内存/部署成本；选型与最小接入范围；绑定提交独审、必需CI、PR集成和上游回传。更新版本/权重、数据来源或接入产品时重新核验。
