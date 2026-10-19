# T-048 Windows 10 零开发环境离线测试版安装包

- 状态：local-package-accepted / test-distribution；2026-10-19用户明确候选继续作为测试版，不正式上线。离线包与本机安装验收通过；干净Win10实测仍未完成，不据此宣告正式上线。
- 基线：edfc8507663b03ddef609c01fdba01eb3f32b53d；复用t045候选checkout和codex/t045-wbquant-manual-and-fig，不新增worktree，不改原版/原图/用户窗口，不发布main或网络下载站。
- 范围：核验Win10系统/位数要求，检查所有本地运行库与延迟DLL依赖，制作离线安装器、必需快捷方式/卸载/版本标记、交付校验和与简明说明，执行可获得的环境验收与绑定独审。
- 当前已确认：用户目标为64位Win10，版本未知；最低支持1809/build17763，安装器拦截更早系统和非x64。宿主Windows11 Home x64 build26200，没有发现VirtualBox/VMware/QEMU/Hyper-V命令；不能把本机通过写成干净Win10通过。
- 沿用T047私有CPython3.12.14与uv.lock产品依赖，不下载/升级库以掩盖兼容问题；科学公式/UI布局不变。安装包、模型、原图均保持ignored，不提交。
- 验收：离线完整依赖；明确拒绝不支持的OS/架构；桌面/开始菜单与卸载必需；非管理员可安装；不依赖PATH/Python/uv/VC开发环境；真实worker/OCR/保存重开/取消退出；完整产物摘要和独立审查；干净Win10实测条件/缺口如实记录。

- 产品提交3821c64：独立Win10Test AppId/目录/QSettings；桌面和开始菜单必建；私有Python/固定wheel/本地VC++/OCR模型；开始菜单PS5.1自检与独立报告；原版和旧候选均保持。
- 13项专项/Ruff/format/Pyright/policy exit0；非管理员安装和卸载重装0；实际安装七项GUI/worker/OCR/保存重开/退出通过、无残留、无开发模块。初次观察器null退出码记录保留，v2完整通过。独审ship绑定3821c64，两项P2已修复。
- 详细证据和来源：work/evidence/T-048/{validation,research,independent-review}.md。构建产物与完整日志ignored；无PR/main/正式发布。
- 交付：桌面 BioImage-WB-Win10-测试版-T048 文件夹，Setup.exe 361325507字节、SHA899082492c10ae94e5638ef1eb6517a8cc6eaa1b30235b81ecccd1706c4930b4，附说明与SHA256SUMS；本机重装7721文件摘要一致。
