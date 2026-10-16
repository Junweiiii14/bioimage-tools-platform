# T-035 比例自动裁图闭环

- 状态：implementing；用户批准宽高比1.25*n，不缩放原图；正常图直接拼图，点击回原图、n快速调宽。
- 基线b253e34；范围tools/wb、apps/desktop、tests、docs、work、.agent-handoff、PRODUCT.md、DESIGN.md、.impeccable。
- 仅用户指定1G与2B的_0_11597/_0_26751原图验证，排版/过程图/副本不当自动验收输入。
- 独立原图存储/原值裁图；新策略版本化，旧项目不静默重裁；科学质量与裁图完成分开。
- 现有样式/动效保留；本轮高级功能其他迁移不扩展。
