# 候选验证与独立 Windows 验收

仓库工具分开处理构建、只读来源核验、合成诊断和实际安装。它不发布、安装或卸载软件。T081 未跟踪本地脚本已经不可取得；本入口是基于现有 `installation_check*.py`、laboratory 自检及冻结 manifest 的最小通用替代，不声称恢复旧脚本的全部行为。

## 输入与构建

使用干净、准确提交及已有门禁/独审。构建入口仍先验证 `toolchain-lock.json` 的工具来源和哈希。用于本轮可弃验收时：

```powershell
uv run --locked --no-sync python -m tooling.build_runtime_candidate --iscc $taskISCC --gcc $taskGCC --laboratory --acceptance-id t082-r11-a
```

`--acceptance-id` 必须同时选择 `--laboratory`，匹配 `[a-z][a-z0-9-]{0,31}`；空字符串也拒绝。复用 `windows_laboratory.iss`，不增加另一份安装模板。该参数会改变以下**全部**身份：

| 身份 | 值（示例） |
| --- | --- |
| AppId / 卸载登记 | `BioImageTools.WB.Acceptance.t082-r11-a` |
| 启动通道 / 设置 | `wb-acceptance-t082-r11-a` / `BioImageTools/Acceptance-t082-r11-a` |
| 启动器 | `BioImageWB-Acceptance.exe` |
| 默认目录 | `%LOCALAPPDATA%/Programs/BioImage WB 验收 t082-r11-a` |
| 桌面 / 开始菜单 | `BioImage WB 验收 t082-r11-a` |
| 自检报告默认目录 | `%LOCALAPPDATA%/BioImage-WB-Acceptance-t082-r11-a/Diagnostics` |

manifest 记录这些值及 `user_data_removal=false`。设置分支、启动器、模板及工具必须作为同一准确提交独审后再构建。没有参数时，已有 Laboratory 和其它 profile 的身份保持原值。只给旧 laboratory 安装器 `/DIR` **不能**隔离 AppId、设置或快捷方式。

## 新检出中的只读核验

调用者提供候选输出目录、准确源提交、包含该提交的 Git 检出、安装器路径及从交付检查点独立核对的 SHA256。`$taskReport` 是候选/安装目录之外的一个不存在目录。

```powershell
uv run --locked --no-sync python -m tooling.candidate_acceptance verify --candidate $taskCandidate --installer $taskInstaller --installer-sha256 $taskSHA256 --source-commit $taskCommit --source-repo . --report-directory $taskReport
```

验证器检查最终/包内 manifest 对应关系、安装器摘要/大小、payload 的原字节 SHA256、运行库/启动器、包内 source-code.zip、源码锁及四包的实际源码/资源。Git 参考归档由准确提交重新生成，遵守冻结的 `.gitattributes`（包括 `.cmd` CRLF）；四包纯文本仅容许明确记录的 CRLF/LF 差异，payload 哈希始终逐字节。重定向路径、未知工件、源码/资源缺失及不匹配一律失败。报告记录参考归档摘要，不承诺安装器字节级可复现。

目标机可使用已核对的私有 Python 直接执行仓库脚本；它只需标准库，不能用 `-I -m tooling...`，因为产品没有安装开发 tooling：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tooling/windows_candidate_acceptance.ps1 -Python $taskPython -Candidate $taskCandidate -Installer $taskInstaller -InstallerSha256 $taskSHA256 -SourceCommit $taskCommit -SourceRepo $taskCheckout -ReportDirectory $taskReport
```

PowerShell 7 使用相同参数。wrapper 仅在自身进程恢复 `$PSHOME/Modules`，在系统临时目录独占创建 UTF-8 JSON 请求文件；所有目录参数作为 JSON 数据交给 Python，避免 PS5.1 尾反斜杠/引号合并。请求文件及其摘要被保留，真实进程退出码原样传出；空退出码不能转换为 0。不会向候选或安装目录写请求/报告。

## 实际安装是单独的 Windows 门槛

R11 先记录 OS build、CPU/内存、显示器缩放、准确安装器 SHA、源码提交及本次验证脚本/命令。新 ID 的 `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\BioImageTools.WB.Acceptance.<id>_is1` 必须不存在，目标目录必须不存在；记录当前 Laboratory 登记/快捷方式/设置，安装后对比保持原样。不要直接安装任意旧 profile。

经准确提交独审后，使用明确的新中文带空格目录和新日志执行安装；同样适用于 PowerShell 5.1/7：

```powershell
$taskProcess = Start-Process -FilePath $taskInstaller -ArgumentList @('/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-', ('/DIR="' + $taskInstallRoot + '"'), ('/LOG="' + $taskInstallLog + '"')) -WindowStyle Hidden -PassThru
$null = $taskProcess.Handle
if (-not $taskProcess.WaitForExit(180000)) { throw 'Installer timed out; retain PID and logs' }
if ($null -eq $taskProcess.ExitCode -or $taskProcess.ExitCode -ne 0) { throw 'Installer failed; retain logs' }
```

核对**新 ID** 的登记 InstallLocation、DisplayVersion、UninstallString，快捷方式目标必须是新目录中的独立启动器。升级只针对这个已核验的可弃 ID/目录；不能使用在用 Laboratory 登记。升级前后保留合成项目、历史 schema 样例及摘要。卸载仅使用该登记指向的自有 uninstaller；记录真实退出码/日志及合成保留文件前后摘要，验证无 blanket UninstallDelete 的行为。上述实际安装/升级/卸载日志不能由目录复制或源码测试替代。

## 合成执行、失败与恢复

验证器的 `run` 先完成同样的来源核验，只执行 manifest 身份完整一致的 disposable acceptance 包。传入 `--installed-root` 核对实际目录；缺少此参数时明确标为 `candidate-directory`。目录核验本身只标 `supplied-installation-directory`，不推断它经过了安装器。

```powershell
uv run --locked --no-sync python -m tooling.candidate_acceptance run --candidate $taskCandidate --installed-root $taskInstallRoot --installer $taskInstaller --installer-sha256 $taskSHA256 --source-commit $taskCommit --source-repo . --report-directory $taskRunReport
```

PS wrapper 的对应参数是 `-InstalledRoot $taskInstallRoot -RunDiagnostics`。两个合成流程复用 `--verify-installation` 与 `--verify-supervision-installation`，分别覆盖独立灰度/OCR、保存失败/取消/重开及当前裁图/成图/结果/导出链。私有解释器以 `-I` 查四包实际模块路径；诊断须真实 exit0、报告 passed/无 errors、准确模块/通道及已结束的报告 worker PID。超时仅停止本次持有的 launcher，既有 Job Object 负责所属后代；不扫描或终止其它进程。报告包含 stdout/stderr、PID、退出码、超时、模块位置、worker 退出观察及诊断报告摘要。

执行前拒绝未冻结 `.pyc`，`-B` 不被误当作禁读缓存。一次诊断自行生成的缓存只在末尾清点为未认证文件，不改原 payload 清单；再次执行须使用恢复到冻结内容的新可弃目录/安装。工具不删除旧缓存，不把未检查缓存转成可信输入。安装器升级不会保证清理旧 cache，因此可先完成受控安装/升级，再对冻结状态运行一次诊断；后续恢复另建 ID/目录并保存关联。

每次必须指定新的报告目录。失败留下 `acceptance.json`、已产生的诊断和日志；中断留下 `phase=running`，不能判为通过。修复环境/来源后用新目录重跑，并传 `--previous-report <旧acceptance.json>`（wrapper 为 `-PreviousReport`），新报告记录旧报告 SHA，旧内容不覆盖。不得以更改原报告的 phase 或删除失败日志“恢复”。

本机 Win11、离屏软件渲染、合成图和目录核验各有范围：干净 Win10、物理 125/150/200% DPI、真实拖放/GPU、员工设备、外部 Excel/WPS/LibreOffice、独立科学留出均须单列实际运行/未运行，不据自动诊断外推。
