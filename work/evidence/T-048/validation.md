# T048 验证记录

产品提交 `3821c64a7068f2108fda15fcaf72d72f7f0da035`；2026-10-19；复用 t045 候选 checkout，未新增 worktree。宿主 Win11 Home x64 build26200，当前 token 非管理员。目标用户确认 x64 Win10，具体版本未知。

| 操作 | 实际结果与证据 |
|---|---|
| context scope . / apps/desktop | exit0，提交 rules-context.json；原图/原 checkout 不修改 |
| Ruff / format / Pyright 指定改动 | 最终 exit0；初次 format 指出 required 集合格式，已修正，无规则弱化 |
| pytest lifecycle/navigation/folder | 13 passed，35.84s，exit0；全769未重复，T047完整结果仅作为上游背景 |
| `python -m tooling.build_runtime_candidate ...` | exit0；GCC -Wall/-Wextra/-Werror；ISCC6.7.3 编译49.203s；私有同版本CPython与锁定四wheel，未重跑失败的全AOT路线 |
| 实际非管理员安装/重装 | 两次 exit0，无重启；独立测试 AppId/目录；`.local/t048/install.log` / `reinstall.log` |
| 必需入口 | 桌面、开始菜单程序、自检、卸载四lnk目标正确；HKCU卸载登记；`.local/t048/final-entries.json` |
| 实际Windows GUI生命周期 | `.local/t048/installed report v2.json` 七检查passed/8.047s；精确 `.process.json` exit0/14.2036s/所属进程全退/无开发模块 |
| 本地VC运行库 | manifest十个DLL摘要；安装后的动态模块MSVC140全来自应用内；复制源来自固定Qt wheel，Microsoft签名有效，不改System32 |
| 实际原生worker | staged-worker.json真实OCR标签Fig 1A/AKT与三模型摘要、非法quant协议exit2；实际安装诊断另跑真实定量和OCR |
| Win10内置PS5.1自检 | 安装的selfcheck.ps1实际exit0，selfcheck-success.log；缺失EXE负测CMD实际返回1，失败未伪装为通过 |
| 卸载 | exit0；移除入口和卸载登记、保留自建用户数据sentinel，uninstall-evidence.json；重装后只清理本验收创建且内容核实的sentinel |
| 保护检查 | protection-evidence.json：原TIFF和两个旧lnk摘要不变、Candidate设置不变，四个既有用户进程仍响应 |
| policy | exit0；policy.log；不改依赖锁/科学公式/schema/门禁 |
| 重装完整性 | installed-integrity.json：7721个非字节码文件与构建目录SHA256逐个一致；排除可重建__pycache__/pyc；exit0 |

失败证据：第一次外层控制器运行于 PowerShell5.1，进程退出码缺失为 null，故外层exit1；应用报告passed、所属进程无残留。不将该次记为完整成功，不改产品成功状态。保留 installed report.json 及其 .process.json/log；沿用现有pwsh控制器后v2完整exit0。安装所带的PS5.1自检使用 Start-Process -Wait，独立实测exit0，未受此观察脚本问题影响。

安装包：`BioImage-WB-Win10-x64-Test-T048-3821c64a7068-Setup.exe`，361325507字节，SHA256 `899082492c10ae94e5638ef1eb6517a8cc6eaa1b30235b81ecccd1706c4930b4`。原生入口 SHA256 `c49f22df44ce1fe11f3a7b7884c14964dabd0ee64f307855a51b5f529352e870`。完整manifest/产物位于ignored `.local/releases/runtime-3821c64a7068`。

交付复制：`C:/Users/70236/Desktop/BioImage-WB-Win10-测试版-T048/`，同名Setup.exe、安装说明.txt、SHA256SUMS.txt；复制后再次核对安装器摘要。`.local/t048/delivery.json`记录路径/摘要/版本。只需将安装EXE拷到目标电脑；说明与摘要便于核验。

未运行：干净 Win10（未发现本地VM/可用目标机器）、旧系统拒绝实机路径、物理鼠标点击/DPI矩阵、科学留出。非管理员本机通过不等于没有任何预装组件的Win10通过；交付说明明确最低系统和该缺口。未替换原版、未发布PR/main或网络发行版。
