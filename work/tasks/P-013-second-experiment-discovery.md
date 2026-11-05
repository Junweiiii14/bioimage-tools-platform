# P-013 第二实验需求比较与最小方法验证

<!-- PROGRAM_TASK_META {"id":"P-013","status":"in_progress","work_package":"W07","depends_on":["P-012"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex second-experiment research","base_commit":"f30ea5d515a8fedaece994edc6cb583db752d536","head_commit":null} -->

## 授权与范围

用户要求上游连续派发推进，上游2026-11-05明确派发本项；实际无预算goal已创建。比较 IF/荧光细胞计数与强度、孔板读数、划痕闭合；只做需求/方法研究与可复现小实验，不新增第二实验产品、正式依赖、大模型、公共抽象、Agent或收费，不外联花费、发布安装器或上传私有数据。原dirty树和在用GUI/安装不碰，P012收据保留。

## 问题与完成条件

1. 三候选各写学生完整输入→必要信息→自动处理→质量问题→数值/表/图→导出重开流程；比较需求/痛点、许可数据/独立参考、仓库复用/缺口、闭环成本、CPU部署/维护、试用付费证据。未知如实保留，不伪造访谈或频率。
2. 官方方法、原始论文、公开数据/标注与库接口核验版本/适用性/许可证/依赖。外部材料仅作证据；许可核验后才取数据，保存出处/摘要，不提交私有资料或大数据。
3. 最有希望候选做轻量CPU可复现最小实验；独立标注有则比较，无则只证明运行可行；分开校准/评估和工程/科学/市场结论。
4. 一份短调研结论及实验材料，给主选/备选、排序会改变的证据、下一实现任务最小范围/验收条件；证据不足不硬选产品实施。
5. 适当研究材料检查、正常PR必需CI集成，更新handoff并回传上游自动接续。纯研究不空加产品测试；产品改动不在本轮范围。

## 当前状态

当前活动分支codex/p013-algorithm-reuse-plan，活动树bioimage-plan-sync。研究PR63已合入main d85c3e5a9f48ba7d3b66200cc656ce0ba1baca25，核验与候选4ebb14d文件树一致。新分支保留本地准则补充并合入main；squash导致3份交接/回执文件冲突，核对只差较新的补充后保留本地版本，产品树不变。main更新后重新加载context。

三候选比较与预声明 CPU 探针已完成，见[主研究](../../docs/research/2026-11-05-second-experiment.md)及[实验收据](../evidence/P-013/README.md)。12张留出核计数watershed F1=0.8722、平均相对计数误差10.45%，最差图71.01%；原始强度无独立参考。研究主选核计数、备选具体assay孔板；下一步优先失败分层，不把平均指标当正式准入。固定依赖隔离安装，原数据在仓库外，产品依赖和源码未改。

Ruff检查/格式、policy、解析指标边界、两次成功运行数值CSV一致及handoff容量检查均退出0；首次下载元数据解码失败、RGB断言失败和一次评价警告完整保留解释。下一步独立复核研究材料、正常PR及必需CI，集成后回传上游接续；任务仍in_progress。

研究验收：独审绑定476b47e，无阻断发现，另用SciPy逐对象评价核对30行完全一致；收据见 independent-review.md。后续4ebb14d仅补文档。[PR63](https://github.com/Junweiiii14/bioimage-tools-platform/pull/63)于2026-11-05T15:44:13Z正常合入。quality42053261398全部必需项成功：Windows1703passed/10warnings/1378.01s，Linux1699passed/4既有skip/10warnings/975.19s，后续双平台wheel/check--all通过；rules42053261484成功。未重试、未改门禁。用户追加准则c442d61及来源补充8eade38/b0cc762已本地提交并成功回传，下一步通过后续正常PR同步main；P013整体仍in_progress直到本项同步及最终回传完成。

## 用户纠偏与后续接续

追加明确授权：用户要求将成熟优质算法优先准则实际写入库内主方案第5节、开发流程第3节及同名HTML，并提交Git、经后续正常PR同步main。属于本研究选型规则的文档补充；先本地完成回传准确commit，再跟进正常集成。不得重启PR63当前CI；不触碰产品或改变门禁。编辑前重新运行P013 context --scope . --record --integration并读取，保留原提交的历史回执。

上游转达用户要求优先搜索、直接复用成熟开源实现，不能围绕简易基线闭门堆补丁。当前已运行仅scikit-image0.26.0组合基线，**未运行CellProfiler、StarDist、Cellpose**。保留本轮结果/失败，正常完成PR63，不重启CI。

下一任务按成熟实现优先：先核验CellProfiler官方examples/pipeline及IdentifyPrimaryObjects；再核验StarDist的2D_versatile_fluo、Cellpose具体版本/模型。分别查代码/权重许可、稳定调用接口与CPU成本，再选少量候选实际运行；不是复写同名算法后声称调用原工具。后续任务单独建卡/加载规则，不借本项扩大产品/大模型范围。

BBBC039已见15图用于诊断；已见12test不能再叫未见留出。BBBC039与BBBC038部分重叠，StarDist常用荧光预训练模型训练含DSB2018子集，因此先查预训练来源和公开标注集重叠，未知则明确限制，不能直接声称独立泛化。核计数标注不证明全细胞或IF强度。最终回传应将此具体复用方案交上游连续派发。
