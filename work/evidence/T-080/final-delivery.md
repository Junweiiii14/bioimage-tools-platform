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
- 构建命令：`uv run --locked --no-sync python -m tooling.build_runtime_candidate --laboratory --iscc <已固定Inno6.7.3> --gcc <已固定MinGW15.2.0>`，exit0；安装/载荷/自检/安装UI/staging/桌面复制命令均exit0，精确参数脚本和日志在上述ignored目录PLAN.md。收尾包含文档、测试就绪同步及CI总预算修正；不重建或改动已验产品包。

## 真实限制

目标安装为Win10 1809+/Win11 x64，普通用户安装。已验为当前Win11工作站；不能保证所有工作人员硬件、干净Win10、物理Explorer/OLE/DPI、全部GPU或外部表格软件均已验。首次部署运行随包环境自检及练习。

给定两目录是开发素材：其两项目工程流程全部自动完成不等于独立科学真值通过。没有独立项目库/人工真值，整项目A/B/C泛化比例和80%目标未统计验证；21来源案例不能充作21独立项目。保留科学复核与事后修正能力，不声称通用100%正确。

安装UI日志有SharedImageManager mailbox提示，27功能断言通过但不证明历史GPU/原生退出根因已根治。新包未商业签名；没有公开GitHub二进制发布、私图上传、再次创建视频聊天或周期任务。

## 收尾 PR41 检查修正

1fbf2dc 的 CI39939061612：Linux 1264通过/1失败（521.55s），test_crop_edit_identity的session参数在初始crop-overlay可见等待超时，尚未执行会话替换。现场没有mode快照，唯一根因未证实。本机原测试5通过/7.20s。
代码检查和独审确认测试准备存在竞态：native保存结束不等于初始会话路由已消费；晚到的quant路由能覆盖测试刚选的review。5c788d3等待native idle、同项目/epoch网页quant路由，然后只切一次review；原overlay 10秒、真实pointerdown单次发送/拒绝必须失败、原像素和旧编辑拒绝断言保持，并增加失败诊断。修后5通过/5.64s，Ruff及Pyright退出0。
Windows同run全部1265通过/796.59s、全部wheel及末尾Governance成功日志已出现，但作业15m1s取消，不能算CI通过。这是第二次全量通过而总预算不足，foundation预算15→20分钟经独审评估；检查内容、required名称、故障传播、测试超时均不改。新HEAD仍须正常四CI成功后合入。
原日志保留ignored .local/T080/package/closeout-linux-failure.log及closeout-windows-failure.log。此修正无产品/依赖/安装器变化，安装包仍绑定79b9db9。首次提交因未激活pre-commit失败；恢复项目venv PATH后实际三钩子通过提交，未绕过。

独审受控探针仅确认“真实sessionStateChanged晚quant route能将已可见review overlay隐藏”。人工fresh-token对照与宿主position回报token不一致，新顺序对照未全部通过，不能当成新的产品失败或对照成功；首探针停止整个session_timer和清理参数错误也如实保留。停止扩展探针，不以其覆盖5项真实测试通过。5c788d3源码增量独审Accepted，完整探针与边界见closeout-independent-review.md；原CI唯一根因仍未证实。


cd62be8 的 CI39941601014：Linux1265/495.24s及全部wheel成功；Windows1264过1失败/618.94s（不是超时），手动泳道真实拖动期望35,40,20,40而实际39,43,16,37，终点55,80一致。原日志closeout-windows-final.log保留。测试原先仅等两RAF，motion.js进入动画320ms仍可能改变DOMRect；image_point到真实pointerdown之间重取rect，存在布局竞争。新增10秒内等待动画自然结束，再按原两RAF/真实Qt手势执行，abs1不变，附实际dragging起点/rect失败诊断；不finish/cancel动画。现场未采样rect，唯一根因未证实。定向原测试1通过9.10s；Ruff格式首次要求重排后修正，Ruff/Pyright0。独立审查认可该最小就绪修正，未新增人工探针。产品和安装器字节继续保持，后继准确HEAD仍须完整CI。
