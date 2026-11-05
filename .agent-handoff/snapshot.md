# 当前恢复入口

当前任务[P015核分割研究适配器](../work/tasks/P-015-nuclei-research-adapter.md)，上游已收到P014验收后明确派发，新goal已实际创建。分支codex/p015-nuclei-research-adapter，起点b6cc389；已查重建卡登记，下一步读取规则/公开契约，复用WorkflowSession接独立nuclei_tool与进程外CPU环境。尚无产品改动，不重启P014实验或CI。

[P014成熟核计数直接调用研究](../work/tasks/P-014-mature-nuclei-methods.md)已完成实验、独审与正常集成，最终证据见[final-delivery](../work/evidence/P-014/final-delivery.md)。PR65 main07838c293390b0ce209b9c1500d49d734bc393a6与候选c86e3db树一致；活动树bioimage-plan-sync已合入main为58ad6c7，原dirty树/GUI/安装不碰。

CP4.2.8与StarDist0.9.2 CPU真实对照、3开发/10评估先冻结、20行指标独审一致。SD平均F1 0.8600/计数相对误差11.59%，最差38.46%；只作研究适配候选，未知训练重叠/患者独立性、16bit/实验室/学生等边界仍保留。

独审fd88b76通过；最终quality42071385491和rules42071385465成功。Windows1703passed/Linux1699passed+4既有skip，两平台wheel及desktop通过。旧质量42070466221已cancelled，不计通过；watch session41138终态exit0，不重启实验或监测。

本轮正式验收已成功回传（工具返回目标threadId、isError=false）；下一步由上游01a19bfd-f3ab-7502-86da-9f61953d1c8a（local）自动接续，用户已明确授权且不等待再次催促。建议最小独立核分割研究适配器，固定模型/参数、进程外执行、原坐标标签、失败/取消/资源边界；不扩展IF强度/全细胞/科学准入或发布。下一任务编号只按上游派发/任务卡，不自行猜测。

P013 PR63/64、P012、P011及T082旧交付/科学与目标环境缺项均保留，见risks/backlog及各final-delivery。P014本地收尾收据与main集成候选区分，下一正常任务带入。
