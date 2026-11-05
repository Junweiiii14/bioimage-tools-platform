# 当前恢复入口

当前任务[P014成熟核计数方法直接调用](../work/tasks/P-014-mature-nuclei-methods.md)，已接上游明确派发并创建新goal，分支codex/p014-mature-nuclei-methods。main cddf759已合入00bce42；P013历史回执祖先问题已真实重载并单独提交b882b8e，P014 context成功。CellProfiler 4.2.8官方Human示例已真实成功执行，289核、9.44秒，仅执行烟测。Kromp元数据已核并冻结3开发/10评估图（dataset-plan.json），730dd50冻结后已下载3开发图和权重，10评估图未下载。CP开发3图与StarDist首图CPU均真实运行成功，官方加载后pipeline已从Experiment.csv提取。1866b47/687e34a冻结配置后10评估图两方法均成功；20行指标/内存时间已归档。SD平均F1 0.8600，仍有最差计数误差38.46%。下一步候选独审、CI/PR和回传。全部实验进程终态，不重复调参或运行。不自研分割，不碰产品依赖与旧dirty树。

[P013第二实验研究与成熟算法准则](../work/tasks/P-013-second-experiment-discovery.md)已完成研究和集成，证据见[final-delivery](../work/evidence/P-013/final-delivery.md)。活动树bioimage-plan-sync，分支codex/p013-algorithm-reuse-plan；原bioimage-tools-platform dirty树/旧GUI与安装不碰。

PR63研究合入d85c3e5，PR64正式MD/HTML准则合入main cddf759，两次候选与合入树一致；Windows1703passed/Linux1699passed+4既有skip、双平台wheel及全部必需门禁成功。独审476b47e核对30行一致。CI/监测均终态，不重启已完成研究和测试。当前本地收尾记录随下一正常任务带入。

研究只运行scikit-image基线，未运行CellProfiler/StarDist/Cellpose。test最差计数误差71.01%，没有科学准入或IF强度/全细胞验证。主方案第5节、开发流程第3节及同名HTML已明确成熟实现优先、先检索/实测再自研，适用所有实验模块/算法研发Agent。

最终验收和下一步方案已成功送达上游01a19bfd-f3ab-7502-86da-9f61953d1c8a（local），工具返回该threadId。下一步由上游在授权范围连续派发，不等用户催促。优先真实调用CellProfiler官方pipeline，再按固定版本/代码与权重许可/CPU成本选少量成熟候选；先排查BBBC038/039/DSB2018及预训练数据重叠，再定未见留出。来源入口见P013/plan-amendment。已见12test只作诊断。

P012/历史科学、真人学生、干净Windows/GPU未验仍保留，见risks/backlog及各任务final-delivery。旧快照完整保留在archive/P013-before-closeout-snapshot.md；P012收据已随PR63入main。

用户再次明确要求每次验收后回传上游，由上游自动派发下一步；本轮已立即发消息至既定上游，工具返回threadId且isError=false。普通交接不等待用户再次继续，授权边界与审查门禁不变。
