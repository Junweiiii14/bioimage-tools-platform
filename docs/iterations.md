# WB迭代与证据导航

当前总任务是 [T063采集组交付](../work/tasks/T-063-grouped-intake-delivery-plan.md)，完整授权范围与验收见 [P0–P8计划](wb-grouped-intake-plan.md)。[GitHub交付跟踪 #25](https://github.com/Junweiiii14/bioimage-tools-platform/issues/25) 和 [离线测试版里程碑](https://github.com/Junweiiii14/bioimage-tools-platform/milestone/1) 汇总进展；任务文件仍是状态来源。这里的历史通过不代表当前候选已交付。

| 迭代 | 可观察结果与契约 | 实施/审查证据及集成 |
|---|---|---|
| 原E0–E7 | 清单→固定N裁剪→完整Fig→原像素定量→身份填表/新目录输出/恢复 | [验收索引](wb-execution-acceptance.md)、[T060](../work/tasks/T-060-integration-installation-acceptance.md)；原910项与旧安装候选为当时工程证据 |
| T061 | 仪器导出角色、条带/N未确认建议 | [识别契约](contracts/wb-export-discovery-v1.md)、[T061证据](../work/evidence/T-061/validation.md)，PR19已合 |
| T063/P0 | 专用工作树、需求/任务/验收映射 | [完整计划](wb-grouped-intake-plan.md)，PR21已合；历史dirty与原图保持 |
| T064/P1/P2 | 采集组草稿、唯一Fig级N、稳定行/源/槽位，批准网格 | [分组契约](contracts/wb-intake-grouping-v1.md)、[独审](../work/evidence/T-064/independent-review.md)，[PR22](https://github.com/Junweiiii14/bioimage-tools-platform/pull/22)已四检查合main |
| T065/P3 | 目标候选与原坐标框，已完成裁剪的新修订/定向失效 | [修订契约](contracts/wb-intake-revision-v1.md)、[独审](../work/evidence/T-065/independent-review.md)、[CI原始失败与最终结果](../work/evidence/T-065/pr23-ci.md)，[PR23](https://github.com/Junweiiii14/bioimage-tools-platform/pull/23)已合main e842c6c |
| T066/P4 | 统一21动作、配置/冲突/默认/持久化、输入/IME/弹窗保护 | [快捷键契约](contracts/workbench-shortcuts-v1.md)、[独审](../work/evidence/T-066/independent-review.md)，[PR24](https://github.com/Junweiiii14/bioimage-tools-platform/pull/24)检查/集成以任务为准 |
| T067/P1/P3补齐 | 执行后未知N/未选源草稿、失效矩阵、数值请求全等才复用真实run | [分组修订契约](contracts/wb-intake-group-revision-v1.md)、[任务](../work/tasks/T-067-intake-group-revisions.md)、[独审](../work/evidence/T-067/independent-review.md)，已接受1211d70，后继PR待前置集成 |
| T068/P5/P6 | 算法消费者/版本清单、仓库导航、依赖分流 | [算法清单](wb-algorithm-inventory.md)、[任务](../work/tasks/T-068-wb-algorithm-inventory.md)，不为了删行改变数值或删除兼容能力 |
| P7/P8 | 三目录正式整链含人工修正/失效/重开，一次最终本地全门禁，冻结离线安装双流程/SHA/manifest | 本轮新候选尚未交付，以T063及后继交付任务真实证据更新；干净Win10/物理DPI/独立科学真值仍未验 |

## 数据与检查边界

仅本轮指定三目录95 TIFF/76唯一内容、19个三图采集组/19唯一参考；验证目录参考与另两目录重复，不充当独立留出。N建议、来源角色和正式蛋白名称仍需按原图证据核对，不靠文件编号或同名蛋白猜配。原图、已完成项目/结果、初始PDF及旧工作树未提交改动不覆盖。

普通开发先定向检查，最终冻结候选本地完整 `uv run --locked --no-sync python dev.py check --all` 一次；服务器每个待合PR仍照常跑必需检查。930/910等历史数量不自动套用新版本。完整通过需原进程成功退出及隔离wheel/OCR完成，不只看pytest摘要；旧原生UNKNOWN保留。

## 仓库与依赖分流

2026-10-20核验：公开仓库默认main，About已说明Windows本地WB测试工作台；26个远端分支，未删任何分支/标签/发布/工作树。历史 [开发日志 #6](https://github.com/Junweiiii14/bioimage-tools-platform/issues/6) 保留其2026-10-17时点，当前产品已有分阶段PR集成，不能据旧日志判定main仍未含产品。

| 独立依赖PR | 实际diff/现有证据 | 本轮处置 |
|---|---|---|
| [#4 checkout 6.1.0→7.0.1](https://github.com/Junweiiii14/bioimage-tools-platform/pull/4) | 两workflow共3处固定SHA更换；当前head1fbdeb7三产品检查成功、rules-context失败，且基线需更新 | 保留独立升级；不因产品检查绿而豁免回执/独立依赖审查，不混进本交付 |
| [#5 setup-uv固定SHA更新](https://github.com/Junweiiii14/bioimage-tools-platform/pull/5) | head ac75f6f含2处workflow SHA及旧F004回执/交接；2026-10-15四检查通过是当时治理基线/29项，不能替代当前产品验证 | 保留历史修复证据，当前需重新核验基线、上游固定提交、规则和实际差异；不把旧snapshot带回当前状态，不自动合并 |
| [#20 uv-build 0.13.0→0.13.1](https://github.com/Junweiiii14/bioimage-tools-platform/pull/20) | 4个成员build-system requires变化，非纯文字/运行时无关；当前依赖/锁定环境仍0.13.0 | 单独构建供应链变更，须独立wheel/manifest/锁定一致性验证与回执；本轮冻结保持0.13.0，不搭车升级 |

这些是本轮范围决定，不是对上游版本安全性或优劣的结论。未给机器人豁免、降低保护、改成功状态或触发自动合并。当前功能分支保留可审差异，历史分支保留来源；归档/回收只处理已明确授权且新交付已验证的对象。
