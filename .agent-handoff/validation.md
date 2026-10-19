# Validation History

2026-10-14 T-002：最终本地 35 passed（27.22s），Ruff/Pyright strict 通过；standalone 与 ZIP 哈希通过；包态基准 exit 0，20 图整批中位数 21.819s、worker RSS 峰值 257.855MiB。源码原生 UI 通过；包态 UI 因用户 Esc 停止而未验收，不能推断通过。完整证据在 work/evidence/T-002/validation.md。

T-002 进行中：本轮基线 `dev.py check --all` 29 passed；新增协议/原值/真实进程反例后 Ruff、Pyright strict、35 pytest 全部通过（23.74s）。源码基准已执行，standalone 与真实窗口尚未通过；最终结论以 T-002 证据为准。

| Date | Command/Check | Result | Notes |
| --- | --- | --- | --- |
| 2026-10-13 | Codex updater / login / CLI features | passed | 更新渠道 up_to_date，实际能力与未测能力见环境报告 |
| 2026-10-13 | uv lock / sync --locked --all-groups | passed | Python 3.12.14，67 个依赖安装 |
| 2026-10-13 | dev.py check --all | passed | Ruff、Pyright strict、14 pytest；无产品源码 |
| 2026-10-13 | dev.py smoke-env | passed | Qt offscreen、QProcess、中文 TIFF 原值往返 |
| 2026-10-13 | pip-audit --local | passed | 67 个包，未发现已知漏洞 |
| 2026-10-13 | Skills frontmatter / script AST / digest | passed | 5 技能，2 脚本语法，非业务端到端验证 |
| 2026-10-13 | GitHub rulesets | blocked | 私有仓库套餐限制 403 |
| 2026-10-13 | 产品/打包/科学样本/独立审查 | not run | 当前只治理与环境，产品任务未启动 |

| 2026-10-13 | Nuitka / GCC compiler probe | passed | 专用短缓存路径、生成启动器；不等于 Qt standalone |
| 2026-10-13 | GitHub CI at fdf9a61 | passed | Windows/Linux foundation 与 desktop-environment 三项 |
| 2026-10-13 | 官方 GitHub skills 只读脚本 | passed | PR #1 检查与审查线程读取成功 |
| 2026-10-13 | F-002 rule loader / Ruff / Pyright / pytest | passed | 29 个测试；包含遗漏、过期、范围扩大、路径与中文编码反例 |
| 2026-10-13 | Public visibility / ruleset 25008972 | passed | 用户授权公开；active，四项指定 Actions 检查，无 bypass；替代初次私有套餐阻碍 |
| 2026-10-13 | 规则回执独立负例与正例 | passed | 03afb43：其余检查成功，仅回执失败仍 BLOCKED；5eb1e8b：四项全部通过 |

| 2026-10-14 | T-003 dev.py check --all | passed | 61 测试，Ruff/Pyright strict、2 import-linter、隔离 wheel；GUI/检测未实现 |

| 2026-10-14 | T-003 输入阶段 dev.py check --all / 真实输入探针 | passed | 77 测试、3 合约、隔离 wheel；5 张 TIFF 只读加载，真实检测/GUI 未测 |

| 2026-10-14 | T-004 dev.py check --all | passed | 90 测试、4 import-linter、隔离 wheel TIFF→手工分析；不代表 worker/UI/存储完成 |

| 2026-10-14 | T-005 dev.py check --all | passed | 123 测试、4 合约、schema 漂移、隔离 wheel 真实 worker；GUI/强停/存储未测 |

| 2026-10-14 | T-006 dev.py check --all | passed | 164 测试、7 合约、3 wheel；38 工作区案例含真实硬退出/Windows别名/备份；UI未测 |

| 2026-10-14 | T-007 存储子阶段 check --all + 最终 pytest/Pyright/Ruff/policy | passed | 初次167，补用例后170测试；9合约/4wheel；实际Qt队列与退出提交；QProcess/UI未实现，独审未执行 |

| 2026-10-14 | T-007 进程阶段 dev.py check --all | passed | 185tests/9合约/4wheel；真实Qt进程、Windows孙进程强停、WB存储重开/旧revision、取消发布；GUI/独审/远程CI未完成 |

| 2026-10-14 | T-008 dev.py check --all / Qt交互追加验证 | passed | 190全量、9合约、4wheel5安装场景；真实手工GUI信号10保存重开/关闭保存/uint16/取消关闭；最终pytest见T008证据；OCR/独审/包态未完成 |

- 2026-10-19 T050/main221a2df：规划文档链接/PDF blob一致性、policy、diff、handoff容量均exit0。policy扫描0产品文件不证明产品通过。PDF文本初次GBK控制台失败，UTF-8重读exit0；归档目录缺失已由main原始blob恢复。产品测试/GUI/安装/科学评分未运行，后续文档审查见T050证据。
- T050方案fa61c29独立文档审查无阻塞，精确回执/链接/PDF/归档/diff exit0；PR16为Draft，远端检查以最终head为准。本轮仅规划，不合并或实施产品。
- T050后续澄清：当前方案942ecaa增量独立文档审查通过，按蛋白行分别管理槽位，检查exit0；无产品测试或修改。
- T050方案66f0b67：S1/S2批准与独立OCR功能保留的增量独审无阻塞；回执/diff/链接/PDF/容量exit0。无产品或安装验证。
