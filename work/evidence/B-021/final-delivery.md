# B021 最终交付

2026-11-06完成用户要求的共同审查方案与窗口闭环。[PR69](https://github.com/Junweiiii14/bioimage-tools-platform/pull/69)于05:45:22Z正常合入main `dc2609dd79de98a63d4e8283e6c6db9e7c8e28ba`；上游最终交叉核对的候选为`ebe7aaa0a46bfd6e4485a5f3bcbcab0a0bde768d`，两者文件树diff exit0。

[共同方案](../../../docs/plans/independent-review.md)将实验可插拔、独立算法与统一科学契约、友好可视化保存复用、自研简洁小体量、上游算法原件保护映射为分阶段验证。普通实验向导与专业节点画布共用算法、执行和结果；不把研究MVP冒称终局完成，不要求研究任务反复重跑完整插件矩阵。AGENTS和ai-workflow已挂入口。

工作闭环固定为上游派新开发窗口→作者自验候选→上游调用本独审窗口→结果回上游→原开发窗修复/增量复审或正常集成→释放树→下一新任务新窗口。用户授权的调用与回传已实际使用；这不是新后台监听服务。P017研究独审及收尾已完成，P018研究内容审查已回传，后者的集成清单与正式PR仍待其开发窗口完成，不在本任务冒称通过。

准确候选四项必需检查全部成功：[quality 42168074979](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42168074979)含Windows1737 passed、Linux1733 passed/4既有skip、双平台完整check --all及wheel烟测、desktop-environment；[rules 42168074980](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42168074980)成功。native-case为既有条件skip。policy/context/链接/diff/handoff等本地文档检查见[验证](validation.md)，上游准确文稿交叉核对见[协商](agreement.md)。没有修改产品、第三方算法、依赖、容差或门禁；没有替换用户安装。

方案、main与CI已用聊天工具回传上游`01a19bfd-f3ab-7502-86da-9f61953d1c8a`，上游确认接收并通知P018合主线、重载规则及修复历史回执清单。本审查树仅补本地完成记录，不重新推送触发CI；后续正常任务采用必要完成文档，不覆盖更晚产品指针，也不改写历史加载/验证对象。共享开发树全程未写，本树不派发下一产品任务。

产品全局可插拔、所有算法节点覆盖、友好度真人比较及科学/目标机验收尚未由本方案完成；具体能力按各任务证据判断。已有GPU/科学/用户安装限制原样保留。
