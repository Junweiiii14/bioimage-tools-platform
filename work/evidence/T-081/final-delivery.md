# T081 安装包交付与最终闭合证据（2026-10-24）

R2完整离线安装包已经实际安装验证、独立产物审查并交付桌面，Windows原生解压及解压后校验完成。完整任务仅在最终文档准确HEAD独审、四项必需CI及PR43正常合入也全部成立时完成；以任务的闭合谓词、实时PR和 `.local/T081/package/r2/final-closeout.json` 为准。本记录不预先声称自身未来提交的检查已通过。

## 冻结版本与集成

明显条带算法及整批裁剪门槛提交 `81d8d87f6ffbe265137b8a8dce9864231bef7e39` 已获独立源码审查 Accepted，四项必需检查成功。Linux 1291 测试/442.16s、Windows 1291 测试/620.87s及全部隔离 wheel 完成；PR42 正常合入 main `b59123e1eedabbb9f70bc4456e8ab74956aedd4a`，产品树相同。初始 Windows 2 fail 与 Linux 20 分钟取消保留，后继成功不等于原生退出根因已解决。

R2 源码及实际构建提交为 `f1e6142ab41e16c66cfeb3d33958ab3a364581b1`；独立源码审查 Accepted，报告原样保存为 [final-source-review.md](final-source-review.md)。其继承算法独审，并覆盖恢复图片角色修复及测试前置修正。安装器准确标记此受审查/CI验证的源码 SHA，不把后续文档或合并 SHA 冒充安装包来源。

| R2 集成项目 | 真实状态及证据 |
| --- | --- |
| `f1e6142` 的 `desktop-environment` | **SUCCESS**；[job 120593359561](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/40005831584/job/120593359561) |
| `f1e6142` 的 `foundation (ubuntu-latest)` | **SUCCESS**；1295 passed/509.77s、全部隔离 wheel；[job 120593359538](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/40005831584/job/120593359538) |
| `f1e6142` 的 `foundation (windows-latest)` | **SUCCESS**；1295 passed/756.69s、全部隔离 wheel；[job 120593359079](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/40005831584/job/120593359079) |
| `f1e6142` 的 `rules-context` | **SUCCESS**；[job 120593359167](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/40005831722/job/120593359167) |
| 最终文档提交的准确HEAD独审及四项必需CI | 按任务闭合谓词及最终真实收据核准确新提交、独审、四项检查和产品树无差异；不替换上面的构建来源记录 |
| PR43 正常合入 | 按实时PR及最终真实收据核合入 SHA、时间和合并树；不可用旧 HEAD CI 替代 |

四项准确提交检查由 `release-gate.json`、`github-final-checks.json` 绑定；非必需 `native-case` 按原条件 SKIPPED。两平台实际执行 `uv run --locked --no-sync python dev.py check --all`，退出成功，完整日志为 `ci-linux-f1e6142-complete.log` / `ci-windows-f1e6142-complete.log`；末尾 wheel 和治理检查成功，不只引用 pytest 计数。没有因此改依赖、锁文件或门禁。

## 需求逐项核对

| 要求 | 已证明事实 |
| --- | --- |
| 明显主行直接定位，不固定上方；填写 N 为硬约束 | `prominent@1` / `intake_crop@5` / `fixed_n_frame@2`；按明显程度选择主行，保留 N 槽及原坐标中间区域。94 项定向回归通过/9.55s，静态检查通过；见 `algorithm-validation.md`、`validation.md` |
| 失败行继续尝试其余裁剪，未完成整批裁剪不继续拼图/测量/输出 | `intake_workflow@5` 及公开发布 API 门槛；保留成功原值资产，修正后继续，未把失败写成有效零。门槛和重试证据见 `workflow-barrier-validation.md` |
| 用户给定 180 实际流程 | 用户确认 Fig1/2 原 N 填反后，按 **4/2/5/4** 配置，与原工程相同的 9 个 `(1)` 来源。正常 DOM 入口完成 9 crop、4 compose、4 measure、1 export，自动到结果页；无手工裁剪确认。1 项真实流程/51.95s、exit0；原工程只读 |
| 原值、槽位与原始输入保留 | 9 份保存裁图逐像素等于原图完整窗口，dtype/形状/N 槽保持；包含约 −17° GAPDH。最终只读复核 39/39 原始输入 SHA/大小与 T080 基线一致；9/9 裁图重新比对一致 |
| 完整项目目录 | 私有桌面 `C:/Users/70236/Desktop/WB-180-T081` 与原交付 **127 文件、222129820 bytes** 完全同 SHA/大小；126 个保存 index 成员逐个核验，另含 index 本身。包含 Fig 组、各类原图/对应裁图/预览、完整拼图 PNG/TIFF、灰度 CSV/XLSX、项目恢复 ZIP |
| 恢复后所有图片仍能使用 | R1 暴露的问题已由 typed role 修复；**R2 安装态**真实恢复验证27原图 TIFF 可读、9原值裁图精确一致、4 Fig 的 PNG 格式/CRC/像素解码、27缩略图及源交付127文件不变。实际结果页截图显示“缩略图加载结束：0张失败”；既有导出 interrupted 提示仍如实保留 |

最终私有数据复核命令：`uv run --locked --no-sync python .local/T081/package/r2/private_final_audit.py`，exit0；收据 `private-final-audit.json`。Win11 10.0.26200 / Python3.12.14 / NumPy2.5.4 / tifffile2026.9.20。全部旧验收收据审计前后 SHA 一致；没有运行 Qt、重算算法、写入原图或历史。此复核不替代新安装包验收。

## R1 失败与 R2 修正

R1 构建和实际升级、双模式自检、7793 载荷/209 源码 SHA、163 安装态模块来源及33项有限验收曾通过。但真实恢复截图和独审发现 **18 辅助 TIFF 原图、9 原值裁图、4 Fig PNG 被映射为 `source.json`**。原始字节未丢，读取类型错误影响预览、改选来源及引导裁剪。R1 产物独审 **Blocked**，未发布桌面安装包；旧包、日志、截图不覆盖或改称 R2。

修复按持久化明确角色恢复来源/裁图为 TIFF、Fig 为 PNG，普通元信息仍 JSON，不依据不可信文件名猜测。SHA/大小、TIFF 单页/32MP/512MiB保持；PNG校验格式/CRC、32MP和解码预算。初稿额外64MiB限制已移除，全局普通成员512MiB和既有 OCR 独立限制保持。四个真实导出→恢复反例先 **4 failed/exit1**，修后连同既有恢复回归 **30 passed/6.05s/exit0**；移除额外限制后4项 **2.11s/exit0**。开发源码真实 UI 重开 **1 passed/9.41s/exit0**。详见 `restore-image-roles.md`；首次 helper 路径缺失 collection exit2 也保留。

R2 首轮 `c3df3a5` CI：Linux 1295 及 wheel/规则/桌面成功，Windows **1294 passed、1 failed/759.97s**。失败测试在第二次关闭前未等真实后台空闲；受控真实读表反例先 **1 failed/2.62s**，补齐空闲和新未保存编辑前置后，受控及相邻路径 **3 passed/3.98s**。原状态断言、3000/20000ms时限、产品与门禁不改。历史 CI 具体后台工作仍 UNKNOWN；不能推断一定是自动保存。详见 `ci-session-precondition.md`。后继 `f1e6142` 四项检查成功，不改写首次失败。

## R2 安装和可分发包验收

| 项目 | 真实结果 |
| --- | --- |
| 构建冻结及环境 | `f1e6142` 构建 exit0；隔离 Python3.12.14、Qt6.12.0、38个已安装发行包，`pytest_present=false`；离线运行环境/模型/运行库及许可在随包环境和构建清单中 |
| 实际安装升级 | 安装到 `C:/Users/70236/AppData/Local/Programs/BioImage WB 实验室版`，install_exit0。R1旧哨兵与本轮新哨兵安装前后SHA分别保持 `AF7AAA…1F47` / `2264E7…5834`；完整摘要见 `install/before.json`、`install/installation.json` |
| 安装载荷与产品来源 | 7793个构建→安装文件、209个源码→安装产品文件核验，failures为空；163个实际加载模块均来自安装目录且SHA与构建一致。产品和Qt不从开发树导入 |
| 随包自检 | `--verify-installation` / `--verify-supervision-installation` 均通过，7/19项检查，selfcheck_exit0；`selfcheck/selfcheck-receipt.json` 及两份实际诊断 |
| 安装态有限验收 | **37 passed/53.91s/exit0**；包含拖入入口、未审核导出、旋转、裁剪门槛、完整项目及强化恢复。27来源/9原值裁图/4 Fig/27缩略图全部通过；4 PNG均实际CRC核验和解码。安装态模块失败列表为空 |
| 随包合成练习与恢复 | 两张确定性合成 TIFF 来自真实安装态未审核导出测试，完整项目及恢复通过；`installed-ui/practice/practice-receipt.json`。质量标志有意保留，不把练习当科学真值；安装包未放入私有180原图或截图 |
| 有界进程复核 | 套件退出后只读快照 observed_count0；`installed-processes-after.json`。没有强制终止，不推断一般退出/GPU问题已根治 |
| 交付暂存 | 新R2目录/ZIP含201文件，`staging-receipt.json` 为 `staged-not-published`；包含安装器、中文指南、环境/许可/源码、校验入口和合成练习。该暂存收据本身不证明桌面完成；桌面另有最终交付收据 |
| 最终产物独立审查 | **Accepted**；独立复核7793载荷/209源码/163模块、37项JUnit、恢复原值和PNG、全部201暂存文件及ZIP成员/SHA/CRC。报告原样保存为 [final-artifact-review.md](final-artifact-review.md)，绑定准确安装器/ZIP摘要 |
| 桌面完整目录、ZIP与原生解压 | 已交付 `C:/Users/70236/Desktop/WB-T081` / `WB-T081.zip`；201文件、总文件字节404489016，ZIP397078977 bytes。WindowsPowerShell5.1原生解压exit0，201文件与暂存相同；独立审查后的恢复校验exit0。原publisher整体exit1仍保留，详情见下节；旧交付不删不覆盖 |

- R2 安装器：`BioImage-WB-Lab-Windows-x64-f1e6142ab41e-Setup.exe`，383952574 bytes；SHA256 `d4ff255ad422cc183b98c46dc39b6486035b9b79b4b438803d9baa46429c2d36`。
- R2 暂存完整ZIP：`.local/T081/package/r2/WB-f1e6142ab41e.zip`，397078977 bytes；SHA256 `8581bc080464a8300aeba1eaca8e7c270840d42ba4110c1ee09be295a28705db`；桌面同字节副本为 `C:/Users/70236/Desktop/WB-T081.zip`。
- 实际稳定安装产品已更新为 `f1e6142ab41e16c66cfeb3d33958ab3a364581b1`；该事实不替代最终独审和PR合入。
- 构建执行入口：`uv run --locked --no-sync python -X utf8 -m tooling.build_runtime_candidate --laboratory --iscc <固定Inno6.7.3> --gcc <固定MinGW>`，exit0，`build-exit.json` / `build.log`；工具绝对路径及SHA见 `preflight.json`。后者仅为预检，不独自证明构建运行。
- 安装由 `install_update.ps1` 运行，安装器退出码0；`verify_payload.py` 验证冻结源码/构建/安装，`selfcheck.ps1` 调随包PowerShell5.1自检。参数接口及真实绑定结果分别见脚本与 `install/installation.json`、`payload.json`、`selfcheck/selfcheck-receipt.json`，不补造未保存的完整命令行。
- 安装验收使用安装目录 `runtime/python.exe -I -X utf8` 执行 `installed_acceptance.py`，绑定准确HEAD、release-gate、payload和新输出目录，exit0；`installed-acceptance-exit.json`、日志及 `installed-ui/acceptance.json`。开发pytest只作外部测试台，未装入产品。Qt平台为offscreen、`--disable-gpu`，不声称物理拖放/DPI全覆盖。
- 以上新收据和暂存产物均在 `.local/T081/package/r2/`；R1原始文件未替换。本次文档核对读取真实JSON/日志并检查恢复结果截图，没有重跑构建/安装/Qt或改产品。

## 桌面发布的首次失败与恢复校验

首次 `publish_local.py` 已复制到全新桌面路径，系统 WindowsPowerShell5.1 `Expand-Archive` 返回0，完整解压树及ZIP核验均成功；随后运行解压目录原 `verify-installer.ps1` 时，`Get-FileHash` 无法解析，进程exit1，publisher整体 **exit1**。该次没有生成成功交付收据。原日志 `publish.log`（SHA256 `5d2088f600f2e33455e2415f326e221d1ca4d7c4467314b9432796e289e71af1`）及失败保留，不能把原publisher改记exit0。

只读 `publish-environment-diagnosis.json` 显示，维护终端继承的 `PSModulePath` 将PowerShell7 Utility模块放在WindowsPowerShell5.1内置模块前，`Get-Command Get-FileHash` 返回null。独立子进程只将其环境变量限定为系统 `WindowsPowerShell/v1.0/Modules` 后，原命令可解析为 `Microsoft.PowerShell.Utility`，control exit0。没有改全局或用户模块设置。

恢复脚本 `resume_publish.py` 经非作者独审Accepted，报告/回执为 `publish-resume-review.md` / `publish-resume-review.json`，绑定脚本SHA。真实命令 `uv run --locked --no-sync python -X utf8 .local/T081/package/r2/resume_publish.py --repo .` **exit0**，见 `resume-publish-exit.json`。它先复核准确源码/CI/独审及既有桌面完整树、ZIP、原publisher失败位置，再在上述进程独立环境中运行**同一份、未改字节的**解压后校验脚本。`resumed-checker.json` 记录exit0及 `PASS: installer checksum matches this delivery.`，完成后再次核验全部桌面文件与ZIP。

最终 `desktop-delivery.json` 为 `phase=delivered`，明确保留 `original_publish_exit=1`、`extract_exit=0`、`extracted_installer_check_exit=0` 及原日志/独审/恢复回执摘要。没有重新复制、重复解压、删除、修改安装器或校验脚本，也没有降低原SHA校验；桌面ZIP仍为 `8581bc080464a8300aeba1eaca8e7c270840d42ba4110c1ee09be295a28705db`。

产物审查本身曾因审查脚本将Git归档的 `.cmd` 与原LF blob直接比较而exit1；查明仓库指定该唯一文件 `eol=crlf` 后，仅按已有属性处理该文件，其余源码仍逐字节校验，复核exit0。此为审查方法修正，未改产品/门禁；两个日志及报告均保留。原样报告描述的是其审查当时状态，之后发布结果以上述实际交付收据为准。

## 真实限制与使用说明

目标为 Win10 1809+/Win11 x64、普通用户安装；R2 已在本机 Win11完成上述安装验收。干净 Win10、全部员工硬件、物理 Explorer/OLE/DPI、全部 GPU 和外部表格软件未经普遍验收，不承诺所有设备无条件可用。

给定输入属于已见开发素材，一次完整项目自动运行与原值完整性，不证明 **80% 独立项目均能100%自动裁剪通过**，也不证明蛋白身份或科学准确性；没有独立留出项目库与人工真值。保留事后复核/修正能力。

从完整项目 ZIP 恢复时，导出尚在活动状态的历史记录按既有契约标记 interrupted；已完成裁剪和测量保留，选择新输出目录后继续。这与 R1 图片类型缺陷分开，不应隐藏提示或覆盖历史输出。

安装验收日志仍有 SharedImageManager mailbox 提示与10条弃用警告，37项功能断言通过不能证明一般GPU或原生退出根因已解决。安装器未商业签名，当前交付为本地目录和ZIP，没有公开上传私有原图或二进制。旧交付和历史保留；本轮未重建视频聊天或周期任务。
