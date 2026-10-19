# F-003 最终验证

2026-10-15，Windows/Node26.7.0；本地基线2a72127。本任务没有产品代码修改，T-021既有dirty产品文件保持未提交。

| 验证 | 结果 |
|---|---|
| 项目dev.py policy | 退出0，83产品文件边界与7项技能清单/摘要一致 |
| 两技能来源比较 | 30/63文件与skill-installer固定SHA暂存来源逐字节一致，仅补上游LICENSE |
| Markdown相对引用 | 0缺失 |
| Taste脚本语法与列表 | 7个mjs node --check通过，draw --list sectors退出0/22类 |
| Impeccable引擎 | Windows x64 0.1.14，SHA与GitHub asset digest一致；默认cmd engine-probe退出0 |
| Impeccable context | 隔离空目录退出0，正常报告缺PRODUCT/DESIGN；未编辑实际产品设计或hooks |
| REA6.5.0合成静态样例 | analyze/trace退出0；5个种子27节点34边、coverage partial；篡改Evidence后退出1并明确身份不符 |
| PR #5本地 | 独立分支29测试22.30秒、Ruff/格式/Pyright、环境烟测、rules-context均退出0 |
| PR #5最终远程 | ac75f6f4a84e27b4a709fb048a33a7fcb1e897bc，Windows42秒/Ubuntu13秒/desktop28秒/rules4秒全SUCCESS |
| handoff容量 | changed=0 warnings=0 unresolved=0 |

技能安装没有UI产物，因此未跑网页视觉验收；未执行产品全量425项、产品独审、实际社区项目效率基准或Windows原生Ghidra。REA完整输出/隔离包锁在.local/research，摘要及自有样例随F-003保存。PR #5未合并/发布，main未变；本地技能与维护文档独立保存。

为保持来源字节，Impeccable cmd使用专属LF属性，Windows现有启动烟测已通过。提交前另用Git checkout-index在core.autocrlf=true下还原技能并比较树摘要，实际结果在收尾补记。

## Git保存前复核

- core.autocrlf=true 的 checkout-index 还原两技能，目录hash与实际安装完全一致；LF专属属性已验证。
- git diff --cached --check 在Impeccable上游原文件报告6处空白问题（extract.md末尾空行、harden.md四处、optimize.md一处）；与上游暂存逐字节一致，保留原文，不清理vendor或关闭规则。
- 排除未修改的上游技能内容后，本任务自有文件 diff --check 通过。来源完整性检查policy仍通过；该空白提示不涉及运行行为。
