# Handoff Snapshot

- 更新2026-10-19。当前唯一任务状态源 work/tasks/T-048-win10-offline-test-installer.md；本机离线测试包交付/独审通过，干净Win10实测未完成，未PR/main/正式上线。
- 只复用 C:/Users/70236/.codex/worktrees/t045-wbquant/bioimage-tools-platform，分支codex/t045-wbquant-manual-and-fig；T048 baseedfc850，产品3821c64a7068f2108fda15fcaf72d72f7f0da035，核对实际HEAD/dirty。无新增worktree，原ResearchVault dirty及旧树不动。
- T048用户确认x64 Win10版本未知：最低1809/build17763，独立Win10Test安装目录/AppId/设置空间，必建桌面/开始/自检/卸载。固定wheel与私有Python、本地VC DLL及OCR模型，无目标机联网安装依赖。普通安装器预设，无新UI布局/动画设计。
- 交付 C:/Users/70236/Desktop/BioImage-WB-Win10-测试版-T048/，Setup文件BioImage-WB-Win10-x64-Test-T048-3821c64a7068-Setup.exe；361325507字节，SHA899082492c10ae94e5638ef1eb6517a8cc6eaa1b30235b81ecccd1706c4930b4，附说明与SHA256SUMS。
- 实际非管理员Win11安装/卸载/重装0；七项安装GUI检查8.047s，外层14.2036s/exit0/无所属进程残留/无开发模块。MSVC均来自应用内；PS5.1自检0、失败CMD返回1；7721文件SHA一致；独审ship绑定3821c64。初次PS5.1外层观察器exit=null失败保留，v2由现有pwsh控制器完整通过，无产品掩盖。
- 目标干净Win10未跑：本机Win11 Home26200无发现可用VM。不要写成目标实测通过；下一步用户目标机安装/自检反馈。具体证据work/evidence/T-048/{validation,research,independent-review}.md与ignored .local/t048。
- 本机另装 C:/Users/70236/AppData/Local/Programs/BioImage WB Test；桌面BioImage WB（测试版），旧T047候选仍在。原TIFF/旧两个lnk摘要及Candidate设置不变，用户11004/41220/55936/55440四进程仍响应；先核对PID再操作，禁止清理用户窗口。
- 已批准58339入口/退出预览并实现：首页原图/文件夹/已有项目、直达灰度、恢复页面/Fig/泳道、真实最近项目、同窗切换宿主与epoch、可见取消/草稿/保存/失败/退出流程。科学schema/公式不变。
- 最终源码完整769passed659.96秒，全部隔离wheel/dev0；取消后重新确认草稿P1在53a2030已独审关闭。后继仅诊断/打包/文档，无科学UI变化。
- 全AOT632编译/安装成功但真实GUI初始化exit3/OCR缺动态模块，未交付；c8重建停止。失败UNKNOWN保留。最终采用同版本CPython3.12.14私有运行库、锁定产品依赖和四wheel，原生Windows入口，仅管理自有Job/退出码/标准流。不是依赖本机Python或UV。
- 当前已安装 C:/Users/70236/AppData/Local/Programs/BioImage WB Candidate；桌面和开始菜单入口 BioImage WB（候选版）。安装器 `.local/releases/runtime-b6df40edf2be/BioImage-WB-Candidate-T047-b6df40edf2be-Setup.exe`，360638287字节，SHA37865a43f7eed96be4ec410628814c8990c634a755c5636bdbf2414a3bcb18bc。
- 实际安装正常Windows GUI七检查11.516秒passed；控制器22.442秒/exit0/所属六PID全部退出/316模块无开发路径；真实OCR及定量协议passed。报告 `.local/t047/installed acceptance/final report.json` 与精确 `final report.json.process.json`；worker/入口报告 `.local/t047/installed-runtime-*`。原00060263(1).tif与原桌面开发快捷方式摘要一致。
- 从新桌面快捷方式已启动给用户：`.local/t047/installed-user-launch.json`，记录父55936/窗口55440、标题BioImage WB · 候选版、响应正常。后续须重新核对PID。不要关闭用户这个窗口、旧版/旧试用窗口；新首页未自动导入用户原图。
- 独审最终对b6df40e关闭第二项、ship仅本轮两项评分范围。documenter更新PRODUCT/surface，DESIGN/sidecar保持。干净Windows、DPI、物理按钮、科学准确率未验收。下一步只响应用户试用反馈，不自动扩展路线图。
- 完整证据 work/evidence/T-047/validation.md；历史T046产品4d4944a、761门禁与全组审核/完整峰/UB逻辑保留。原始输入/已完成结果/私图/安装包不得提交覆盖。历史全局说明见AGENT_HANDOFF索引。
