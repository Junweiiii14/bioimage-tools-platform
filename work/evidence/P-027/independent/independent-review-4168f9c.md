# P027 普通 WB 文件夹与参考组独审

**产品修复通过，候选 changes_required。唯一阻断 R01 位于任务卡。** 2026-11-09，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`。绑定 base `8321615773c73ede412e1a60b2688e545f537f8a` → head `4168f9c4b9d55f1fbc67b124244be15f0c0393da`。[PR79](https://github.com/Junweiiii14/bioimage-tools-platform/pull/79)

## R01 · P027 的状态无法登记

`work/tasks/P-027-wb-folder.md:3` 使用未定义的 active，head_commit 为 null。计划检查器第 12、74、87–91 行要求选择已定义状态，并为 in_review 提供 40 位受审提交。在隔离副本中仅将该卡调整为第一项，原检查器 exit 1 并直接指出 P027 的 metadata 无效。基线非法状态数为 0，本候选为 1。最小修复为将 P027 填为 in_review，绑定上述已完成产品和走查的 `4168f9c…`。历史 P010 等问题沿用原记录。

PR 的规则回执检查、git diff --check 均 exit 0。集成清单正确保留 P026 收尾来源，其完成卡指向受审的 45daa37。产品差异仅删除 intake_groups.js 的一处空数组赋值，既有测试改从真实按钮触发并保留原有识别、保存、重开断言。算法、数据格式、锁和门禁无变化。

## 空草稿与普通单图

独立检出、Windows x64、锁定 CPython 3.12.14、Qt WebEngine 离屏，使用隔离设置和项目目录。取已核 IOCBIO ZIP 中原名未改的单张 `gel1_GAPDH_expo1min.tif`，成员摘要 `af35f27d9171f1699a8247611dc48683833f03eae1ed30a1e795ad5966ab3a64`。从实际 WB 首页点击“选择仪器文件夹”，用 Qt 目录框选入只含该图的普通文件夹。

点击“识别来源与参考图”当下，未编辑的分组草稿保持干净。真实 worker 回包后识别为 unknown、regions 为空、error 为空。页面可以实际点击“添加 Fig”、输入 GAPDH 并勾选该原图。N 留空时启动按钮禁用，保存草稿成功。同一项目重开后 Fig、来源 ID、GAPDH、lane_count=null 与保存前完全相同，启动仍禁用。这里执行的是来源识别；P026 的固定 13 个样本泳道探针使用另一个公开入口，本次没有执行批次裁剪或积分。

对独立灰度入口只读复核作者证据。三种来源识别状态及独立灰度共 13 个界面片段与留存原记录一致，仅替换隔离目录路径。四个项目的原图均与 ZIP 成员逐字节一致，灰度原图页为 3072×2048、16 位、已框选 0 条泳道。四个项目的正式运行记录为 0。项目与界面证据相符。

## 已编辑草稿与参考组保存

| 独立实测操作 | 结果 |
|---|---|
| 已有保存过的 Fig，从页面点击识别，在回包前编辑 Fig 名称 | 后台摘要改变后，页面保留新名称、提示真实冲突并禁止覆盖。存盘的原名称仍在。显式重载后解除冲突。 |
| 识别参考组，点击“单列已识别的参考结果”并保存有效草稿 | 非空 reference_group_ids 与对应组匹配。参考组退出实验 Fig 分配，普通组继续保留蛋白和 Fig。项目账本中的已提交分组与页面一致。 |
| 在识别前已合法勾选潜在参考图并保存，识别后将它单列，再尝试保存 | 旧裁剪源选择保留。界面提示先取消原选择，启动禁用。点保存后宿主拒绝，存盘摘要不变，草稿和取消按钮仍在。点击参考区的“取消原有裁剪源选择”后保存成功，普通组上的 Target 保留。 |

最后一条在候选和基线页面分别复现。基线页面从准确 Git 对象还原唯一有差异的产品文件，使用相同宿主和 worker。两者对无效选择均拒绝且可恢复；候选修复了基线在无本地编辑时误报的冲突。这项修复不需静默清除用户选好的来源。

## 验证与边界

- 三项既有定向 pytest 用例通过，涵盖实际 worker 保存重开、后台草稿冲突和参考组顺序，exit 0，3 passed。见 `.local/focused-tests.log`。
- 主审单图页面探针最终 exit 0，1 passed。首轮未等待页面桥接就绪，在打开输入后等待超时；第二轮已走完选择、编辑与保存，但程序化重开早于宿主接收页面草稿状态。改为等待正常同步后，原有断言连同重开一致性全部通过。离屏渲染有 GLES/mailbox 提示。见 `.local/single-input-receipt.json` 和 `.local/single-input-final.log`。
- 参考组正例的两份早期独审脚本因 JS 换行导致提前 return 而失败；修正探针后 1 passed。基线/候选的预选参考图负例 2 passed。见 `.local/references/observations.json`、`.local/references/disk-check.json`、`.local/references/preselected-base.json`、`.local/references/preselected-candidate.json`。
- 作者原始文件、实际项目账本及界面片段的只读对照见 `.local/evidence/p027-source-and-walkthrough.json`；规则和元数据检查见 `.local/governance/review-4168f9c.json`。

工程结论限于上述工作台路径，独立灰度的按钮与零泳道来自留存观察。科学定量、真人操作及安装矩阵不在本次增量验收范围。
