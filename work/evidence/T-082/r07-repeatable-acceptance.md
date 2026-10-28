# R07 仓库验收入口与隔离安装身份

2026-10-28；实施基线 R06 `516d7c0`，最终定向检查时 HEAD `45106f99e7d684fc1fb4b961afe642dfdc948b32`。本文件记录作者自验，提交及非作者独审由集成人员补充；不表示 R11 已通过。

## 范围与事实

- 旧 `.local/T081/package/r2` 曾可列出并读取部分文件，随后目录外部消失。未恢复 `installed_acceptance.py/publish_local.py/resume_publish.py`，不伪称照搬旧脚本。本次基于仓库 `installation_check*.py`、lab selfcheck、R06 manifest 实现最小通用替代。
- 新 `tooling/candidate_acceptance.py` 为纯标准库，可由 private Python `-I -X utf8 <绝对脚本>` 执行；`verify` 只读核验，`run` 显式调用现有两项合成诊断。不安装、升级、卸载、发布软件，不操作真实实验图。
- `verify` 关联准确源提交、独立选定 installer SHA、最终/包内 manifest、全部 payload 原字节、launcher/runtime、Git 冻结归档和四包源码/资源。实际 Git archive 处理 `.cmd` 换行属性；包内文本仅记录 CRLF-only 差异，payload 原字节检查不归一化。
- `run` 仅接受一致的 disposable identity，核对 private interpreter/四模块路径、诊断实际退出/报告、supervision 通道/源码位置及报告 worker 已退出。超时只停止本次启动的 launcher，所属后代由已有 Job Object 释放；不扫杀其它进程。执行前未冻结 pyc 拒绝；本轮新 cache 仅在末尾列为未认证观察，重跑需要恢复新冻结 payload/隔离目录，不自动删除旧 cache。
- 每次新报告目录，原失败及恢复分别保存；恢复显式引用旧报告路径、phase、SHA。中断保留 running，非 passed。报告含验证器 SHA、OS/CPU、shell、进程、超时、模块和诊断摘要。`supplied-installation-directory` 不冒充真实安装/登记/生命周期证据。
- PS wrapper 在独立 TEMP JSON 传值，只在自身进程修复 PSModulePath；UTF-8 请求保留并在报告关联。不会向候选/安装路径先写 request 再拒绝。

## 隔离 profile

复用既有 `windows_laboratory.iss` 的可选宏，`--acceptance-id` 仅与 `--laboratory` 同用，完整匹配 `[a-z][a-z0-9-]{0,31}`（空字符串拒绝）。AppId=`BioImageTools.WB.Acceptance.<id>`，channel=`wb-acceptance-<id>`，settings=`Acceptance-<id>`，launcher=`BioImageWB-Acceptance.exe`；独立中文默认目录/桌面/菜单、专用自检报告目录。manifest 明列身份与不删除用户数据。default profile 的既有参数与输出配置保留；没有增加第十一份 `.iss`。

产品 `web_window` 的受限 channel→QSettings 支持由 root 独立修改并测试，需与该工具一起提交复核。本子任务不修改产品 UI。不能只通过 `/DIR` 安装旧 laboratory 包；R11 必须先核对新 AppId 未登记、新目标目录不存在、当前在用登记不变。实际步骤见 [runbook](../../../docs/runbooks/candidate-acceptance.md)。

## 有效检查

Windows 当前开发环境，Python/uv 按仓库锁；不运行 GUI 和全门禁。

| 命令 / 探针 | 实际结果 |
| --- | --- |
| `uv run --locked --no-sync python -m pytest tests/test_candidate_acceptance.py tests/test_runtime_integrity.py -q --tb=short` | **46 passed / 14.22s / exit0**；32 新例 + 14 R06 回归 |
| 对 4 个改动 Python 文件运行 `ruff check` / `ruff format --check` | 均 exit0；最终 format check 为 4 files already formatted |
| `uv run --locked --no-sync pyright tooling/acceptance_profile.py tooling/candidate_acceptance.py tooling/build_runtime_candidate.py tests/test_candidate_acceptance.py` | 0 errors / 0 warnings / exit0 |
| `git diff --check` | exit0（未修改他人的 R03/R05/R09 文件） |
| 新临时 Git fixture + 冻结属性/源归档 + 四包合成目录 | 精确源码通过；源码/缓存/额外 DLL/installer/embedded manifest 篡改或外逸路径均拒绝 |
| 两实际 shell `powershell.exe` / `pwsh.exe` | 中文/空格/末尾反斜杠路径，错误 SHA exit1 留失败 → 新目录正确 SHA exit0 且引用旧 SHA；保护目录请求失败且 payload 全部不变 |
| 自有短进程 exit7 / 30秒进程超时 | 保留非零；0.1秒超时仅停止本次进程、真实 wait/非零，不当作成功 |

成功的模拟诊断验证流程保留 3 次进程与 2 项诊断证据；异常退出、错误模块路径、仍存活 worker 的独立反例拒绝。模拟并非真实安装态或 GUI 通过，后者留给 R11。

## PowerShell 与预审修正

只读子任务实际核对 PS5.1 `5.1.26100.9711`、PS7 `7.6.5`。PS5.1 继承当前 PSModulePath 时找不到 Get-FileHash，受控退出19；只隔离子进程模块路径后同一文件 hash exit0；PS7 两种情况均 exit0。PS5.1 原生调用把末尾 `\` 的带空格目录与后一个含引号参数合并，PS7 保持三个参数。本工具用 JSON 避免该边界。两个 shell 的自有150ms/exit7进程均如实超时/退出；本次没有复现旧 null ExitCode，不伪称已复现。

早期预审发现并修正三项：①真实 `.cmd` Git blob 140B、archive145B 的属性转换，改为冻结 Git archive 参考并补 `.gitattributes` fixture；②执行前不能默认接受未冻结 pyc，`-B` 只禁写；③PS request 原来可能先写保护目录，改 TEMP 唯一请求并增加“拒绝且目录不变”的双 shell 反例。初始定向 3 例因复制出的环境字典大小写失败，修正为 Windows `os.environ['SYSTEMROOT']`；扩展属性 fixture 一度用 CRLF 写 uv.lock 导致 6 个预期通过项失败，fixture 改按仓库 LF 属性生成，未放松验证器哈希。最终 46 项通过不覆盖/抹除这些失败。

## 真实 Inno 最小编译

经 root 进一步授权，仅编译合成 payload，不执行生成的安装器。使用锁定 `.local/T082/r06-toolchain/inno-6.7.3/ISCC.exe`，执行前核验 ISCC 和全部 Inno support hashes。合成启动器只是标明 NEVER RUN 的文本工件，不是产品程序。

`uv run --locked --no-sync python -c "import runpy; runpy.run_path('.local/T082/r07-inno-probe/run.py')"` → **exit0 / 3.78s**。原直接脚本调用因缺少 repo import path 失败；用 runpy 从 repo 执行修正，仅探针路径问题。

- `516d7c0` 旧模板、当前默认宏、当前 `AcceptanceId=t082-compiler-probe` 三次实际编译 exit0。
- 使用官方 ISPP [SaveToFile](https://jrsoftware.org/ishelp/topic_savetofile.htm) 保存真实预处理文本；去掉 OutputDir（各次独立目录）、空白/注释后，当前 default 与旧模板完全相同。
- 本次旧/新 default 合成 installer SHA 同为 `ee1f7806cdb2e352841cad08dcec65aa15d2e3d430a054cf73b58d0c6d6d427b`。这只是该最小实验事实，不泛化为产品安装器逐字节可复现。
- Acceptance installer SHA `22de0895a67f13956744699b9bfd7683b16b2c6c9820c00a2401bbc0b345d715`。预处理文本核 AppId、中文默认目录/菜单、桌面 AppUserModelID、独立 launcher、无 UninstallDelete。
- 被编译模板 SHA `f0535e52bfd084307eb1592a0373f8149fe4d571d6687cd50467f0c7ba80ee63`。本地完整探针、3日志、预处理文本与 result.json 位于 `.local/T082/r07-inno-probe/`，生成 exe 不提交且从未执行。

## 尚未完成

root集成设置分支：仅完整匹配合法acceptance通道时选择独立QSettings及验收标题，非法长度/空ID/路径/大写/换行继续默认Platform；既有全部通道保持。新增真实构造/独立临时设置文件检查，旧产品 **3 failed,5 passed / 3.21s / exit1**（r07-settings-red.txt），证明合法测试通道原会复用Platform。修后联合R03/R05/设置/导航/关闭/高级/重试/quant/组审核9文件 **88 passed / 45.87s / exit0**（r05-r07-integrated.txt）。Ruff及严格Pyright0；这是准确提交前作者集成自验，非安装态通过。

本单元没有真实产品全量构建、安装、升级、卸载、GUI 合成诊断、在用登记对比、R11 目标矩阵或独立科学验收。需设置分支完成、准确提交独审与最终冻结门禁之后，由 root 按 runbook 在新目录/新 AppId 执行。真实目标机、物理 DPI/GPU、外部 Office 和 R10 留出材料仍按各自条件记录。这里的工具/合成证据通过不能把这些项目标为完成。
