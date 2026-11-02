# B-011 M1/M2依赖拆分与可运行交付任务登记

状态：in_review，2026-11-02。仅做接续准备，不将计划当作实施。

用户已授权M0→M1→M2持续实际研发。依据4.0总方案12.3/12.4/12.9及phase-2-workflow-authoring.md，保留P001 done及P002原有范围。P002尚待PR48当前HEAD必需CI与正常集成；本任务可先准备planned任务，产品实施须按依赖就绪启动。

范围：P002实际集成收尾及其证据、work/tasks/P-003至P-009、registry、phase-2接续说明、相应规则回执与handoff。P004科学资产基础与WB几何方法拆开；保留其原P002/P003依赖，增加窄契约依赖。P005保留真实串行可靠执行标准；另拆有限批量/依赖复用及M2节点编排，不扩实验、Agent、安装器发布、数据上传、外联或花费。

验收：每张新增卡有可观察产物、依赖、实际API/worker/Workspace复用、错误反例、准确提交独审和集成要求；registry检查通过，无依赖环、不提前激活。既有科学/现场缺项保留。此治理准备须在后续独立PR审查集成，不能夹到已送审P002。

当前下一步：真实context，核对现有P003–006及主方案，再登记planned任务。P002未集成前不启动依赖它的产品代码。

## 准备与预审

已准备P007最小科学/图契约、P008有限批量M1、P009可视编排M2，全部planned；P004/P005保持原依赖并增加P007，registry为14工作包。只读预审指出P004 ScientificAsset职责重复及P005/P008依赖重算边界歧义，已分别改为消费P007、单图可靠性由P005完成/多样本扩展复用同一实现由P008完成。未提交预审不算最终独审。读取workspace发现仍声称T072为当前树，已先原字节归档再更新为实际产品根。P002当前PR与候选未夹入这些工作区准备改动。

## 准确提交预审

本地分支codex/m1-workflow-foundation，规划提交7dac55da13cc2238a3c0538630f037830bd5d13b；未推送且未进入PR48。非作者p002_independent_review对a69b38e..7dac55d规划内容Accepted，实际policy/planchecker/diffcheck及归档/无产品差异核验exit0；workspace归档SHA256=f70b4606718f4f1b25e04b9f63322373a70c23c89c7ea2b9dccf3f6d1140fd8f。提醒snapshot的“未提交”已失效，现已纠正。当前回执仍为旧main299，PR48合入后须真实新基线重载及最终增量审查，不提前宣告本任务集成完成。

## P002集成后重载

PR48已正常合main f2dc5ad44fba2e4f951b8987f0babb6b41c1d1a2，四必需CI通过、合并树等于独审候选；P002按真实收据done。当前分支合入origin/main得到75c502866c49f714451c21b7a55aeb67f88a6962后，已真实执行B011 context --scope . --base f2dc5ad... --record并重读规则。旧main回执版本保留在7dac55d历史；新回执正常刷新，待准确增量审查。
