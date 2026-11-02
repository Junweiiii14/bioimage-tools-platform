# 研发方案4.2（待接入草案）

新版方案已整理到独立GitHub分支，尚未合入main或下发当前开发窗口。优先阅读[接入评估与时机](v42-adoption-assessment.md)。

- [研发总方案](research-platform-rd.md) / [HTML](research-platform-rd.html)
- [真实操作到自动化模块](workflow-development.md) / [HTML](workflow-development.html)
- [长期维护与人工代码审查](../maintenance-plan.md) / [HTML](../maintenance-plan.html)
- [WB真实流程研究与已有模块对照](../research/2026-11-02-wb-workflow-audit.md) / [HTML](../research/2026-11-02-wb-workflow-audit.html)
- [后续实验路线](experiment-research-roadmap.md) / [HTML](experiment-research-roadmap.html)
- [工程规范待接入文本](v42-engineering-proposals.md)
- [4.0原文](research-platform-reference-v4.md)、[4.1原文](research-platform-reference-v4.1.md)

4.2渲染：在renderer目录使用既有锁文件npm ci，再node build-v42.cjs。旧build.mjs仍为4.0版本构建器；接入4.2时一并切换文档命令，不能用旧脚本覆盖新版HTML。任务状态以实际开发树最新任务卡为准。
