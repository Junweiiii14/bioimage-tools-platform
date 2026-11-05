# P014 验收交付

研究及正常集成已完成。[PR65](https://github.com/Junweiiii14/bioimage-tools-platform/pull/65)于2026-11-05 17:35:40 UTC合入main `07838c293390b0ce209b9c1500d49d734bc393a6`；候选`c86e3db4832891d56f33b87178ccdec33bf8c0aa`与合入树`git diff --exit-code`为0。活动树已真实合入main，祖先合并提交58ad6c7；本地收尾记录随后提交，不冒充新产品变更或新CI结果。

## 交付与结论

CellProfiler官方4.2.8/IdentifyPrimaryObjects和StarDist0.9.2公开2D_versatile_fluo真实CPU运行；先冻结3开发/10评估，20行实例指标独立复算一致。代码/权重许可、完整依赖、公开输入摘要、官方实际加载pipeline、运行材料和下一最小范围均见[README](README.md)与[研究报告](../../../docs/research/2026-11-06-mature-nuclei-methods.md)。

StarDist评估逐图平均F1=0.8600、平均计数相对误差11.59%、最差计数误差38.46%，进程12.72秒/采样RSS535.7MB，隔离环境逻辑文件约2.02GB。CP本次有限配置平均F1=0.2155，严重过分割，进程9.58秒/RSS421.6MB。只推荐StarDist作下一研究适配候选，不宣称所有CP管线不适用，不授予科学准入。未知训练像素重叠/患者独立性、真实实验室/学生、16bit范围及跨设备性能仍未证明。

## 独审与必需检查

- 独立只读审查9ffa327：另写逐实例IoU核验20行一致；两项P3文档问题修正后，fd88b76增量复审通过。c86e3db仅新增审查与审计收据，实验源码/参数/数值不变。见[independent-review](independent-review.md)。
- [quality 42071385491](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42071385491)结论success，精确HEAD c86e3db。Windows job127400654748：1703 passed、10 warnings、1402.35秒；Linux job127400654327：1699 passed、4既有平台skip、10 warnings、998.77秒。两平台check --all和独立wheel安装检查通过。
- desktop-environment job127400654038成功；[rules-context 42071385465](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42071385465)成功。四项required checks均SUCCESS，合并前mergeStateStatus=CLEAN。可选native-case未触发而SKIPPED，不计成通过或新的原生验收。
- 首轮rules42070466193失败（两份变化集成清单），保留历史清单且重新加载唯一当前集成清单后修复，未改门禁。旧候选quality42070466221被新候选替代并确认cancelled，不借用旧测试结果。
- 本地研究Ruff、policy、输入/模型SHA、精确规则校验、handoff容量均实际通过；全量产品检查在远端执行，不写成本地通过。监测session41138已退出0，无实验/CI监测进程待恢复。

## 连续接续

用户已明确授权回传并要求上游自动派发下一项。建议下一最小任务：独立核实例分割研究适配器，版本化模型/预处理，进程外CPU执行，原坐标标签/核数/摘要/显式失败，验证取消与资源边界；不接入IF强度、全细胞或自动科学准入，不发布安装器。正式验收已发送指定上游，工具返回threadId且isError=false，任务卡已记录；上游根据主计划与依赖自动接续派发。

原dirty树、原图、历史结果和在用安装保留；本轮无产品包、正式依赖、模型训练、私有上传或付费操作。
