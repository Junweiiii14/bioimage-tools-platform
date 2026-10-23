# T079 独立代码审查：实验室离线发行配置

结论：**Accepted（本次配置/代码差异）**。没有未解决的阻断发现。实际安装器与清理操作尚未在本轮独立验收，不把此结论当成交付完成或干净目标机通过。

- base：`eec9cd2e0893a2e847d08f151c5bcce27675a8ae`
- head：`e97d721e799397c22f3b5da4475f5f21e4720b56`
- 分支：`codex/t079-laboratory-delivery`
- 活动树：`C:/Users/70236/.codex/worktrees/wb-lab-installer/bioimage-tools-platform`
- 审查时间：2026-10-23 10:11:44 Asia/Shanghai（02:11:44 UTC）。
- 环境：Windows 11 10.0.26200、Python 3.12.14、PySide6 6.12.0；实际 Windows PowerShell **5.1.26100.9711**。
- 非作者独立审查；没有创建代理、修改产品/测试/门禁、改变分支/HEAD、干预构建或其他进程。仅新增本报告；测试文件位于经绝对路径验证的本次临时目录，结束后清理自己的目录。

## 阅读与范围

核对开始和收尾 HEAD/dirty，期间 HEAD 固定且产品树干净。阅读根 AGENTS、恢复索引/snapshot、当前风险/待办、module-map、T079、desktop README、architecture、coding-standards、research-protocol、ai-workflow、规则流程、installed diagnostics v1 及本次发行研究。

检查 eec9cd2..e97d721 全部差异；另核继承的 runtime builder、C launcher、许可收集、CMD wrapper、桌面入口/设置和相关测试。既有 T074–T077 产品审查不因本轮配置审查自动扩大，也未重验其全部科学/界面行为。

按只读委派读取已有 rules-context/integration-context，执行不带 --record 的 context loader（退出0），没有重写作者回执。该集成回执以 main 91dd985 为服务器基线、eec9cd2 为 source_head，保留 T074–T077 历史回执；本报告的代码差异基线仍是 eec9cd2。

## 复核要点

- **私有运行库与来源**：--laboratory 复用现有 CPython/锁定产品依赖和四 wheel 配方，无锁/依赖升级。原生启动器从自身绝对位置寻找 runtime/python.exe，以 -I -X utf8 -m bioimage_app 运行；不查找开发 Python、不使用 shell 解释业务参数。固定 Job 只包含其自己创建的进程。新分支选择同一 VC DLL 校验/复制路径，没有改为采集 System32 DLL。
- **许可与载荷边界**：代码保留 runtime 复制、依赖包元信息、third-party-licenses、Python LICENSE 和绑定提交的 source-code.zip 路径，没有新增删除/裁剪。此处确认配方保留，并非实际许可/模型/二进制载荷逐文件验收；后者应在构建结束后独立比对。
- **身份隔离**：AppId/AppUserModelID=BioImageTools.WB.Laboratory；通道 wb-laboratory；WebWorkbenchWindow 设置 BioImageTools/Laboratory；稳定私有安装目录和 BioImageWB.exe 名称互相一致。实验室窗口标题有真实构造器断言。此隔离结论针对当前 WebWorkbenchWindow 通道；旧显式原生兼容入口的既有共用设置没有在本轮重写。
- **安装/卸载**：每用户最低权限、x64、MinVersion 10.0.17763；桌面/开始菜单/自检/说明/卸载入口明确。没有旧版本自动卸载、任意进程扫描、 blanket UninstallDelete 或用户项目清理代码。说明要求退出并备份后更新，项目另存本地可写目录。实际卸载数据哨兵仍待包态验证。
- **PS5.1 自检**：固定私有 exe，两个诊断串行；使用新 GUID 报告、持有真实 Process.Handle、WaitForExit(180000)、非零/空 ExitCode 拒绝，并要求 JSON.phase=passed。超时、启动异常、报告缺失/损坏和第二阶段失败都进入失败分支；没有 Stop-Process/Kill 扫描或自动终止操作。超时返回失败不等于已清理所有所属子进程，实际进程残留需交付观察。
- **环境与数据**：脚本只在自身进程环境清理 PATH/PYTHONPATH/VIRTUAL_ENV/QT_PLUGIN_PATH，工作目录为 TEMP，诊断使用合成输入；不操作用户原图。普通产品启动算法、数据 schema、原始输入和历史输出代码未变。
- **说明范围**：部署目标、无商业签名、离线依赖、CSV text:、备份/更新/卸载和目标机限制已明确。没有把本机包态或软件渲染推为干净 Win10、物理 DPI/GPU/Explorer、科学准确率或正式科学验收。

## 独立验证记录

| 命令/实验 | 实际结果 | 可支持范围 |
|---|---|---|
| `uv run --locked --no-sync pytest -q tests/test_execution_distribution.py tests/test_workbench_launcher.py`，环境 QT_QPA_PLATFORM=offscreen、QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu | **exit 0；13 passed / 4.93s** | 实际通道构造器设置空间/标题与已有隔离入口。未动真实用户注册表设置 |
| 实际 Windows PowerShell 5.1，以 -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command 运行原 windows_laboratory_selfcheck.ps1；只替换 Start-Process 端口和禁止调用的 Kill/Stop-Process，LOCALAPPDATA 指向临时中文/空格路径 | 外层 **exit 0**；9 个独立场景符合预期，详见下表 | 原脚本的失败传播/顺序/路径逻辑，不是安装版真实 OS 进程运行证明 |
| stdin Python 在已验证的临时 ROOT 实际调用 build_runtime_candidate.main；编译器、uv 安装、许可证/图标工具均为显式 test double | **exit 0**；四 wheel、五个本地 VC DLL、私有 exe、环境自检.cmd、正确 .iss/通道/manifest identity 均符合断言 | 新 profile 接线与名称一致性；不冒充完成编译或离线载荷验收 |
| 实际 Python 子进程 `python -m tooling.build_runtime_candidate --laboratory --execution-test --iscc C:/fake/iscc.exe --gcc C:/fake/gcc.exe` | 子进程 **exit 2**，互斥选项明确拒绝；外层断言程序 exit0 | 未进入构建或调用假编译器 |
| `uv run --locked --no-sync python dev.py context --task T-079 --scope . --base 91dd98554e0ce649e691c4fd656d2e3d8dbf7628` | **exit 0** | 只读加载适用规则，不改回执 |

PS5.1 反例的原脚本实际退出码：

| 场景 | 退出码 | 诊断调用次数 |
|---|---:|---:|
| 两阶段 exit0 + passed | 0 | 2，顺序正确且报告名不同 |
| OS 端口 ExitCode=17 | 1 | 1 |
| ExitCode=null | 1 | 1 |
| JSON phase=failed | 1 | 1 |
| 报告缺失 | 1 | 1 |
| JSON 损坏 | 1 | 1 |
| WaitForExit 返回 false | 1 | 1 |
| Start-Process 抛异常 | 1 | 0 |
| 第一阶段通过、第二阶段失败 | 1 | 2 |

所有反例均未调用测试中设为失败哨兵的 Kill/Stop-Process。超时被端口立即模拟，没有等待真实180秒，也没有启动或终止用户/构建进程。

保留的探索失败：

1. 首次 PS5.1 harness 漏传 ExecutionPolicy Bypass，系统执行策略拒绝 dot-source，外层 exit1，未运行脚本主体。补上与随包 CMD 相同的参数后，九场景通过；这不是产品脚本失败，也不隐去该轮。
2. 直接经 uv/PowerShell 调用互斥参数的负例时，命令宿主返回1；随后用 Python subprocess 明确取到 argparse 子进程实际2，记录两层区别。
3. 初始定位命令包含不存在的 scripts/installer/packaging 目录、runtime_bootstrap.py，返回1；改用 rg 定位实际文件后逐项阅读，未据空片段修改或推断实现。

## 未执行与后续交付核验

本轮未重建/安装/卸载软件，未启动真实包态诊断，未触碰本地旧版或 GitHub。未独立重复全部 check、wheel 安装、远端 CI、外部漏洞查询或许可证法律审计。

下一阶段应绑定实际安装器/manifest/载荷摘要，核实际模型和许可文件、受限环境下所有模块均来自安装目录、真实 PS5.1 自检及 OS 退出/所属后代、卸载/重装哨兵和明确清理清单。已有历史 UNKNOWN、干净目标 Win10、物理 DPI/输入/硬件 GPU 和独立科学留出继续保留。

**最终代码结论：Accepted；实际交付与清理验收待后续独立证据。**

