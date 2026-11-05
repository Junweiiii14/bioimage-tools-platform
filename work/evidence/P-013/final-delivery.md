# P013 最终验收与接续

2026-11-06（北京时间）。完成第二实验候选研究及可复现CPU探针，未新增第二实验产品。用户追加的成熟算法复用准则已写入正式MD/同名HTML并同步main。

## 已集成与验证

- [PR63](https://github.com/Junweiiii14/bioimage-tools-platform/pull/63)：研究候选4ebb14d17262f704cc7464a70e015e334a955aff正常合入d85c3e5a9f48ba7d3b66200cc656ce0ba1baca25，fetch核验文件树一致。探针独审绑定476b47e，另一评价实现复核30行计数/匹配一致，无阻断发现。
- [PR64](https://github.com/Junweiiii14/bioimage-tools-platform/pull/64)：准则候选887fd536800c4657a267d09d8ca5f6a2f3ffc4bd于2026-11-05T16:15:41Z正常合入cddf759d20368f10e3ea1d447503dcc3cf3740ea；fetch核验完整文件树一致，并从origin/main读回主方案/开发流程关键条款。两份HTML也在相同树内。
- PR63 quality42053261398：Windows1703passed/10warnings/1378.01s；Linux1699passed/4既有skip/10warnings/975.19s。PR64 quality42058419612：Windows1703passed/10warnings/1480.53s；Linux1699passed/4既有skip/10warnings/939.54s。四个job后续独立wheel及check--all均通过，两PR各自rules/desktop成功。native-case仅非默认诊断job按原规则skip。没有重试、改门禁或测试预期；未重启PR63来塞入新增准则。
- 本地研究：15图CPU运行、两次成功CSV逐字节一致、解析评价边界、Ruff/格式、policy、context、HTML构建和关键文本/链接、22本地链接存在性、handoff容量均通过。首次资源分叉读取失败、RGB/RGBA断言失败和除法警告修正保留在README/experiment-plan。未额外跑本机产品全量。
- 对比f30ea5d与cddf759，apps/packages/tools、正式pyproject/uv.lock及.github无差异。原dirty树、私有原图、旧安装/GUI未动，P012收据已完整带入PR63。

## 结论和限制

[主研究](../../../docs/research/2026-11-05-second-experiment.md)比较三种学生完整任务、证据/许可、复用及部署代价；研究主选2D荧光核计数，备选明确assay的孔板终点处理。真实学生频率、试用与付费意愿UNKNOWN，未假造访谈。划痕代码再分发许可及独立时序参考尚不明确。

实际只运行scikit-image0.26.0固定基线，**没有运行CellProfiler/StarDist/Cellpose**。BBBC039v1公开CC0人工核标注，3张validation+12张test；分水岭test micro F1=0.8722、平均相对计数误差10.45%，最差图69核只计20核（71.01%误差）。这说明需要成熟实现对照，不能授予正式科学准入。原始ADU测量无独立强度参考；核计数不证明全细胞/IF蛋白表达。预声明与结果同一Git提交，不能仅靠Git独立证明时间顺序。

## 上游下一步

按用户要求连续接续，下一任务优先实际调用成熟实现，不继续为简易基线堆补丁：先CellProfiler官方示例pipeline/IdentifyPrimaryObjects（已核4.2.8 CLI与许可，BBBC039也附旧参考pipeline），再按具体版本/代码和权重许可/CPU代价选择少量StarDist或Cellpose候选。实际调用和仅检索的方案分开报告，先查预训练数据及标注集重叠，再冻结未见留出；已见12test仅作诊断，BBBC038/039/DSB2018关系不能忽略。具体入口与未决项见[plan-amendment](plan-amendment.md)。

准则正式位置：主方案第5节 `docs/plans/research-platform-rd.md/.html`、开发流程第3节 `docs/plans/workflow-development.md/.html`。适用于后续所有实验模块及算法研发Agent；不增加审批表或逐节点用户确认。保留科学/学生/目标机旧缺项，不因本研究关闭。

上游目标：01a19bfd-f3ab-7502-86da-9f61953d1c8a（local）。本文件为最终回传依据，交接发送结果在任务卡记录。合入后状态收据本地提交随下一正常任务带入，不为更新“已合入”再重复开PR。

最终送达确认：send_message_to_thread返回目标threadId且isError=false，正式验收、main提交、验证证据、未验边界和下一成熟实现任务范围均已送达。任务与snapshot已记录，不再停在“待回传”。
