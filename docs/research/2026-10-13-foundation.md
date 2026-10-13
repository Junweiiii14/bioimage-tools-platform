# 长期代码库规划与技术调研

调研日期：2026-10-13。对象为初始 V3.0 PDF 和空产品仓库。以下“采用”指治理设计或当前环境选择，不能外推为产品功能已经实现。

## 结论

继续采用 Python/PySide6、独立 worker、单仓库分包的候选方案。专业性来自可检查的边界、真实数据语义、可复现的环境和可回滚的变更，而不是工具数量。当前先建立治理、环境和审查入口；P0 仍负责验证 GUI、原生库、worker 与安装包，之后才冻结产品技术栈。

## 调研问题与落地决策

| 问题 | 核验与取舍 | 落地 |
|---|---|---|
| 单仓还是多仓 | 目前工具随产品发布、开发者/代理共享变更上下文，单仓便于接口原子变更；无需额外跨仓版本协调 | uv workspace、一个锁文件，成员按真实边界创建 |
| workspace 是否隔离 import | uv 提供依赖解析与共享环境，不阻止 Python 的越界导入 | 直接 AST 检查先落地；真实包再加 import-linter 与独立 wheel 安装测试 |
| 纯 Python 是否足够维护 | 同语言减少桥接，仍需类型和进程边界 | Ruff＋Pyright strict；domain/application/adapters/ui 分离 |
| PySide6 打包是否已证明 | 官方 pyside6-deploy 包装 Nuitka；环境能导入 Qt 不等于安装包可运行 | P0 编译、目录包、无 Python 目标机验证 |
| 哪个 Python | 原方案 3.12 为候选；3.12 已处安全维护期，预计 2028-10 结束 | 现在固定 3.12.14；P0 评估更新受支持版本的 wheel/构建后决定长期产品基线 |
| 怎样管 AI 长期上下文 | AGENTS 按路径发现，skills 按需加载；大量全局技能会挤占发现信息预算 | 约 4 KiB 根 AGENTS，项目技能＋短交接入口，详细文档按任务读 |
| 怎样判断 AI 代码正确 | 工具执行结果、独立预期、故障注入和绑定 SHA 的审查可证伪错误 | 任务模板、数值规则、正反例测试、CI；不许以自评替代证据 |
| GitHub 保护是否已生效 | API 实测私有仓库 rulesets 返回套餐限制 403 | 保持私有，提交待导入模板；当前无法宣称服务器强制保护 |
| “稳定快速”如何兑现 | 单次安装不能证明长期稳定；无端到端产品基准不能承诺性能 | 固定依赖、增量检查/全量 CI、分层验证；记录当前实测和剩余缺口 |

## 后续代码库形态

```text
根：AGENTS / README / pyproject / uv.lock / dev.py
apps/                    一个发布应用，desktop 与 worker 装配入口（规划）
packages/                contracts、runtime、desktop SDK、imaging（规划）
tools/                   WB → IF intensity → count / IHC，按阶段创建（规划）
tests/                   当前门禁测试；未来 contract/integration/packaging
docs/                    架构、代码规范、契约、ADR、运行手册
work/tasks + evidence/   任务唯一状态与可追溯验证
.agent-handoff/          短状态、指针、决策与风险
.agents/skills/          本项目用到的固定提交技能
.github/                 CI、依赖更新、PR 模板和归属
```

每个真实包有公开 API、职责、依赖、版本和独立安装测试。apps 的装配决定具体工具，runtime 只处理通用机制。公开包 API 只通过 api.py 使用；不能通过把文件拆小但互传大字典来假装模块化。

## 质量与发布门禁分层

每个提交先跑格式、静态、类型和基础边界；算法改变增加解析/性质/冻结样例；契约改变覆盖全部消费者及历史格式；进程/存储改变做真实进程与故障注入；界面改变做 Qt 交互及真实 DPI；发布验证干净目标机、worker 路径、可写目录、备份恢复。

CI Windows＋Linux 的基础检查用于揭示路径、大小写和环境耦合；Windows 的桌面依赖烟测只验证目标平台依赖。Linux 基础检查通过不表示产品支持 Linux。未来安装包基准须绑定硬件、数据集、版本、p50/p95 和峰值内存。当前 16 GB 主机先单计算任务准入，再决定并发。

## 科学计算与数据长期性

结果必须记录输入摘要、参数快照、源 revision、算法/模型/依赖版本、单位和随机种子。原始图像不可变；预览渲染与定量不共享可被修改的数组。WB 积分、IF 强度、计数、IHC 分母是各工具语义，不能在平台抽象成一个无说明数值。

结果文件与 SQLite 采用明确的提交顺序及重启恢复，因为它们不是一个事务。版本迁移先备份并在副本验证；代码回退不能代替数据恢复。原方案中的数值定义是待冻结的参考，旧软件输出不单独证明科学正确性。

## Codex 具体检查结论

本机桌面版 26.1007.21434/build 13901，配置渠道 prod；内置更新检查返回 up_to_date。伴随 CLI 为 0.162.0-alpha.17.2，属于应用管理的运行时，没有额外安装另一套 Codex CLI。账户通过 ChatGPT 登录。

现有用户配置模型 gpt-6.1-sol、默认推理 low；这不是本对话实际模型或配额的独立证明。项目配置只设 medium 默认，模型与费用档位保持用户选择。没有通过非官方补丁解锁速度，也没有开启实验特性来声称更快。

本会话实际可用：PowerShell/Git、文件编辑、官方文档 MCP、Web 调研、技能发现、GitHub CLI。worktree、多代理、浏览器等有工具/运行时支持，但此次没有验证其端到端可靠性，也没有因此启动业务开发或新的代理。

用户配置的 Windows sandbox=elevated；当前会话由宿主授予 full access、approval never。二者不能混为一谈，项目配置没有更改宿主权限策略。全局技能较多（包括 Ark 系列），本次未擅自移除；新增技能只作用于本项目。

## 一手来源

- [uv workspaces](https://docs.astral.sh/uv/concepts/projects/workspaces/)：同仓分包与共享锁文件、环境限制。
- [Python 生命周期](https://devguide.python.org/versions/)：支持窗口。
- [Qt 官方部署工具](https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html)：构建链与部署约束。
- [Import Linter](https://import-linter.readthedocs.io/en/stable/)：导入合约能力，不自动生成本项目规则。
- [pytest 项目实践](https://docs.pytest.org/en/stable/explanation/goodpractices.html)：src 布局与安装验证。
- [Codex 项目指令](https://developers.openai.com/codex/guides/agents-md)：发现路径、覆盖顺序与大小预算。
- [Codex skills](https://developers.openai.com/codex/skills)：按需加载、项目作用域与发现预算。
- [Codex 配置](https://developers.openai.com/codex/config-basic)：项目优先级、信任前提与功能成熟度。
- [GitHub rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)：权限及套餐适用性。

架构取舍和流程是基于这些能力与原方案所作的项目决策；来源不构成对本项目已实现或绝不出错的保证。
