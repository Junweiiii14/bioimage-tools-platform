# T079 实际交付与清理独立审查：e97d721

**阶段结论：Needs fixes（e97d721 实际交付包）；清理数据保护部分 Accepted。**

本报告绑定旧安装器，不能作为后续重建包的验收。作者已确认修复下述许可附件与目录拖入说明，计划重建；截至本报告未审新提交、新安装器或最终交付清单。已有独立代码审查 `independent-review-e97d721.md` 的配置差异结论保持，本次是实际文件、运行记录和清理结果的补充审查。

- base：`eec9cd2e0893a2e847d08f151c5bcce27675a8ae`
- product head：`e97d721e799397c22f3b5da4475f5f21e4720b56`
- 分支：`codex/t079-laboratory-delivery`
- 活动树：`C:/Users/70236/.codex/worktrees/wb-lab-installer/bioimage-tools-platform`
- 报告时间：2026-10-23 10:53:27 Asia/Shanghai / 02:53:27 UTC。
- 安装根：`C:/Users/70236/AppData/Local/Programs/BioImage WB 实验室版`
- e97 安装器：`BioImage-WB-Lab-Windows-x64-e97d721e7993-Setup.exe`；**383,850,002 bytes**；SHA256 **`73bff8cfc022c56afd468f77ee530c9d428fed93a1083bd07847146e353de9be`**。

非作者审查。未创建代理、安装/卸载/删除软件或用户文件、终止进程、修改产品/测试/脚本或提交代码。仅新增本报告；反例限经绝对路径验证的 TEMP 子目录，清理的也是自己的临时夹具。作者同期 README/docs 改动保留。

## 发现与待复核修复

1. **交付许可关联缺项。** 实际安装树有 139 个 third-party-licenses 文件，逐项摘要匹配构建收据；但其中无 RapidOCR 或 FlatBuffers 许可副本，运行库两者的 dist-info 也没有 LICENSE/NOTICE。source-code.zip 的 399 成员中只有项目内 wbquant143/LICENSE.txt，不能补足这两项关联。两者 METADATA 声明 Apache-2.0，其他依赖包含通用 Apache 文本，但当前包没有清晰标明这两项运行依赖的许可/来源通知。固定版本上游许可可读：[RapidOCR v3.9.2 LICENSE](https://raw.githubusercontent.com/RapidAI/RapidOCR/v3.9.2/LICENSE)、[FlatBuffers v25.12.19 LICENSE](https://raw.githubusercontent.com/google/flatbuffers/v25.12.19/LICENSE)。这是一项分发材料完整性发现；没有声称完成全部许可证法律审计。作者确认将固定版本、上游来源、文本 SHA 及副本纳入配方和最终包，重建后需复核。

2. **目录拖入说明与入口契约不符。** e97 安装内及 staging 的安装说明第二节第2步写“一个或多个仪器文件夹”，T077 入口要求一次恰好一个本地目录，多项拒绝。应改为一次拖入一个目录。作者确认修进安装器后重建，不用外置正确说明假称旧包内已修正。

3. **旧 staging 清单失效。** 最初 t079-staged-delivery.json 仅13项，02说明记776字节而实际已850字节，也未覆盖后加的完整示例项目文件夹。已通知作者最终重新生成整包逐文件清单；作者称后续已增为121项，仍会因以上两项修复刷新。本报告未签收该临时清单或未来最终 ZIP。主界面“打开已有项目”选择示例项目文件夹的当前说明已正确，ZIP另作归档。

## 亲自运行的实际文件与反例验证

下列均在上述活动树运行。stdin 脚本只读实际文件或操作自己的 TEMP 夹具，不执行作者会写收据的 helper。命令形式为 `uv run --locked --no-sync python -`，下表明确各段脚本的输入、断言和实际退出码，避免将作者报告冒充亲跑。

| 实际命令/输入与断言 | 实际结果 |
|---|---|
| stdin Python 读取 t079-payload.json；对全部7,785相对路径分别重算构建 app 与实际安装文件的大小/SHA，核路径在对应根内；204源码/资源逐个核源码与安装目标；重算 staging 安装器 | **exit0，21.853s**；7,785双副本、204源码/资源及安装器均匹配 |
| 安装私有 `runtime/python.exe -I -B -X utf8 -c <probe>`；TEMP cwd、PATH仅System32，故意设置 PYTHONPATH/VIRTUAL_ENV 指向含抛异常 wb_tool.py 的临时目录；导入五模块、枚举依赖、检查 isolated/pytest/sys.path、调用固定 OCR 模型校验 | 私有进程及外层均 **exit0**；Python3.12.14、Qt6.12.0、Chromium140.0.7339.225；isolated=1、pytest不存在；五模块均来自安装目录；实际38依赖版本与清单相同，未加载假模块 |
| 实际 Windows PowerShell5.1 `-NoProfile -ExecutionPolicy Bypass -File <staging>/verify-installer.ps1` | **exit0**；真实安装器摘要通过；未执行安装器 |
| stdin Python 启动同一真实 PS5.1 verifier；PSModulePath指定系统5.1 Modules，正例用实际包，另复制原脚本到TEMP，以同名假文件、缺失文件运行 | 外层 **exit0**；实际三个子进程退出码依次 **0、1、1**，错误摘要/缺文件都拒绝 |
| stdin Python 逐项核139许可文件与payload摘要，读取source-code.zip并执行testzip；解析19项和示例1项XML；重算当前用户保留哨兵SHA | **exit0**；139文件匹配（含一个无害的空REQUESTED元数据文件）；source ZIP399成员CRC通过；哨兵SHA与循环收据相同 |
| stdin Python 从 test_source_geometry.py AST 提取纯 membrane 函数，按实际测试的±3°/无marker及dtype下限夹具重建两张图，逐像素比较；比较示例CSV与项目自动主表，比较XLSX sheet1.xml/styles.xml；两个示例ZIP执行CRC与重名检测 | **exit0**；两张300×700 uint16原图精确匹配合成夹具；CSV整字节同，XLSX主表/样式同；两个ZIP可读且无重名成员 |

实际 OCR 模型校验通过：

- PP-OCRv6_det_small.onnx：`090f04abcd9d9a7498bc4ebf677e4cb9bdce1fe4197ddb7e529f1ef44e1ff94f`
- PP-OCRv6_rec_small.onnx：`6f327246b50388f3c176ae304bd95767ea6dc0c9ae92153ef8cbe210b3c14884`
- ch_ppocr_mobile_v2.0_cls_mobile.onnx：`e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c`

38项实际依赖包含四产品wheel、NumPy/SciPy/tifffile、PySide6/WebEngine/Pdf、RapidOCR/ORT/OpenCV及其依赖。隔离探针没有添加源码或开发site，也未启动GUI；它支持安装运行库来源/导入与模型完整性，不能单独证明所有工作流不依赖开发环境。

## 审计作者实际运行记录

以下已阅读脚本、原始 JSON/XML/诊断日志并检查其可支持范围，**没有独立重新执行安装、卸载、GUI诊断或整套安装回归**。

- t079-install-result.json / install.log 记录本安装器静默安装退出0，安装路径和包摘要一致。
- t079-installed-acceptance.json/xml 记录实际安装runtime的19项：**19 tests、errors0、failures0、skipped0，14.637s，pytestExit0**。helper先导入安装产品，再为pytest/测试代码添加源码和开发site，检查154个已加载产品/Qt模块来自安装目录。故它证明使用安装产品/worker/Qt的测试成功，不称为完全没有开发测试工具参与的运行。
- t079-selfcheck-result.json 记录实际 Windows PowerShell5.1.26100.9711运行安装selfcheck退出0。Diagnostics中的两份唯一报告均phase=passed/errors=[]：第一份11.766s，覆盖真实worker、离线OCR、保存失败可见、重开和退出/草稿确认；第二份11.047s，为 supervision_installed@1，19检查，记录真实worker及crop/compose/measure/export/repeat、原图不变、缺失不转零、可见结果/曲线和所属资源关闭。两个stderr保留了Chromium GLES上下文创建失败/回退日志，不能据“passed”抹去该图形限制。
- t079-install-cycle.json记录正常qwindows窗口 responding=true、真实句柄/安装python路径；CloseMainWindow后launcher退出0、安装根残留进程0；卸载0、重装0，用户合成哨兵两阶段保留。本次亲自重算哨兵仍为 `dcd349e4c7544ed97c3592a6819550e9e656d50a289da0a8b4e66699dd709d58`。没有将旧PID记录当作当前用户进程操作授权。
- 示例项目安装runtime打开记录：XML **1 test、errors0、failures0、skipped0，3.629s**。初轮仅等待10个placeholder就取raw值，作者记录失败；修正为等待同样的全部raw有值及idle，再保持原断言，成功不抹去初轮时序失败。主界面接收完整项目文件夹，未假称可以直接打开ZIP。

## 清理三项阻断与修复复核

原始方案的三个阻断已在执行前反馈并修复。最终清理脚本执行前后摘要一致：

- t079_cleanup.ps1：`9bb6dcc7c9e91c4680f047c7dda15344c3bbc441a264424dd53b4119d73f7751`
- t079_preserve_generated.py：`63e75757fdcaabc6cc3d32a63c7cd9c03f552eaaff643f73e782adfb4341236a`
- t079_preserve_desktop_complete.py：`9ad02ddae352cec93c5665b875883a5ecff7a1148f6fe860c8d2cf1d4f2cdf3e`

1. **保护路径可绕过**：原精确字符串比较可被尾分隔符绕过。执行前提取纯路径函数，在临时夹具复现；修正后统一绝对路径/去尾分隔符/OrdinalIgnoreCase，祖先与后代重叠均拒绝，逐祖先及树内reparse拒绝。独立7反例外层exit0：视频树尾斜线/大小写/祖先、lab子目录、reparse祖先/后代均拒绝，仅名字相近但独立的兄弟目录接受。未执行完整cleanup来试删。
2. **扩展名白名单漏备份**：原方案会跳过未知ZIP/PDF/NPZ/无扩展/pyc。新方案逐文件SHA，只有与保留payload逐字节相同、或旧manifest精确SHA识别的installer/wheel可重建，其余全部ZIP。独立在TEMP以原生成器和假repo位置执行上述未知文件/已知payload/精确manifest反例，exit0，未知项全部备份；真实清理前复核源集合和每SHA、ZIP摘要、保留引用。
3. **有效快捷方式可能误删**：原BioImage前缀规则过宽。修正为实际已移除旧安装根的目标，或确证目标失效；现存其他目标保留。六个legacy dead links还需目标仍相同且不存在、链接备份SHA一致才删。只读审查对应分支，实际动作收据仅六个已证实失效桌面链接，没有将软件名称当作其他软件/实验数据删除范围。

所有源树、未提交改动及外部原图/项目均不在目标目录删除范围。原preserve.py的desktop/exe和pyc缺口由desktop-complete及generated/remnant全文件保存补上，不能只凭旧脚本宣称完整。

## 清理实际结果与亲自归档核验

收据 t079-cleanup-result.json：2026-10-23 10:45:45+08完成。记录**50目录移除、10次旧版卸载exit0、6个验证失效桌面快捷方式移除**；旧BioImageTools.WB通道登记计数0。后者是该键名前缀范围的作者记录，不扩成全部其他软件登记均已清理。

亲自运行只读stdin核验，exit0：50目录和6快捷方式现均不存在；两个保护树与其.venv现均存在；10个卸载日志存在，收据退出码均0；上列三脚本SHA未变。逻辑移除60,325,925,956 bytes，收据可用空间差25,846,796,288 bytes，不能将逻辑体积当实际腾出空间。

归档根：`C:/Users/70236/ResearchVault/Codex-Workbench/WB-归档-20261023-T079`。

| 独立只读命令/断言 | 实际结果 |
|---|---|
| stdin Python重算master五归档整体大小/SHA；按595条记录读取实际ZIP成员重算SHA，校验无重名 | **exit0**；全部匹配。desktop-complete.zip为2,608,617,766 bytes，SHA `7a13283d0f723876d0e2b73f2b9f0d24803de4af2d41999f81158b62080bad8c` |
| stdin Python读取全部26 generated ZIP，重算整体SHA、精确成员集合/大小及每成员SHA；所有payload引用解析后必须位于kept_payload下，再重算摘要 | **exit0，79.569s**；196,272备份成员、206,009引用记录/7,671唯一保留文件全部匹配；89旧installer/wheel保留为已审manifest精确分类，未声称恢复旧生成包 |
| `git bundle verify C:/Users/70236/ResearchVault/Codex-Workbench/WB-归档-20261023-T079/repository-all-refs.bundle` | **exit0**；187refs，complete history |

此结论针对本轮已审核脚本与明确动作。作者另报孤立StartMenu/卸载登记删除命令被自动审批阻止、整条未执行；本次未执行或批准此类额外删除，也不将后续可恢复移动失效链接算入已完成事实。

## 保留失败与验收边界

- 一轮stdin阅读收据未显式UTF8导致GBK解码失败，exit1；改显式UTF8后通过，属审查helper错误。
- 通过Python从Codex进程继承PS7模块路径运行PS5.1时，Get-FileHash被错误的Utility模块遮蔽，校验器安全返回1。直接原生PS5.1调用通过；将测试子进程PSModulePath限定系统5.1 Modules后正/负三例通过。未修改随包脚本或宿主设置，未把该受污染环境当产品已支持。
- 初次归档helper把记录中的相对payload引用误当cwd路径，FileNotFound/exit1；改为解析到记录的kept_payload并核边界后，26包全量通过。
- 初次将两份XLSX要求整ZIP字节同，断言exit1；CSV相同，XLSX仅ZIP元数据差异，实际主表XML及styles逐字节相同。后续按可表达内容检查，未改产品或弱化其数值/格式预期。
- 定位命令曾读取不存在的文件/目录，返回1；随后用rg定位实际文件，未据空输出作结论。

未验：干净目标Win10、物理Explorer输入/目标DPI/硬件GPU、多台实验室部署、科学留出真值或准确率、完整许可证法律结论、远端CI完成及main合入。未独立重复所有19项包态测试或安装循环；表中已明确亲跑与作者记录。当前本机软件图形回退日志继续保留。

**最终阶段结论：清理数据保护 Accepted；e97实际交付 Needs fixes。补齐通知、修正一次一个目录说明、重建安装器并刷新最终清单后，必须对新提交/新SHA作增量独立审查，不能沿用旧安装器摘要签收。**
