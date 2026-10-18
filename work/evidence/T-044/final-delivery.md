# T-044 最终本地交付记录

产品提交 `a72e7102891df287e3484f20f3724612779b53f5`，基线d11552c32b87538e33ef3bfbe70fb3797e3f403e；本文为文档后继，不修改已验证的产品代码。Windows本机、锁定uv环境、当前绿色WebWorkbenchWindow。

## 完整检查

`uv run --locked --no-sync python dev.py check --all`：**733 passed in 525.53s，pytest原子进程0、全部隔离wheel和最终dev实际0**。包括Ruff、格式、Pyright、导入契约、真实桌面关闭、OCR与PNG worker，启用原生异常观察和Qt对象清单。日志/回执.local/t044/check-final-core-boundary.*，结束2026-10-18T14:34:50.3973170+08:00。

上一轮8e4de82虽然733用例通过，核心wheel缺PIL使最终check退出1；失败保留，见wheel-import-boundary.md。新修复延迟可选显示依赖，核心无PIL安装检查加严，没有补装依赖或跳过旧检查。

## 真实8原图

正常工作台目录导入→8真实worker→4Fig完整成图→8次审核回存→保存重开→关闭，实际exit0，无结果注入。证据.local/t044/final-workbench-20261018T062442Z/validation.json，预测冻结SHA `9dd6f108ec222920c00e31035ff4d23f8f7b579c3396c0f5b60dce88543f5271`。本次参考像素未读，逐源几何/完整成图像素与T042已评分结果一致；独立只读核验实际exit0。

沿用T042严格标准：目标膜/行正确、N匹配、所有band完整、无Marker或邻行；不要求完全消除弯曲。单图是二元评分，旧值沿用T040记录，本轮不重新读取参考评分。

| 原图 | 旧N | 当前N | 旧正确率 | 当前回归评分 |
|---|---:|---:|---:|---:|
| 1D ABCA9 | 1 | 8 | 0% | 100% |
| 1D β-actin | 7 | 8 | 0% | 100% |
| 1F ABCA9 | 4 | 4 | 100% | 100% |
| 1F β-actin | 1 | 4 | 0% | 100% |
| 4F NSUN6 | 1 | 8 | 0% | 100% |
| 4F β-actin | 7 | 8 | 0% | 100% |
| 4H NSUN6 | 2 | 4 | 0% | 100% |
| 4H β-actin | 4 | 4 | 0% | 100% |

合计1/8（12.5%）→8/8（100%），仅固定开发回归集；4F NSUN6右端少量膜边缘、部分残余倾斜/曲率按既有评分限制保留。不是独立留出泛化率。

48槽7valid/41quality_review→13valid/35quality_review，背景不足21→2，33零值风险仍保留。没有独立积分真值，**不是积分准确率**。扩大背景范围的二次背景反例约31.5%偏差，未发布扩大上限策略。原像素与公式保持。

8源SHA不变；8份正式回存各为显示PNG、原值TIFF和最后JSON，直接原文件夹新增24文件、不覆盖；独立核对来源/输出SHA、位深、原ROI像素、显示与成图对应区域及嵌入映射。诊断期间其他输出同样保留。31份旧结果作者进程前后SHA一致，但前态仅进程RAM，独审不能复算历史差异；current-ledger只作未来基线。重开行和8运行相等为作者Qt回执，独审未重复GUI。

## 独审、界面与保留限制

各产品阶段绑定独审见任务；a72e710独审11项3.31秒实际0、隔离API/发现不加载PIL检查0，无阻断；最终8图产物独审实际0。8e4de82弹框迟到关闭修复独审1项7.18秒0。作者独立wheel实际0，独审查看日志未重跑整套安装。

机械detector恰好一次85项；初轮6张实际Qt截图后修复弹框迟到事件，确认8张截图，保持绿色界面。部分离屏resize视口陈旧、DOM对象指标为空，不算全DPI/物理Windows验收。设计sidecar/PRODUCT过时保留待办。

21工作树59本地分支，6干净历史树原位锁定；原19树备份/34原未提交文件待最终allrefs再核验，当前4未提交文件已外置唯一目录核SHA。Git不备份私有原图/忽略结果。T044按阶段9草稿PR接stage-08，不直接合128提交到main。远端CI/备份/PR以GitHub和后继记录为准。

本轮完整成功不关闭历史间歇原生退出UNKNOWN；独立科学真值/留出、恢复演练、干净Windows最终包和全DPI交互待后续。维护说明见docs/maintenance-plan.md。

## 阶段同步

[草稿PR #15](https://github.com/Junweiiii14/bioimage-tools-platform/pull/15)已创建，base stage-08=d11552c；main仍221a2df，原阶段链保留。407083e全引用bundle已verify并再核原34未提交文件，SHA 1a40a4da10723b86026348741892296fbe4baf14ac0b125379b8341758b1cf2a。当前4未提交文件另存外置唯一目录并核SHA。本文最后文档后继将另建完整bundle，最新索引.local/t043/backup-final.json；GitHub开发日志issue6记录最新摘要。远端CI在本文提交时仍运行，实际结果见PR最终HEAD；不由本机通过推断。
