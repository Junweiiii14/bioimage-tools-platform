# P025 首单研究交付

[报告](../../../docs/research/2026-11-09-first-order.md)建议先验证高校 WB 新人带教，最多四人同机、每组试报 1,200 元。已有本机练习材料，尚无真人独立使用、采购、到账、复购或科学准入证据。采购与试用由用户协调。

[PR77](https://github.com/Junweiiii14/bioimage-tools-platform/pull/77) 正常 squash 合入 main e846a681c85e04d53904fe8b6b384376e98f6032，与准确候选 472247f783d3f80adc116599b02302f8baf71125 完整树 diff exit 0。原 base 4d3c3fa7cb8df1a1ae00f7a7c2c34b392817626f。首审 6868040 的 [R01](independent/independent-review-6868040.md) 修复后，[固定增量独审](independent/independent-review-472247f.md) pass；报告从 3b259b5 起未变。

最终提交 [quality](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42505116610) 和 [rules-context](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42505116760) 的四项必需 CI 全部成功；native-case 条件未触发。旧 head 的 quality 被新提交取消。全局 check_plan.py 的既有首错为 P010；基线与最终缺项相同，新增零项。作者只做来源、算术、规则和交接检查，未重跑本机产品或科学测试。仅归档收尾随下次正常 PR 带入，不另推收据或触发新研发任务。
