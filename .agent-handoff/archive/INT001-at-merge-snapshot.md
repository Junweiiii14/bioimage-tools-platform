# Handoff Snapshot

- 当前集成任务唯一状态源：work/tasks/INT-001-e7-governance.md；临时e7-integration工作树，分支codex/e7-integrate-01。此批仅治理，不包含WB产品实现，不把零产品检查写成产品通过。
- 用户授权按E0–E7连续推进。主产品任务T060在t051/codex/wb-e0-e7，E0–E6已完成本机验证/独审；其最终状态请读该树任务，不从此历史基线推断产品尚未开始。
- 本批：原PR7治理0b786cb5，已merge main43d520f（规划PR16），当前准确PR基线43d520f。规则重新加载/阅读，INT001当前scope .，RULE001历史回执保留原0b7不可变来源；显式integration-context无豁免。
- 下一步：治理本地全门禁/负例、绑定当前head独审、快进更新原PR7、四项最终head必需检查后merge集成main。只用merge方法保留来源提交祖先关系，不squash/rebase历史证据。
- 不改服务器ruleset、不删除回执、不伪造成功或降低测试；不修改旧工作树/安装/原图/用户进程。后续P0及产品阶段按真实依赖分别更新当前集成回执和CI。
- 被替换的T050规划快照已先保存archive/INT001-before-integration-snapshot.md；PR16真实已合入main，旧“未合并”是历史文本，不是当前事实。
