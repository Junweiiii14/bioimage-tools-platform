# 当前恢复入口

本审查树当前任务为 `work/tasks/B-021-continuous-independent-review.md`，唯一状态以任务卡为准。工作树 `bioimage-independent-review`、分支 `codex/b021-independent-review`；持续独审协议见 `docs/plans/independent-review.md`。上游已核对方案，PR69待最终增量交叉核对、必需CI与正常集成，再回传“规划”窗口使用；方案落库不等于产品全局合规通过。

产品开发由上游另开窗口，活动树 `bioimage-plan-sync` 已登记 `work/tasks/P-018-bca-method-contract.md`，该未集成任务卡不复制到审查树。恢复产品开发须读取活动树实际任务和最新上游派发，不把本快照当作任务授权或状态副本。本审查树不编辑活动树、旧dirty树、用户安装或原图。

P017 BCA孔板研究已完成：任务 `work/tasks/P-017-endpoint-assay-research.md`，交付 `work/evidence/P-017/final-delivery.md`。指定独审及纯文档增量pass，PR68候选b2eaccd与main f8f69b5文件树相同，必需双平台CI成功。B021按白名单采用本地0d134的完成事实，保留main上的P017历史回执；来源及检查见 `work/evidence/B-021/validation.md`。此前P016已完成PR67/main6bd4680，B020主方案及HTML已随PR68集成。

P017真实42孔/6样本参考与SciPy+statsmodels直接调用一致，但18技术孔均低于原软件计算LoQ，3/10uL体积与空白身份未获SOP验证；不能把软件复现或未外推当科学通过。R全流程、独立化学真值、学生需求、安装及目标机未验；既有科学/训练重叠/患者独立性/16bit/Linux真实模型/旧GPU限制保留。

主方案 `docs/plans/research-platform-rd.md` 第11节规定MVP先行、当前小批次后集中统一前端与既有P009图形编排，资料不足不无限推迟统一。分别报告工程MVP、统一交互、源码候选、用户安装更新及科学/真人试用。新任务由上游另开开发窗口，同一任务修复/复审回原窗口。第三方算法本体、权重、冻结参考不改；自有胶水可修，方法参数变化须版本化重验。简洁、小体量优先，真实外部边界校验一次，不添加臆测fallback或重复包装。普通已授权步骤继续，不要求用户重复批准。
