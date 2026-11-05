# P-014 成熟2D荧光核计数实现直接调用与对照

<!-- PROGRAM_TASK_META {"id":"P-014","status":"in_progress","work_package":"W07","depends_on":["P-013"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex mature-method research","base_commit":"cddf759d20368f10e3ea1d447503dcc3cf3740ea","head_commit":null} -->

## 授权与范围

2026-11-06上游依据用户持续推进/成熟算法优先要求明确派发，旧goal已完成，新goal已实际创建且无token预算。研究与最小接入建议，不做产品接入/正式依赖/IF强度/全细胞/Agent，不训练或自行研发分割算法。允许合理大小公开模型存仓库外隔离缓存，不下载超大基础模型、不花费、不上传私有数据。原dirty树/GUI/原图/旧安装不碰。

## 完成条件

1. 核验当前稳定发布及接口/代码许可，真实运行CellProfiler官方程序与适用pipeline/IdentifyPrimaryObjects；旧cp3 pipeline仅在官方加载/迁移有效时采用并保存转换版本/参数。不能自行重写冒充官方链。环境隔离；遇安装困难查官方支持路线，不因小问题放弃或无限试错。
2. StarDist荧光核预训练模型或Cellpose具体适用模型至少一个合理对照真实运行；先核版本、代码/权重许可、大小、CPU内存/部署成本，客观无法运行须有证据。
3. 评测前查训练来源和BBBC038/039/DSB2018重复，选择人工实例标注公开数据、冻结开发/评估组；已见12test仅诊断，未知重叠不称独立泛化。优先少量代表性明暗/密集/粘连场景，不在测试组调参。
4. 可按官方设置在开发组配置，再冻结参数；保留完整实际前处理和输入缩放差异。复用P013已审计评价，逐图计数/匹配/失败、运行时间和内存/部署负担，不只报平均分。不改变自有watershed基线追赶。
5. 一份精简选型、固定版本运行脚本/官方pipeline出处配置、非私有复现实测，明确直接复用谁及限制、下一最小产品接入任务范围；无方案适用则如实给证据和下一最小调查，不强行自研。公开基准不代替学生/实验室验收。
6. 绑定候选只读独审、适当本地检查、正常PR必需CI集成、更新handoff并回传上游01a19bfd-f3ab-7502-86da-9f61953d1c8a（local）接续。

## 当前状态

查重无P014。干净树从6868b06建立codex/p014-mature-nuclei-methods，合入最新main cddf759；squash产生6份旧交接冲突，核验main与887fd53树相同、差异仅P013较新收尾后保留本地，合并00bce42。469152c/6868b06收据保留，产品不变。P014 context及登记已完成。已真实运行官方CellProfiler 4.2.8 Human示例（原pipeline不改），退出0、Done Complete、289个核、总9.44秒；这是执行烟测，无准确率/内存结论。见official-smoke.json。已核Kromp数据CC0、完整groundtruth与抽样singlecell区别，按元数据冻结3开发/10评估图，尚未下载这些图或模型权重。下一步隔离StarDist环境、开发组配置与正式冻结。

2026-11-06推进：730dd50在任何选中图下载前冻结分组。仓库外3幅开发图/完整实例GT及5.3MB权重已下载并核SHA；评估图未下载。隔离Python3.12.14、StarDist0.9.2/CSBDeep0.8.2/TensorFlowCPU2.21.0安装完成，首次真实CPU推理成功（组织开发图409核，预测1.20秒；不含启动，不作准确率结论）。CP开发配置真实运行3图成功，CSV计数与原始npy连续标签数逐一一致423/328/868；官方Experiment.csv保存了加载后DateRevision428的完整pipeline，已提取入证据。开发配置尚未最终冻结；下一步三开发图对照、参数冻结、独立进程内存监测及10评估图。无活动安装/下载/推理进程遗留。

冻结评估已完成：1866b47冻结后下载评估图、687e34a补精确记录后10图两方法运行成功，20行匹配结果归档；StarDist平均F1 0.8600/平均计数相对误差11.59%，最差计数误差38.46%；CP所测有限配置过分割明显。实测内存与运行/环境体积齐全。下一步绑定候选独审、CI/PR集成，上游回传尚未完成。

PR65已建立。首轮rules-context 42070466193失败“Integration needs exactly one changed integration context”：b882重载P013时也改了其旧集成清单，导致两份当前清单差异。修复为恢复P013已在main验收的canonical integration-context原文，将本次重载清单完整复制保留于P014/p013-reload-integration-context.json；P013真实重载rules-context及P014历史来源校验保持，不删除回执、不改门禁。此修复独立说明并纳入增量独审。

独审收尾：9ffa327独立逐实例IoU核对20行一致；两项P3文档修正后fd88b76增量复审通过，含历史清单逐字节保留与规则校验。记录见independent-review.md。后续提交仅记录审查/目标审计，不改变被审实验代码/参数/数值。PR65最终远端CI仍待通过，未集成。
