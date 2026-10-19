# F-003：长期维护规划、前端技能与 REA 评估

- 状态：done
- base commit：2a72127（本地产品分支）；T-021全部未提交改动保留。
- 用户2026-10-15授权继续技能安装、REA调研、PR #5修复并验证通过。
- 范围：docs、work/tasks/F-003*、work/evidence/F-003、tooling/skills-lock.json、.agents/skills、.gitattributes（仅新增技能cmd的LF固定）及交接。
- 规则：已加载F-003 scope .回执；不改科学语义、不降低门禁、不混入T-021产品内容。

## 完成内容

1. docs/maintenance-plan.md补全维护责任/优先级/触发/证据，并接入ai-workflow。
2. Taste v2、Impeccable4.5.2通过skill-installer固定SHA安装，许可证/目录hash入锁；Impeccable引擎0.1.14另锁Windows x64 SHA并安装用户版本缓存。
3. REA源码/官方文档核验完成；隔离CLI6.5.0静态Electron样例分析、功能追踪、篡改Evidence拒绝实测完成。结论与来源见docs/research/2026-10-15-maintenance-skills-rea.md。
4. PR #5在独立目录F-004补任务/唯一规则回执。最终ac75f6f4a84e27b4a709fb048a33a7fcb1e897bc四项CI SUCCESS，PR OPEN/CLEAN；未合并/发布。

## 验证与边界

- 项目policy退出0；技能30/63文件与来源逐字节一致，仅补上游LICENSE；Markdown相对引用无缺失。
- Taste7个mjs语法检查及22类方向列表通过；Impeccable发布SHA256、默认启动器engine-probe、隔离context通过。
- 新增Impeccable cmd在.gitattributes固定LF，避免全局cmd CRLF策略令跨平台技能hash失配；当前Windows已验证LF cmd可执行。
- REA分析/追踪退出0，5个种子27节点34边；coverage partial；篡改摘要后退出1并报告Evidence身份不符。无原生Ghidra或实际社区项目速度基准结论。
- PR分支本地29测试/22.30秒及环境烟测通过，rules-context通过；最终远程Windows42秒、Ubuntu13秒、desktop28秒、规则4秒全SUCCESS。
- 本轮没有产品代码修改，未重跑产品425项测试或产品独审；PR分支的0产品文件不能外推产品验收。

## 回滚及下一步

回退F-003本地治理提交即可撤销项目技能/文档/锁项；用户缓存二进制与.local研究产物为本地工具，不是产品依赖。F-004回退经PR处理，不强推。前端技能下轮本仓库会话可发现；当前没有UI改版任务或REA常驻MCP。回到T-021及maintenance-plan已有验收/独审缺口，不启动新工具。
