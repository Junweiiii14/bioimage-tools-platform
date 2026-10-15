# 前端技能安装与 REA 调研（2026-10-15）

## 结论

Taste 和 Impeccable 已按固定提交安装到本项目，来源、许可证与目录SHA256进入 tooling/skills-lock.json。当前产品的应用界面优先用 Impeccable 的 Operate 模式；Taste v2 按其声明用于公开网站/宣传页。用户确认 Impact-cable 即 Impeccable。

REA 对 Electron/JavaScript 的开源学习、打包产物与版本差异调查有实际用途；对当前 Python/PySide6 项目的日常维护，源码/测试/契约/独审优先。暂不把 REA 加入产品依赖或全局MCP，仅在 .local/research 中安装固定版CLI做合成样例调研。没有科学准确率、真实社区项目学习效率或原生Ghidra验收结论。

## 固定来源与版本

| 项目 | 实际来源与固定提交 | 状态 |
|---|---|---|
| Taste v2 / design-taste-frontend | [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/f624f37a8c650b9cc550253104925efe4c8de246/skills/taste-skill)，f624f37a8c650b9cc550253104925efe4c8de246 | 项目 .agents/skills/taste-skill；MIT |
| Impeccable / metadata 4.5.2 | [pbakaus/impeccable](https://github.com/pbakaus/impeccable/tree/abf5779cabc20147fd9c013fa4705088c200bf8a/.agents/skills/impeccable)，abf5779cabc20147fd9c013fa4705088c200bf8a | 项目 .agents/skills/impeccable；Apache-2.0 |
| REA 源码 | [morluto/rea](https://github.com/morluto/rea/tree/ce89706145dd98fbaa8df8f062fdc80777136940)，ce89706145dd98fbaa8df8f062fdc80777136940 | 本轮读取该main快照；取代上轮仅记录未下载的fc712b3 |
| REA 实测包 | [rea-agents-6.5.0](https://github.com/morluto/rea/releases/tag/rea-agents-6.5.0)，发布2026-10-14 | npm包6.5.0；实际完整性见rea-probe-summary.json。源码main与发布包分别记录，不假定逐字相同 |

## 技能核验与使用

使用已安装 skill-installer 的 install-skill-from-github.py，先安装到 .local/skill-review 读取SKILL.md及脚本边界，再以同SHA安装到 .agents/skills。两目录分别30/63文件，与暂存来源逐字节一致；仅额外补入各上游根LICENSE，没有改写上游SKILL。

- 所有Markdown相对引用均存在；Taste的7个mjs文件经 node --check 通过，draw --list sectors 正常返回22类。未运行浏览器视觉验收，因为本次只安装，没有网页设计产物。
- Taste要求Node22+，网络素材搜索访问开放素材服务；inspect会启动headless Chromium、保存截图，使用独立临时浏览器profile。其强制动效/图片数量、营销文案规则不适用于Qt科研应用。
- Impeccable技能版本4.5.2与辅助引擎版本0.1.14分开。Windows启动器支持版本缓存、下载旁侧校验。已取[engine-v0.1.14](https://github.com/pbakaus/impeccable/releases/tag/engine-v0.1.14) Windows x64程序，SHA256为`38e09451694973ba664a24e67e1502a6913e6d0e533a0a5ae1e04c5963a804b1`，与GitHub release asset digest一致。
- 引擎保存在用户缓存 `~/.impeccable/bin/0.1.14/impeccable.exe`，不进仓库；默认项目启动器engine-probe返回impeccable-engine 0.1.14。context在隔离的空样例目录运行退出0，正常报告缺PRODUCT/DESIGN；未生成实际产品设计、未启用hooks或pin命令。
- .agents/skills在下次从本仓库启动/继续任务时可发现；当前会话已显式读取。UI任务仍按项目context加载、限定范围。第三方技能的权限/子代理/用户访谈说明不能覆盖当前用户与宿主指令；本轮仅安装验证，不触发设计访谈或子代理。

## REA 能力与成本

以下为一手源码/文档核验，不能推广为所有宿主均实测。

| 能力 | 一手证据 | 对本项目的价值与边界 |
|---|---|---|
| JS/Electron静态重建 | [artifact reconstruction](https://github.com/morluto/rea/blob/ce89706145dd98fbaa8df8f062fdc80777136940/docs/javascript-artifact-reconstruction.md) | 读取目录/ASAR，记录入口、preload、contextBridge、IPC、原生addon；静态路径不执行目标 |
| 功能追踪/版本比较 | [application workflows](https://github.com/morluto/rea/blob/ce89706145dd98fbaa8df8f062fdc80777136940/docs/javascript-application-workflows.md) | 有源码也可用，不必等到完全无源码；精确种子、关系图、source-to-bundle与版本差异。动态调用/别名/编译选项仍可能未知，不证明行为等价 |
| Evidence持久化 | [MCP contracts](https://github.com/morluto/rea/blob/ce89706145dd98fbaa8df8f062fdc80777136940/docs/mcp-contracts.md)、src/domain/evidence.ts | 输入SHA、参数/分析版本、observed/derived/inferred、authority/coverage/limitations及来源位置。摘要认证记录一致性，不认证推断科学正确 |
| Windows原生逆向 | [Windows Ghidra P0](https://github.com/morluto/rea/blob/ce89706145dd98fbaa8df8f062fdc80777136940/docs/windows-ghidra-p0.md) | 实验性Windows10+x64/本地NTFS；Ghidra12.1.x（文档验证12.1.4）与JDK21+；只读PE x86/x64及限定raw6502。非全功能Windows互通证明，本机未装/未测Ghidra |
| .NET静态分析 | [managed guide](https://github.com/morluto/rea/blob/ce89706145dd98fbaa8df8f062fdc80777136940/docs/managed-code-analysis.md) | 独立PE/CLI元数据与CIL提供者，不执行程序集；不等同于Python语义调用图 |
| 运行时/网络观察 | README、DISCLAIMER及各运行指南 | 与静态分析不同，可能运行/连接目标。若实际使用，按具体目标与范围建任务；本轮只用了静态样例 |

Node要求^22.19.0、^24.11.0或>=26；本机Node26.7.0满足。REA自有代码MIT，其他依赖/外部工具遵循各自许可；不因MIT就认为Hopper/IDA许可证包含在内。REA的setup会写客户端配置，本轮未执行setup，也未把其完整工具面常驻加载。

## 本机可复现实验

证据：work/evidence/F-003/rea-probe-summary.json；完整结果和包锁保存在忽略目录 .local/research。可重建的5个样例文件保存在work/evidence/F-003/rea-fixture，共752字节。它们没有科研资料，main.js故意带异常以避免误当可运行应用；REA将其作为惰性文本分析。

准备：在隔离目录用npm install --ignore-scripts --no-audit --no-fund --save-exact rea-agents@6.5.0安装（173包）。调用其scripts/rea.mjs，未全局安装/注册MCP。包锁resolved/integrity保存在摘要。

1. analyze-javascript-application `<样例绝对路径>` --json：退出0；3个JS、115个AST节点、15发现、0解析失败。识别1个BrowserWindow、1个contextBridge API、1个字面IPC通道、main handler和renderer transmission各1，配对1。动态resolve形式preload未解析出入口（0），graph coverage=partial，未伪称完整。
2. 将完整Evidence与seed={kind:string,value:wb:preview}, direction=both写入输入，调用trace-application-feature `<输入JSON>` --json：退出0；5个种子、27节点、34边，coverage仍partial。摘要observed27/inferred35，不把推断当观察；native handoff=0。
3. 只把已保存分析的browser_windows篡改为999，不更新Evidence身份，重试追踪：退出1，invalid_request，明确Evidence semantic identifier does not match its record。

这是小型功能/一致性验证，不是速度基准。完整分析输出234186字节、追踪98817字节，远大于752字节源码；默认全量工具输出对小项目可能增加阅读/上下文成本。主仓库提供summary、分页与保留Evidence接口，但上游效率实验也明确有些场景只减少回复字节，模型token/延迟收益未成立，见[analysis-efficiency](https://github.com/morluto/rea/blob/ce89706145dd98fbaa8df8f062fdc80777136940/experiments/analysis-efficiency/README.md)。本轮不报告“节省多少token/提高多少效率”。

## 采用建议与复核条件

- 自己的Python/Qt平台：保持直接源码、契约测试、独审和故障栈为主。借鉴REA的证据结构与未知状态表达，现有任务/证据可承载，暂不添加新知识库/平台层。
- 学习Electron/JS社区项目：值得按功能试用。固定commit/许可与发布产物SHA→源码粗读→选具体IPC/字符串/API种子→REA静态图→回到源码位置和测试核对→写最小独立复现。以用户关心的问题为界，不要求扫描整个大型仓库。
- 原生Qt/Nuitka产物问题：源码与包态行为确有差异且普通调试不足时，再评估Ghidra试点；不能据反编译恢复函数就认定保留了Python/Qt语义。
- 真正决定长期接入前，在一个实际开源项目做同问题的人工源码路径/REA路径对照，比较已验证结论、遗漏、总时间和上下文成本。该基准是后续采用条件，不是本次已执行事实。REA升级、Windows边界变化、引入新产物类型或实际学习任务出现时重新核验。
