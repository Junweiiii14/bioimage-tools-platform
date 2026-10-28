# 最终交接冷启动与小变更

2026-10-28，`/root/final_cold_start` 以空对话上下文仅获得仓库路径和一个低影响事实修正范围，按根AGENTS/交接索引恢复T082。起止HEAD均 `ed830e1d3bab3d0c8c57f3766a898991e8a0f431`，观察到Root正在整理交接的dirty文件，未把未提交文档当作新构建或已完成目标。

准确恢复：任务in-progress/最后交接待独审；冻结源码、完整门禁及实际构建均ed830e1，后续文档HEAD不同；恢复最终5c493…安装器、384432982B、持久短路径及已卸载的独立acceptance身份，173文件/设置/Laboratory保护、残留1274缓存+26合成用户文件；区分在用T081正式实验室交付。恢复科学材料/负责人标准、外部设备/物理DPI等未验与native/GPU/Temp删除UNKNOWN，以及R09/R12有据暂缓。没有重新读取安装器/注册表或将恢复信息当作新安装验证。

实际只修改 `docs/ai-workflow.md:31` 一行：原“冷启动测试尚未执行”改为已有T082独立冷启动**恢复核验**并链接原R08证据；保留“新会话仅凭仓库完成一次小变更”的里程碑要求。原R08确是只读恢复，不被回填为当时有小变更；本次才完成一行修正。同时发现README首段“尚未构建交付”将可弃验收构建与正式交付混淆，报告给Root，由Root单独修正。其余并发dirty内容保持。

`dev.py context --task T-082 --scope .` 两次exit0、不加--record，第一次工具输出截断，第二次保存内存并分片补读完整输出；未冒称截断部分已读。`git diff --check -- docs/ai-workflow.md` exit0，实际diff/正文回读一致。未运行产品、测试、构建、安装或远端操作，也未commit。Root随后对规则变动真实刷新scope .回执并读取变化。

阅读口径：去重完整文件版本的磁盘字节16份71958B（当前AGENTS/索引/snapshot/risks/backlog/模块图/任务/ai-workflow/architecture/coding-standards/research-protocol/rule-enforcement/R08证据/final-handoff/r11-execution/修正前README）；另有4份main旧规则22152B、skill及quality16119B。validation只按rg命中28行/9837B读取，不声称全文。第二次完整context输出72605 UTF8B含重复当前/旧规则，不能与去重字节或R08冻结前后21.7%比较口径混用。

这是恢复与一个受限事实修改的实际记录，不替代最终交接提交的独立审查，也不改变科学/目标机未验结论。
