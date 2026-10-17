# T-043：入口统一、分阶段同步与保留清单

## 当前入口

正常启动固定使用当前活动检出的 `Start-BioImage.ps1`，桌面快捷方式为“BioImage WB 工作台（当前开发）”。无参数、`--figure-project`、`--platform` 均打开当前绿色网页工作台。旧窗口只由明确兼容选项进入，关闭失败不再自动弹出旧宿主。测试默认离屏；模块地图和交接地图同步标注，历史检出不得当作当前产品演示。

## 门禁与独审

- 产品提交 `2e5021d`：完整 `dev.py check --all` 实际退出0，642项/361.62s，含全部隔离wheel；独立入口/环境14项通过，代码独审无确定阻断问题。
- 治理前置 `0b786cb`：独立锁定环境完整检查44项/165.88s，退出0，Ruff/format/Pyright通过；独审6项拒绝路径通过。首次无独立venv的运行退出1，补齐原锁定环境后重跑通过，没有修改依赖或门禁预期。
- 合并治理后的最终开发树e0be945全量检查真实退出0：657项/427.30s，Ruff/format/Pyright/import/policy及全部隔离wheel完成（.local/t043/check-final-integrated.log）；后续仅文档/回执整理。原生Windows交互式间歇挂起根因UNKNOWN；离屏检查不能作为原生显示/交互或科学泛化验收。
- 八阶段整理经独立逐文件核验，产品快照一致，前置祖先链连续，8份显式清单均退出0；绑定HEAD详见阶段任务及本次独审记录。此复核不替代各历史产品阶段的独审与CI。

## 阶段集成

治理前置[PR #7](https://github.com/Junweiiii14/bioimage-tools-platform/pull/7)先行。产品链分为P0、WB核心、Fig/OCR、恢复/维护、自动化、现有工作台、灰度监督/显示、原图修复/入口统一共8阶段。各阶段基于前置分支，保持草稿，不将累计历史一次合main。前置合main后必须重新加载实际PR基线并重跑检查。

历史回执不删除、不重命名以逃避门禁。显式清单逐份检查历史内容、来源祖先、原始规则与基线；唯一当前回执继续覆盖整个PR。T-007/T-026原指纹不符，在对应阶段真实重载并单独提交，旧Git对象可追溯，不追认旧回执有效。服务器规则及工作流未修改。

## 工作树与备份

- 同步前已在仓库外生成并验证all-refs.bundle（SHA256 `a557348f01f4cdac7eb5e3c116d6ea0045eff5afa8bbdda032cbad96774998a5`）；19个原有工作树逐一保存index/unstaged二进制补丁、未跟踪文件tar及哈希。此bundle时点为产品2e5021d，后续阶段refs另行备份。
- 再核对34个原有未提交文件，哈希全部保持。原主目录15个修改与12个未跟踪文件、兼容/解码/模板分支改动、现有questions均未丢弃。
- 6个干净且不含`.local`成果的历史工作树原位锁定分类：pr5-repair、t037-ui、t021-legacy-golden、t033-web-host、t035-crop-core、bioimage-pr5-fix。没有删除或移动任何目录，也未清理venv/缓存；解锁用`git worktree unlock <原路径>`。该分类不释放磁盘。
- dirty或含`.local`旧结果的树保留原路径；活动、治理和阶段整理树保留。规则草稿的本地副本移入活动树`.local/t043/RULE001-pre-governance/`，没有丢弃。
- 忽略的原图/参考/结果没有包含在Git bundle或未跟踪tar中，继续保留原位。不得因Git备份存在就删除这些目录。新增Git内容扫描未发现已知凭据格式或私有原始图/模型/安装包；此扫描不构成穷尽证明。
- 仅推送选定开发/阶段分支，不强推、不镜像推送、不删除旧分支。main保持`221a2df`，依赖机器人PR #4/#5另行保留。

8图裁图回归仍为旧1/8→新8/8，参考仅评分，数据哈希保持；没有独立积分真值，48槽质量状态不等于积分准确率。详见T-042评分与验证记录。


阶段远端PR：P0 #3；WB核心 #8；Fig/OCR #9；恢复 #10；自动化 #11；现有工作台 #12；灰度监督 #13；原图修复阶段待最终文档/清单提交后创建。P0推送先于base修改，首轮按main校验失败；之后close/reopen触发实际前置base的新检查，旧失败保留，没有改状态或添加空提交。


## 最终阶段链与跨平台补充

| 阶段 | PR | 整理独审绑定HEAD |
|---|---|---|
| 1 P0 环境与便携探针 | [#3](https://github.com/Junweiiii14/bioimage-tools-platform/pull/3) | 66e0240bc211e5d9f08e1019cf686df249adbd97 |
| 2 WB 原值定量、worker、存储与手工闭环 | [#8](https://github.com/Junweiiii14/bioimage-tools-platform/pull/8) | dd929960c4886e882d282490fd9ed59fdc8d2e50 |
| 3 Fig、多原图、OCR 与显式归一化 | [#9](https://github.com/Junweiiii14/bioimage-tools-platform/pull/9) | d7dbee51543e6cc061065fc79598d2eda7a53e8c |
| 4 元信息、归档恢复与维护基线 | [#10](https://github.com/Junweiiii14/bioimage-tools-platform/pull/10) | ef17d8a9c5dc800e6e0ea9842c3bd91714715ba0 |
| 5 实验室版式、模板与自动处理平台 | [#11](https://github.com/Junweiiii14/bioimage-tools-platform/pull/11) | 8be1c56d2399f728ead09415ab8c9800b32cdc99 |
| 6 现有工作台与网页宿主 | [#12](https://github.com/Junweiiii14/bioimage-tools-platform/pull/12) | 4a9c682883fbe552947c520e4e5b00284a8601ae |
| 7 灰度监督、标准显示与真实图验证 | [#13](https://github.com/Junweiiii14/bioimage-tools-platform/pull/13) | 4582976e4623e6ce25e433be59d08290bff3e3a9 |
| 8 原图几何、积分边界与入口统一 | [#14](https://github.com/Junweiiii14/bioimage-tools-platform/pull/14) | 0637250e33044c42a769ac8195a53b8916ff730e |

以上为最终整理复核绑定，后继仅补本记录/交接，产品不变。阶段1仅说明文档；阶段2–8唯一额外产品差异是独审2b9f643的Windows条件，原历史快照和旧失败均保留。
CI001之后最终产品树fa9c5f2正式完整check实际exit0：657passed/451.28s，全部隔离wheel含真实OCR完成。日志.local/t043/check-final-ci001.log；文档后继与此产品内容相同。
远端CI以PR实时为准，初轮Linux类型失败修复后重跑；不修改状态或门禁。P0新说明提交66e0240记录基线转换，使本次CI在新的可审查SHA运行，原失败仍在历史。


## CI002–004后继与当前入口

阶段8在原整理后追加CI002诊断、CI003宿主Qt所有权和CI004无载荷请求日志，均有绑定独审；不能将后继继续描述为只有文档/单行guard。产品68c3265最新659完整门禁实际exit0/509.86秒及全部隔离wheel/真实OCR通过。精确前置仍4582976e，SYNC008显式清单来源68c3265并保留CI002/003/004、T042/T043来源，原回执不删除。当前AGENT_HANDOFF索引已修旧目录指针，专用快捷方式只指活动树；原ResearchVault dirty树保持。

原有34未提交文件、8原图/12参考与旧预测SHA再次验证一致，证据.local/t043/preservation-ci004.json。阶段8远端15分钟取消和10秒create等待失败、阶段7首次5秒失败仍保留；原SHA重跑成功不能抹初败。远端最终状态看PR14及Issue6，main仍221a2df，全PR草稿，不发布。


## CI005/006与反复旧入口的追加修复

父工作区AGENTS仍路由旧dirty根，已仅替换WB段，完整原文件外置备份并独审SHA/范围；桌面固定当前开发树，原dirty代码和旧结果不变。CI00579f9070诊断独审8项0，正式664全检真实挂起后保存三线程原生证据，专属pytest停止后check实际exit1。CI006a811ccfd修复四后台退休与owner线程析构，独审18项0，最新精确清单来源a811ccfd，增加CI005/006历史回执；完整668门禁结果见CI006验证。原有阶段整理表为当时绑定，不适用于后来产品增量。

8原图新工作台功能链退出0，8run/N8/8/4/4/8/8/4/4、原SHA/保存重开/参考未读；8幅原像素ROI与48槽值/状态相同。结果另存workbench-ci006，不覆盖旧目录。远端其他历史超时是否与本地锁反转同因尚待证据；main221a2df和阶段链不变。
