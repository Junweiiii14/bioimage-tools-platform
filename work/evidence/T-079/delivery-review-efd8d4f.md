# T079 最终安装包增量独立审查：efd8d4f

**结论：Accepted，限本报告绑定的 efd8d4f 安装器及当前263文件交付内容。** e97阶段发现的目录拖入说明和两项运行依赖许可附件缺口均已在新安装载荷及外置材料中修复。没有未解决的阻断发现。后续仅追加验证记录、文件清单或CI收据仍需核对增量；本报告不预先签收未来ZIP、远端CI或main合入。

- product base：`e97d721e799397c22f3b5da4475f5f21e4720b56`
- product head：`efd8d4f8fa9cd6c3b86a291d49ede9ad54bb971b`
- 活动树：`C:/Users/70236/.codex/worktrees/wb-lab-installer/bioimage-tools-platform`
- 分支：`codex/t079-laboratory-delivery`
- 审查时间：2026-10-23 11:04:54 Asia/Shanghai / 03:04:54 UTC。
- 安装器：`BioImage-WB-Lab-Windows-x64-efd8d4f8fa9c-Setup.exe`，**383,860,684 bytes**，SHA256 **`571a66b3e214ea2167c2208e19b8c399c0e46ef7aef3c6548fd457f456b18b8b`**。
- 实际安装根：`C:/Users/70236/AppData/Local/Programs/BioImage WB 实验室版`。
- 构建根：活动树 `.local/releases/runtime-efd8d4f8fa9c`；交付根：活动树 `.local/t079-delivery-staging`。

非作者独立增量审查。未创建代理、修改产品/测试/脚本、安装/卸载、删除用户数据或终止进程。只新增本报告；反例操作限经绝对路径验证的自身TEMP夹具。开始和收尾HEAD为efd8d4f；既有e97阶段报告未提交状态保留。

## 范围与源码修复

承接 `independent-review-e97d721.md` 的发行配置独审，以及 `delivery-review-e97d721.md` 的实际包/清理阶段审查。e97旧包的Needs fixes仍是其真实历史结论；本新报告针对重建包关闭对应发现，不回写旧包成功。原清理三项阻断的修复、实际归档验证和数据保护Accepted结论详见e97报告。

阅读 e97..efd 全部差异。亲自执行 `git diff --exit-code e97d721e799397c22f3b5da4475f5f21e4720b56 efd8d4f8fa9cd6c3b86a291d49ede9ad54bb971b -- apps packages tools uv.lock`，**exit0、无差异**。应用、算法、项目/历史归档格式及锁不变。本次有效行为变化限打包许可复制与说明；新增文档明确项目文件夹入口、部署边界及私有安装方式。

- readme改为一次拖入一个仪器目录，多项拒绝，与T077契约一致。实际源码、安装内说明、外置01说明逐字节相同；旧“一个或多个”句子已移除。
- `tooling/third_party_notices/sources.json` 固定RapidOCR3.9.2、FlatBuffers25.12.19的版本、上游URL、文本摘要。实际许可全文按固定tag原始字节保存，RapidOCR版权行保留。
- `licenses()`在构建安装器前校验实际已安装发行版本、许可文件SHA；版本不符、文件改动或缺失会抛异常中断，未捕获后伪造成功。通过校验后复制为对应发行目录的UPSTREAM-LICENSE.txt，并带来源JSON。没有更改科学值或通过忽略异常继续发行。
- 许可补充是分发材料完整性修复；本报告不扩成全部许可证法律结论。

## 亲自运行的源码反例

`uv run --locked --no-sync python -`，原始`licenses()`函数在当前进程中仅将ROOT映射到经验证的TEMP副本；真实源和构建目录不变。四场景实际执行：正常复制；错误版本；改动一个许可字节；缺失许可。正常副本与预期SHA/来源JSON一致，后三者分别以异常拒绝。**外层exit0，5.729s，四例均符合预期**。

同时直接读取两个固定tag上游URL的原始字节并重算摘要，与工作树/来源清单相同：

- [RapidOCR v3.9.2 LICENSE](https://raw.githubusercontent.com/RapidAI/RapidOCR/v3.9.2/LICENSE)：`3e0af25fdd06aa9586ae97adb00ea927ebe5a3805ac77d2d3a81ce5f55693333`
- [FlatBuffers v25.12.19 LICENSE](https://raw.githubusercontent.com/google/flatbuffers/v25.12.19/LICENSE)：`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`

## 亲自运行的实际文件与运行库核验

以下stdin探针均以 `uv run --locked --no-sync python -` 启动；只读取实际包和原收据，不调用会重写作者收据的helper。运行库探针另使用实际安装python子进程，未加入源码/开发site。

| 命令/具体断言 | 实际结果 |
|---|---|
| 对 t079-efd-payload.json 全部7,788项，分别读取构建app与安装根实际文件；核路径在根内、大小、每SHA及40字符commit | **exit0，15.879s**；7,788双副本全部匹配 |
| 对204源码/资源映射逐个读取源与安装文件；对staging精确文件集合、大小和每SHA核对；仅允许一个Setup.exe；重算安装器大小/摘要 | **exit0**；204源码资源、当前263交付文件及安装器全部匹配，无旧e97安装器混入 |
| 比较源码/安装/外置readme全部字节；比较安装与外置全部142许可文件；两补充许可与源码、来源SHA逐项对照 | **exit0**；三份说明同，142许可同，两项新增许可全文及来源存在且匹配 |
| source-code.zip执行CRC；其中build_candidate.py、readme、sources.json和两个许可全文与 `git show efd8d4f:<path>` 原始字节对照 | **exit0**；CRC及五个增量文件全部匹配提交对象 |
| 外置构建清单与release清单逐字节对照；校验commit、schema身份/通道、compile_exit/installer_exit及uv.lock摘要 | **exit0**；commit=efd8d4f，BioImageTools.WB.Laboratory / wb-laboratory，两个构建退出码均0，锁摘要同当前源 |
| 实际安装 `runtime/python.exe -I -B -X utf8 -c <probe>`：TEMP cwd，PATH仅System32，故意注入含抛异常wb_tool.py的PYTHONPATH和VIRTUAL_ENV；检查模块来源/isolated/pytest/38依赖、调用固定OCR模型校验 | 私有子进程和外层均 **exit0**；五模块均从安装目录导入，isolated=1、pytest不存在；实际38依赖与环境清单相同；Qt6.12.0/Chromium140.0.7339.225，三模型SHA通过 |
| 读取安装用户哨兵并重算SHA | **exit0**；仍为 `dcd349e4c7544ed97c3592a6819550e9e656d50a289da0a8b4e66699dd709d58` |
| 真实Windows PS5.1 `-NoProfile -ExecutionPolicy Bypass -File verify-installer.ps1`；系统5.1模块路径；实际新安装器及TEMP中同名假文件/缺文件三场景 | 外层 **exit0，1.848s**；三个子进程实际退出码 **0、1、1**，错误摘要和缺文件明确拒绝；未执行安装器 |
| 审读CMD wrapper，核固定系统powershell路径、完整引号、Bypass、保存并传递errorlevel | 接线正确；未运行含pause的交互CMD |

安装三模型与e97相同，实际校验调用通过；没有让OCR在探针中下载模型。隔离探针支持模块来源、依赖与模型完整性，不能单独替代所有UI/worker场景。

## 安全示例与实际作者记录

亲自执行只读示例探针，**exit0**：从源码AST提取纯`membrane`函数，按±3°/无marker/dtype下限夹具重建，逐像素确认两张300×700 uint16图仍是原合成输入；完整项目含workspace.json/metadata.sqlite；CSV与项目自动主表整字节一致；XLSX主表XML和styles逐字节同；两个项目ZIP的CRC及唯一成员检查通过。没有把ZIP外层时间戳差异误判为数字或格式差异，没有替换为实验室原图。当前说明正确要求主界面打开示例项目文件夹。

以下为审读原始脚本/JSON/XML/stdout/stderr后的**作者运行证据**，本次没有重做安装、GUI诊断或19项测试：

- t079-efd-selfcheck-result.json记录更新安装退出0、PS5.1自检退出0，绑定正确commit和安装器摘要，用户哨兵保留。
- 两份实际Diagnostics报告：`20261023-105749-bd3681de21924496bf8306c3f42fad9e.json`，phase=passed/errors=[]，6.468s，7项worker/OCR/保存和退出确认；`20261023-105801-9f7403ba0fbe45b1b5f26806b3e86ab2.json`，phase=passed/errors=[]，12.203s，19项supervision_installed@1检查，实际安装runtime/package_file、隔离导入、wb-laboratory、真实worker和提交阶段记录一致。
- t079-efd-installed-acceptance.log/json/xml记录 **19 passed、10个Qt弃用warning，14.790s，errors0/failures0/skipped0，pytestExit0**。测试harness仍只为pytest/测试引入开发site，产品/worker/Qt检查来自安装目录；不将其表述成完全没有开发测试工具参与。
- 新两份诊断stderr仍有GLES上下文回退；第一份还记录shared-image mailbox消息。工程检查通过不能抹去图形日志，也不推出硬件GPU已验。
- 正常qwindows响应/CloseMainWindow退出0/无残留、卸载0/重装0的完整循环属于e97阶段真实记录；本轮更新安装和哨兵已另核，未虚报重新执行完整循环。应用/安装配方无相应行为更改。

六个失效StartMenu链接的后续可恢复移动也已亲自只读核验，**exit0**：原路径与失效目标不存在，六个归档文件逐SHA匹配且无目的名冲突。孤立WBQuant卸载登记因作者报告的自动审批阻止而保留；未重试或假称已删。原50目录/10卸载/6桌面失效链接及归档验证不重复执行，保留e97报告的真实边界。

## 证据绑定与保留失败

本轮核验时的收据SHA256：

- t079-staged-delivery.json（263项）：`a9c8e5ebad6d18613926e0628c4ec87f6e6665bf03dbedc0fce9dd0325e5368c`
- t079-efd-payload.json：`18c2e1657fdb52e869070b4ed74d8704f50055f192c12402e4fedb4ad8bc0973`
- t079-efd-installed-acceptance.json：`897ad09258c080eb049f22b337a741b36083d407029d4d9e22d28fd2b1f89c42`
- t079-efd-selfcheck-result.json：`2ac38132b7e9c57183b1f769dd13e8a04bb75db64e6fb5a20802493b3eaf7e17`

初次发现payload收据手拼commit多一个c、成为41字符；已反馈。作者将helper改为读取构建manifest并重跑，我实际重读确认40字符正确，随后7,788双副本独立复核通过。该笔误是证据绑定错误，未冒称载荷有问题，也未用其他收据遮盖。

初次复合探针在已完成全部载荷/源码/staging校验后，以工作树sources.json的CRLF直接比较git归档LF导致断言，命令exit1。定位后确认内容仅换行不同，改以`git show`提交原始字节比较五文件，exit0；另独立重跑全部载荷命令得到exit0/15.879s。实际notice全文、安装/外置来源JSON和readme仍按原始字节严格比较，未弱化摘要门禁。

## 结论与剩余边界

本次源码修复、实际安装器及当前263文件交付内容 **Accepted**。清理保护与归档Accepted继承e97阶段的实际证据；e97旧安装器仍作为归档/清理proof参照，不应再作为最终实验室包分发。

未验：干净目标Win10、物理Explorer输入/目标DPI/硬件GPU、多台实验室现场、独立科学真值/准确率、完整许可证法律审计、远端CI完成和main合入。没有把本机包态成功或软件图形回退推为这些项目通过。若后续源提交只有本报告/收尾记录变化，应以实际diff证明产品载荷来源不变；最终追加交付文件和ZIP仍需核内容及新摘要。
