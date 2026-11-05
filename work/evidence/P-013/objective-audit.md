# P013 完成审计

本表按原任务及用户追加要求核验。研究候选4ebb14d（探针独审476b47e）；文档准则c442d61及后续来源补充8eade38/b0cc762，最终准则候选887fd53。两个PR已正常集成，详见final-delivery；goal在最终回传成功后关闭。

| 要求 | 当前权威证据及结论 |
|---|---|
| 三类学生完整任务与需求/成本比较 | `docs/research/2026-11-05-second-experiment.md`：输入、身份、自动步骤、质量、表图、保存重开逐候选列明；需求频率/试用/付款UNKNOWN，不冒充访谈 |
| 权威方法/许可/版本 | 同文链接官方数据、库、原始论文；BBBC039v1 CC0；scikit-image0.26.0及plater1.0.5固定来源，划痕代码许可未定且未采用；补充成熟候选真实调用入口在plan-amendment，明确未运行 |
| 仓库复用与边界 | 公开api.py/模块README已核对；只复用通用资产/执行/存储设计，不调用WB内部；本轮无产品源码/正式依赖/门禁变化 |
| 轻量CPU实验及独立参考 | probe.py、requirements、官方ZIP/选图摘要、report/metrics、experiment-plan；Windows真实15图执行，作者人工核标注；原强度仅演示无独立真值 |
| 结果可复现与失败保留 | README记录两次成功CSV摘要一致；失败图69→20保留；RGB断言/资源分叉读取失败及除法警告修正均记录，不修改参数追逐test |
| 独立复核 | independent-review绑定476b47e，独立逐对象交并比实现核对30行完全一致；预声明时间不能仅由同一Git提交证明的限制保留 |
| 主选/备选与下一范围/验收 | 主研究后半及任务纠偏：核计数研究主选，具体assay孔板备选；下一项成熟实现真实调用，训练重叠先查，不继续堆简易基线；产品切片和科学/学生缺项分别列明 |
| 用户要求写入正式方案/HTML | c442d61修改主方案第5节、开发流程第3节及同名HTML，build/文本链接检查/policy/钩子通过；PR64候选887fd53已合入cddf759，fetch全树比较一致并读回main关键条款，已证明远端同步 |
| 正常PR与必需CI | PR63固定4ebb14d正常合入d85c3e5，文件树相同；rules-context及desktop成功；Linux job127334704390实际1699passed/4既有skip/10warnings/975.19s；Windows job127334704893实际1703passed/10warnings/1378.01s；后续双平台wheel/check--all通过，无重试/门禁变化 |
| 历史/授权保护 | P012最终收据完整携带；原dirty树、原图、旧安装与GUI未动；下载仅公开CC0图，不含私有上传/外联/花费/产品发布 |
| 最终交接回传 | 阶段进度及本地/远端提交已成功回传；任务/handoff已更新并归档旧快照，最终交付与下一成熟实现方案见final-delivery；最后发送结果以任务卡回执为准 |

当前结论：研究与准则同步均有准确提交、独审/检查及main树验证证据。PR64 quality42058419612 Windows1703passed、Linux1699passed/4既有skip及后续wheel/check--all全通过，rules/desktop成功，未重试或改门禁。仅最终交接发送回执须在关闭goal前确认。研究完成不关闭科学、学生试用或目标机未验边界。
