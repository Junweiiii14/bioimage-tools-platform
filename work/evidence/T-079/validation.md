# T079 实验室离线交付验收

2026-10-23，北京时间。本机 Windows11 Home 10.0.26200 x64，非管理员安装；uv0.13.0、Python3.12.14、Qt6.12.0 / Chromium140.0.7339.225。产品基线T077 c32ad11，证据基线eec9cd2；T079包装e97d721，最终冻结包装 **efd8d4f8fa9cd6c3b86a291d49ede9ad54bb971b**。后续文档提交不重贴二进制版本，须检查产品/配方字节无差异。

## 构建和可交付物

`uv sync --locked --all-groups` exit0；规则加载 `uv run --locked --no-sync python dev.py context --task T-079 --base origin/main --scope . --record --integration` exit0，读取实际输出。main基线91dd985；历史T074–T077回执保留原字节，显式集成清单随PR39提交。`python -I tooling/rule_context.py check --base origin/main --head HEAD`（uv锁定环境）在e97/efd均exit0。

构建命令两轮均exit0：

```powershell
uv run --locked --no-sync python -m tooling.build_runtime_candidate --laboratory --iscc C:/Users/70236/.codex/worktrees/t045-wbquant/bioimage-tools-platform/.local/t047/toolchain/inno-6.7.3/ISCC.exe --gcc C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform/.local/t075-toolchain/mingw64/bin/gcc.exe
```

固定既有Inno6.7.3/MinGW；锁定运行依赖38项，含私有CPython、QtWebEngine、本地OCR三模型和app-local VC运行库。没有升级锁、引入新科学计算或大模型。随包完整第三方通知、版本清单及源代码归档；RapidOCR/FlatBuffers wheel遗漏的许可证全文由固定上游tag补齐，构建主动核版本/文件SHA，不能将其当全面法律审计结论。

| 候选 | 安装器字节数 / SHA256 | 结论 |
|---|---|---|
| e97d721初包 | 383850002 / 73bff8cfc022c56afd468f77ee530c9d428fed93a1083bd07847146e353de9be | 独审指出两项交付问题，Needs fixes，不能作为最终包 |
| efd8d4f最终包 | 383860684 / 571a66b3e214ea2167c2208e19b8c399c0e46ef7aef3c6548fd457f456b18b8b | 两项修复已内置，实际安装/自检/逐文件核验通过；独审见同目录报告 |

最终包名 `BioImage-WB-Lab-Windows-x64-efd8d4f8fa9c-Setup.exe`。安装身份BioImageTools.WB.Laboratory，设置Laboratory，稳定每用户目录“BioImage WB 实验室版”，桌面/开始菜单/说明/自检/卸载入口齐备。没有公开上传安装器或私有素材。

## 作者实际执行

全部uv命令使用 `uv run --locked --no-sync`；原始大日志和摘要收据在本树ignored `.local/t079-*`，不提交生成包。

| 命令/行为 | 实际结果 |
|---|---|
| `pytest -q tests/test_execution_distribution.py tests/test_folder_drop.py tests/test_visible_export_desktop.py`（源码e97） | 19passed/26.48s，exit0；10个Qt构造弃用警告，GPU/mailbox日志保留 |
| Ruff check/format、Pyright strict、`dev.py policy` / `doctor` / `smoke-env`（e97）；efd增量Ruff/format/Pyright/policy | 均exit0；strict无错误/警告；本地未单独重复完整check--all，最终全门禁由精确HEAD的CI核 |
| 实际Inno普通用户安装e97 | exit0；Win11中文用户路径、非管理员、无重启，收据t079-install-result.json/log |
| 已安装PS5.1 `-NoProfile -ExecutionPolicy Bypass -File <install>/selfcheck.ps1` | e97/efd两轮均exit0；每轮新JSON分别灰度/OCR与supervision完整主链，不复用旧报告 |
| e97原生qwindows窗口启动→主窗口Responding→正常CloseMainWindow | 正确安装python.exe/PID/出生时间/标题/句柄；launcher正常exit0、该安装目录进程剩余0，未强杀 |
| e97卸载→重装 | 两次exit0；安装可执行文件卸载后消失，自建用户哨兵SHA保持；既有原图/项目不作测试目标 |
| efd覆盖更新e97 | 安装exit0；manifest准确更新到efd，用户哨兵SHA保持，新的PS5.1双模式exit0，t079-efd-install-result/selfcheck-result.json |
| 已安装runtime `-I -X utf8 .local/t079_installed_acceptance.py`；efd新副本t079_efd_installed_acceptance.py | e97 19passed/14.64s；efd 19passed/14.79s，均exit0。仅pytest/测试来自dev，产品/worker/Qt模块每项检查来自安装目录，不能称产品包含pytest |
| `.local/t079_verify_payload.py`；efd新副本t079_efd_verify_payload.py | e97 7785、efd 7788构建/安装文件逐SHA相同，204产品.py/web资源源文件相同。隔离PATH=System32、isolated=1、无pytest，38版本清单；最终收据commit读取实际manifest，严格40字符 |
| 已安装runtime运行`.local/t079_demo_acceptance.py` | 1passed/3.79s，exit0；真实主界面打开交付副本示例项目文件夹，等待加载后10个原始单元格/两Fig行存在；未审核可见表/质量缺项保持。主界面入口是文件夹，不把ZIP写成其直接入口 |
| 独立阶段审查 | e97源/失败码/配方Accepted，实际交付Needs fixes；efd许可和说明增量+实际新包另审，见delivery-review-efd8d4f.md，不沿用旧包签收 |

PS5.1新报告：`%LOCALAPPDATA%/BioImage-WB-Laboratory/Diagnostics/20261023-105749-bd3681de21924496bf8306c3f42fad9e.json` 及 `20261023-105801-9f7403ba0fbe45b1b5f26806b3e86ab2.json`。安装无需Python/uv/Office/在线模型；不把临时测试harness作为用户运行条件。

## 本地旧版整理

执行前盘点仓库/分支/HEAD/dirty及磁盘目标，保留ResearchVault旧dirty树、视频研究树、当前交付树、原图和历史结果。先生成并验证all-refs bundle、完整桌面材料ZIP、未提交成果ZIP、未知安装文件ZIP/剩余文件副本及26份旧生成目录未知文件ZIP。未知文件不按扩展名忽略；仅逐摘要等同保留payload的可重建文件、精确manifest证明的89个旧生成包另作分类，不能冒称这些旧包都逐字恢复。

`.local/t079_cleanup.ps1` exit0：12旧程序目录、12桌面材料目录、26旧生成目录移除（10真实旧卸载器exit0），6失效桌面链接备份后移除；旧BioImage通道登记计数0。逻辑移除60,325,925,956字节，可用空间从85,853,130,752到111,699,927,040字节，净增加25,846,796,288（约24.07GiB）；硬链接/备份使两种体积不能混称。原旧源树及仍需的本地编译器保留。

私有归档 `C:/Users/70236/ResearchVault/Codex-Workbench/WB-归档-20261023-T079`，不上传GitHub。非作者独立逐SHA核5主归档/595记录、26生成归档/196272未知文件、206009保留payload引用，git bundle verify187refs/complete history全部exit0。作者清理后再核66保留dirty源文件SHA一致。原ResearchVault实际27项dirty不清零。

含额外旧StartMenu/孤立卸载登记删除的命令被自动审批在执行前拒绝，仅返回“blocked by policy”。未重试注册表删除；WB-Quant旧孤立卸载登记保留。后续更安全的6个失效StartMenu链接移动到私有归档，源/目标边界、失效条件、逐SHA均核，实际exit0；非作者独立复核。桌面现仅一个有效BioImage WB实验室版快捷方式、Programs仅一个BioImage安装目录。

## 保留的失败与限制

- 初始盘点遇到2个已不存在的历史worktree，NotADirectoryError；改成记录缺失/跳过，只读退出0，不猜其状态。
- 清理独审在执行前指出路径尾分隔符/大小写保护、未知文件白名单遗漏、过宽快捷方式匹配三项问题；修正后反例/完整备份通过，再运行删除，没有先删再补证明。
- 初次裸gitcommit找不到pre-commit，未提交；builder因dirty正确拒绝exit1。随后用锁定uv环境执行真实hook全部通过，没有跳过hook。
- 更新helper初次PS5.1读取无BOM中文脚本导致路径解码失败exit1，安装前停止。改helper编码UTF8 BOM后实际更新成功；随包自检为ASCII，未受此问题影响。
- 初次payload helper环境键大小写错误/临时命令智能引号语法错误均exit1，修helper后重跑；efd收据曾手写commit多一个c，独审发现后改为读manifest并重算7788+204摘要。未改产品字节或删除原失败事实。
- 示例项目测试初次只等占位单元格出现，尚未异步加载就断言失败；改为同时等真实10个raw项及idle，原数值/质量断言保持，再过1项。GPU/mailbox回退日志不认定硬件根因已修。
- 无可用干净Win10/VM；工具定位无结果返回1。目标范围Win10 1809+/Win11 x64是打包目标，不是逐台部署已验。物理Explorer/OLE/鼠标、DPI/所有GPU、外部Excel/WPS显示、科学真值及准确率未验。安装器未商业签名，遵守实验室IT策略；不用停用防护来安装。

## 最终集成和交付闭合

正常集成PR为 [#39](https://github.com/Junweiiii14/bioimage-tools-platform/pull/39)。**仅包含最终证据文档的准确PR HEAD四必需检查全SUCCESS、独审Accepted、merge commit真实合入main后才算GitHub整理完成**；e97/efd较早CI不替代最终HEAD。`.local/T079-final-ci.json`和实际GitHub为实时证据，未运行的native-case不写通过。合入后再关闭被替代的35–38并只清理可证明已合入、无活动工作/PR的远端分支，保留独立依赖PR。

最终桌面文件夹/ZIP在上述条件满足后冻结，补入精确CI收据和验证说明，生成逐文件SHA清单、ZIP CRC/成员SHA核验与最终外部收据；不更改已审安装器、许可、示例或校验器。最终摘要以桌面冻结收据为准，不把当前staging预览称已交付。视频研究聊天已在原授权下创建，本轮保留其活动树，不复制新聊天、不新建调度。
