# T-060：E7 集成、包态与交付验收

- 状态：implementing；base5e3459a，E6产品ea7ed55。前置E0–E6各阶段相关/完整门禁、绑定独审及证据已收尾；E6 862/624.64s、原child0、全部wheel/真实OCR/check0。
- 授权：按docs/wb-execution-plan.md连续推进，无阶段重复批准、无定时任务。有效t051/codex/wb-e0-e7；root sole writer，非作者只读独审。原ResearchVault dirty树、旧候选/安装/原图/历史结果/用户窗口保持。
- 范围：apps/desktop、tools/wb、tooling、tests、docs、README.md、AGENT_HANDOFF.md、.agent-handoff、work/tasks、work/evidence、.github（仅实际CI诊断必要时单独说明/独审，不改规则以绕过失败）。scope .加载全部当前与BASE规则。
- 首项：补充当前存活高风险链独审已绑定ea7ed55/base536f04e，发现历史OCR迟到取消P2。ProjectOCRSession异步解码后不查取消，宿主完成/安装只查generation；先改草稿再保存使失败/取消可能替换关联。修session完成与host完成/安装/CAS前后保护；真实已提交RunRecord不撤销，保存失败/取消保留当前旧关联。覆盖decode/install/关闭/encode前/CAS在途/保存失败/后续显式重试及过期generation。
- 科学/接口：不改算法/默认值/项目schema1–14，不升级依赖/锁，不取消独立灰度或OCR。新诊断、构建清单/通道接口明确版本和旧行为兼容。
- 集成：核实main/历史PR7→3→8…15及本地后继真实依赖；逐批更新匹配实际base的规则回执/显式历史manifest，保留历史来源/审查缺口。绑定最终head非作者审查，四项服务器必需检查完整通过后PR集成main；禁止强推main、删除回执、改成功状态/规则绕过失败。远端状态和实际merge SHA逐批记录。
- 包态：干净提交构建新隔离测试候选，独立AppId/目录/设置/入口，不覆盖T047/T048或原安装。沿用已验证private CPython3.12.14/锁定四wheel/WebEngine/完整OCR模型与许可源码；不用未通过的AOT路线。单独说明资源裁剪，既有qml/include排除之外不扩大裁剪。
- 安装验收：本机非管理员Win11新候选安装、卸载/重装、中文路径、独立入口/设置、原资产与旧安装保护；私有实际runtime运行新清单批量主链（保存/真实worker/稳定槽表/新目录输出/重开/重复不覆盖）与独立灰度/OCR两条流程、所属进程关闭、离线模型，精确进程退出和文件摘要。不调用用户Esc停止的原生Computer Use；离屏工程不外推物理输入/DPI。
- 待验边界：独立真实仪器真值/样本对应、干净目标Win10与125/150/200%DPI缺失时保留未验；继续不依赖的候选/集成工作，不标正式发布完成。历史纯虚调用UNKNOWN保留，不据本轮成功销账。
- 验证：针对性真实Qt/故障测试、全量check和隔离wheel、非作者当前提交风险复审；Qt测试/探针/安装态串行。记录每次命令/退出码/环境/提交与失败，未跑明确未跑；必要实验先冻结预期，不弱化断言/容差/时限。
- 下一步：context/规则阅读→OCR取消/CAS回归及修复→高风险复审→依赖集成/远端CI与独立候选构建/包态验收→需求矩阵和交接。

## 当前进展

OCR取消/CAS修复13边界+42兼容、非作者P2关闭；新E7候选/14检查源自检、4设置隔离、2启动故障及独审通过。32d全量单一standalone页面失败后监视器GBK/UTF8异常截断细节，原OS退出未知/outer1/wheel未跑；独立重放1/10.57s0不销未明失败。监视器Unicode2项先失败后8项全部0，只修日志/真实退出传递，不弱化断言。已merge治理main773并重载规则；PR7已合，PR3新base/head远端检查中，后继阶段继续按依赖。下一步绑定监视器复审和完整UTF8全量复验，再独立候选构建/包态。

UTF8全量b105中原standalone页面通过；10个import-linter反例fixture因UTF8子输出/GBK捕获解码失败，单项已复现。仅显式匹配子输出与解码编码，原正反例断言完整保留，18相关回归/5.12s0。此轮原生观察环境名拼写不符，不声称捕获native；最终全量使用真实变量名。scope .已按main e09重载并读取BASE变更。SYNC002独审另发现旧WBWindow完成会话未释放P2，当前兼容入口也存在；等待串行真实成功/失败/取消回归修复后集成。

WBWindow兼容入口会话释放已按真实完成边界最小修复，三路径3/9.84s0，完整相关22/44.87s0；待绑定当前提交独审和最终全量。b105全量结束10编码失败/873通过/738.49s/实际1，inventory4非截断，wheel未跑；编码修复59d独审通过，10原契约独立4.08s0。下一轮正确启用native观察，不改测试答案。

186全量886/750.61s，原child0/u32=0、inventory4非截断、全部wheel/真实OCR/check0。后继独审确认当前crop/confirm旧Web操作可覆盖新ROI，连同同源set_lanes补legacy_crop_edit@1完整身份及开始手势冻结；三条红3/5.38s，修后相关12/21.96s0，真实两种页面手势也通过于组合24pass/1fail。失败是原独立灰度页面run后30s无project_results，来源UNKNOWN，新增仅诊断trace、独立重放1/11.21s0，不弱化等待/数值。该问题继续观察，当前裁剪修复待绑定独审/完整复验。PR8最终9f四最新检查SUCCESS/绑定独审后merge461f2c0，旧26b超时保留；SYNC003等价修复76f及实际main合入e8beb7e，17真实回归运行中。新安装包未构建。

当前73a4cb7裁剪身份P2绑定非作者独审关闭；两种组合间歇失败仍UNKNOWN，已补失败专用字段/页面提交诊断，完整断言/30s时限未改。最近组合25/35.29s0仅证明本次，不能关闭旧失败。SYNC003真实17/109.47s实际0及最终7ab8da1绑定独审通过，PR9实际main基线四检查中。继续当前完整门禁和独立包态，安装包尚未构建。

定量编辑另发现跨会话P2（quant_edit缺project/epoch，quant_target缺epoch），真实桥接8例前7fail1pass，补严格会话和JS冻结/草稿退休后相关11/12.91s0、原兼容16/29.42s0、真实ROI旧手势丢弃及新worker1/5.83s0；包含裁剪/分组/手工泳道最终22/33.34s0。060全量为此主动停止17%/原child1/outer1，无完整pytest/wheel声明；诊断fields已修320a342并独审纯probe关闭。crop用例补公共已保存空闲前置，不减断言，两项历史间歇UNKNOWN仍保留。PR9按四检查/独审merge5e8b891，PR10最终6963a64已独审待四CI；候选尚未构建。

0c927f5完整900/691.23s、原child0、inventory4非截断、全部wheel/真实OCR/check实际0。首个隔离E7包构建0，非管理员中文新目录安装0；安装态intake14全部0且私有运行时/无所属残留。原独立灰度自检旧quant_target调用缺epoch，被新guard正确拒绝/actual1；源CLI先red1/7.58s，补当前snapshot epoch后两故障+完整CLI3/15.29s0，需独审及新包重建/重验，不能把首包判为最终成功。保留所有报告和原候选，后续currentmain上下文aac已重载/read。

Final e579 lifecycle actual uninstall0/reinstall0, registered E7 launcher/runtime/desktop shortcut/uninstall entry removed before reinstall; unique owned synthetic in-install and external user-data sentinels SHA unchanged. Exact registered E7 AppId/install/uninstaller path checked before action; old user candidate PID55936 stayed alive and its executable SHA unchanged. Reinstall restores correct source manifest and E7 shortcut. Logs .local/t060-{uninstall,reinstall}-e579.log and compact .local/t060-e579-install-lifecycle.json. No deletion of user originals/history or old candidates.

Post-reinstall installed v3 dual-flow actual0: intake controller14.8269492s, gray11.9931818s; both report passed, no forbidden development modules/remaining owned processes. Private installed provenance and14 intake checks retained. Fresh .local/t060-installed-{intake,gray}-v3.json and process.json, no older report overwritten. Thus local nonadmin Win11 Chinese-path package engineering/lifecycle is passed for e579; actualmain/final integration checks and scientific/clean Win10/physical DPI remain separate pending items.

5bb准备树完整门禁908pass1fail/762s原child1/outer1/wheel未跑；旧latebatch测试遇合法autosave新批，4条真实运行/修订引用核验见late-batch-failure.json。仅测试隔离旧批完成并新增恢复自动重算两分支，30相关/176.96s0；待最终静态/提交独审与新完整门禁，产品仍e579。PR12 Linux202超时UNKNOWN、3f诊断控制全0但首WebChannel超时（609pass1fail/170.52s/原1），新观察/无GPU环境待验。
