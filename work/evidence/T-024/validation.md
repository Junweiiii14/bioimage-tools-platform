# T-024 验证与交付

环境：Windows / Python3.12 / 锁定uv环境；协调工作树 `t021-coordination`，分支 `codex/t024-platform-automation`。原目录旧dirty工作保留。基线2442d408，平台f32ebbb、画布fec4814、自动核心8f9b050、原始积分6044d64；极性修复02b28edf的两文件diff合入最终集成提交。

## 真实资源闭环

只读输入：用户 WB资料中 `20260519-BK10140126 WB检测/原始数据` 的10张TIFF。实际Qt平台、目录导入、后台定位、真实QProcess测量、提交、导出，无注入ROI/N/结果。最新独立交付目录为 `.local/deliveries/WB-platform-20261015-212916`，输出位于其中 `workspace/outputs/WB-20261015-212920-84db3a`。原图和产物不提交Git。

- 10张保留；5张自动获得裁剪/计划，21条泳道；5张无可靠候选，明确状态而非零。
- 21条均触发现有质量规则，原始积分保留、有效信号为空。此结果不等于21条可信定量或人工标注准确率。
- PNG/TIFF拼图、XLSX/CSV、JSON状态和项目、checksums及完整ZIP实际产生；ZIP经严格inspect恢复验证10行/schema8/5自动证据/0人工审核。
- 已有ROI图上移动/缩放后自动重算保留用户几何；修改旧结果失效。独立QTest鼠标探针验证新run和摘要刷新。
- 默认独立Source编号/独立Fig，不推断蛋白、实验组、内参配对；OCR和归一化的用户语义输入仍未自动化。

## 检查与修复记录

- 作者初轮GUI3项通过；平台/源图/工作流33项通过；核心分工40项及后续58项定向通过。
- 全量前置Pyright曾报新增测试Optional未收窄，已修复，无ignore。一次全量527通过/1失败/183.98s：旧兼容测试将8列作未知schema；合法新增schema8后改拒绝9，保留99/bool/string拒绝和schema8实测读取。
- 结果摘要由12位字符串改4位有效数字供窄栏阅读；显示测试16000对应文本改为1.6e+04，数值语义和完整表/导出未改。一次定向37通过/1显示文本失败，修正明确展示预期后25项通过6.78s。
- 实际跑数据曾发现默认同Fig宽/N不一致，自动新源改独立Fig；混合无ROI行过滤后列号间隙压紧且crop成员索引仍对应原项目，原项目不改。默认中文未知标签无可携带字体，改明确中性Source编号。
- 独审五个可复现P2已修：最新文档选序；同源显式light极性；新图被无关过期计划阻断；发现目录时关闭丢失；坏TIFF错误未入最终报告。独审复测退出0/4.96s，包含过期行+新行ZIP严格stage恢复。
- 第二位独立只读探针验证图上拖动/重算、发布后取消/关闭；发现重开未选原图导致空画布，已接入恢复后选中原图与摘要，回归断言真实canvas非空。
- 原Qt原生中止/停滞根因UNKNOWN仍保留，不以此次通过宣布修复。干净Windows未跑；远程CI/PR集成/发布未做。

## 视觉和文档

Impeccable用于原生Operate界面；Taste明确排除app screen，不强套营销网站。独立fresh视觉审查5张实际截图（1440/1100逻辑视口），初判fix：复核表截断、来源编号无法区分。一次修复与同样五视图回捕，reviewer给出两个resolved、remaining clear、disposition ship；该结论只覆盖两项视觉修复，不代表算法科学验收。documenter独立核对PRODUCT/DESIGN/token JSON，原生Qt平台枚举例外保留。

最终全门禁与绑定提交独审结果由收尾记录补充。

## 最终收尾

产品16f38777d8bf8262b429e4004413937dd55b0195。最终 `uv run --locked --no-sync python dev.py check --all` 退出0，532 passed/193.25s；Ruff与317文件format、Pyright0、9合约、隔离runtime/contracts/WB/desktop及OCR安装烟测通过。日志.local/t024-check-all-final.log。独审绑定本提交，无未解决可操作发现（限定审查范围）；五实际复现脚本.local/reviews/t024-five-repros.py退出0/5.24s，ZIP严格恢复通过。未推送或更改main。

独立交互复核同16f3877：`.local/qa/T-024-independent/replay.py` exit0/4.98s，拖ROI重算/发布后取消/发布后关闭/真实10图复制件重开四项通过。最新项目恢复5成功run、选中第2原图、摘要3行且画布非空。复核输出probe-results.json；该代理未自审其平台作者范围。
