# T080 最终安装交付证据（2026-10-23）

## 冻结版本与集成

产品/构建提交 `79b9db9b7ae055bc3354a3582777082729ca8110`，独立源码审查 Accepted。PR40正常合入main `a4646608a965202c38b0f1dee9dd45607a8c5bf7`；完整Git树diff为空。安装包准确标原审查/CI提交，不冒充合并SHA运行了同一检查。

GitHub quality run39933901590：Linux1265测试/363.63s及全部隔离wheel成功；Windows首轮1265/813.61s全部通过，但15分钟总时限在wheel开始时取消，完整检查当时未通过。只重跑失败Windows一次，1265/754.17s及全部隔离wheel成功。四必需检查最终全部SUCCESS（另native-case按既有条件SKIPPED，不是必需项）。未改门禁、时间预算、依赖或锁文件。首次f363f37失败及修复详见ci-integration-failure.md。

## 需求逐项核对

| 要求 | 实际证据 |
| --- | --- |
| PNG无损转换、180失败及大倾角诊断 | input-evidence/manifest.json含39原文件SHA；3PNG逐像素TIFF副本；baseline与crop-validation.md、研究文件记录根因与约−17.4°原图 |
| 常见明显条带优先，固定N/弱槽/缺失不伪零 | 新policy4及科学影响独审；最终common-ci-guard-v2-impact有21来源案例全部自动采纳，9采集组双来源及3PNG；39原文件/副本/历史基线未改。强第三带/doublet反例拒绝、N内弱槽保留、71项定向回归通过 |
| 实时旋转与量化分离 | 主框拖柄/输入/撤销/复位/边缘校验，范围±30；纯角度保原值ROI/槽/请求身份。安装态27项含实际旋转验证 |
| 完整命名Fig项目、所有原图、对应裁图、预览/单Fig/总拼图/总分表/恢复 | 真实180九组与PNG三组后台自动完成，149/50成员公开inspect核验；最终安装态合成2Fig完整项目及恢复、未审核表格和四直接入口通过。未注册伙伴3原图保留/仅所选1裁图反例通过 |
| 有界独审/CI/PR | 79b9db9源码独审、全部必需检查、PR40正常合入；源码自验不冒充独审 |
| 完整离线环境及实际安装 | 构建exit0，稳定目录更新安装exit0；旧/新用户哨兵SHA保持；7791构建→安装文件、207源码→安装产品文件核验，无额外旧产品代码；隔离Python3.12.14、Qt6.12.0、38个已安装发行包、OCR模型/VC运行库，无pytest |
| 安装后实测 | 随包PS5.1灰度/OCR与supervision双模式exit0（7/19检查）；安装目录运行27项UI/导出/恢复测试，24.12s/exit0，模块路径和SHA确在安装目录。测试依赖仅外部测试台，未安装进产品 |
| 实际可分发包 | 201个成员含离线安装器、中文指南、环境清单、许可/源码、校验脚本及合成原图+完整练习项目。ZIP CRC/逐成员SHA/大小由作者与独审分别核验；最终复制桌面目录和ZIP逐文件/整ZIP再次一致 |

## 交付与摘要

桌面目录及ZIP：`WB-实验室完整安装包-20261023-T080` / 同名.zip；旧WB、旧WB.zip、T079备份、旧dirty树及视频树保留。当前稳定安装已更新到79b9db9。

- 安装器：`BioImage-WB-Lab-Windows-x64-79b9db9b7ae0-Setup.exe`，383923941 bytes。
- 安装器SHA256：`fcc63932b624a58d904b7f2985395bf4f3233463451b7fcd0a0e03e57ed08c5d`。
- 完整ZIP：397029900 bytes；SHA256 `525d4a55af3460ec1273bf29e2956a98973e4d569b05e121069ac214bbd9460f`。
- 本机真实收据：ignored `.local/T080/package/` 内 release-gate/preflight、install/installation、payload、selfcheck/selfcheck-receipt、installed-ui/acceptance、staging-receipt、desktop-delivery JSON及原始日志；产品与最终产物独审副本见本目录相应MD。
- 构建命令：`uv run --locked --no-sync python -m tooling.build_runtime_candidate --laboratory --iscc <已固定Inno6.7.3> --gcc <已固定MinGW15.2.0>`，exit0；安装/载荷/自检/安装UI/staging/桌面复制命令均exit0，精确参数脚本和日志在上述ignored目录PLAN.md。本收尾仅文档，不重建或改动已验包。

## 真实限制

目标安装为Win10 1809+/Win11 x64，普通用户安装。已验为当前Win11工作站；不能保证所有工作人员硬件、干净Win10、物理Explorer/OLE/DPI、全部GPU或外部表格软件均已验。首次部署运行随包环境自检及练习。

给定两目录是开发素材：其两项目工程流程全部自动完成不等于独立科学真值通过。没有独立项目库/人工真值，整项目A/B/C泛化比例和80%目标未统计验证；21来源案例不能充作21独立项目。保留科学复核与事后修正能力，不声称通用100%正确。

安装UI日志有SharedImageManager mailbox提示，27功能断言通过但不证明历史GPU/原生退出根因已根治。新包未商业签名；没有公开GitHub二进制发布、私图上传、再次创建视频聊天或周期任务。
