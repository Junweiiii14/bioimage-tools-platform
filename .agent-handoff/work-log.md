# Current Work Log

## 2026-10-18：回存单行复核、全库审查与质量说明精简

b0e6c37独审1项2.42秒0，关闭多选误确认P2。只读全库覆盖123产品Python文件及主要动态链路，
已落实最小去重/无消费者局部控件删除/明确后台encode分支，兼容入口与旧schema保留。
新增声明与分发集合核对、未知任务真实线程拒绝（不误报保存成功），2项1.48秒0；
相关32项5.69秒0，初次新测试Qt args未知类型问题改为类型明确回调，无ignore或放宽断言。
绿色工作台质量原因集中去重，重复标签改简洁关联标记，原值/有效值区别及来源错误保留。
现成12UI相关34.16秒0、Node0。机械detector一次85项及明确保留/待视觉判断理由见
work/evidence/T-044/code-maintenance-audit.md。整项最后全检/真实8图/视觉/独审/GitHub尚未完成。

## 2026-10-18：最终真实验证发现首页文件夹入口遗漏

9fb79e2绑定独审25项8.75秒实际0，无阻断。随后最终真实验证从首页首次目录建项目，
发现ProjectSelectionJob仅collect_source_images，选入32项；旧首阶段目录证据只覆盖已有
项目的automatic.import_directory，不能证明首页路径已修复。该次自有验证明确中止，
核对PID34304命令行是本地验证脚本后仅停止其子树，外层实际1；用户PID/窗口未动，
部分新验证工作区保留，未执行回存，未形成最终8图或视觉通过。旧日志另存
.local/t044/first-folder-real-aborted.log，之前成功证据不抹掉这次产品遗漏。

现统一首页单目录automatic模式为既有folder_sources@1发现函数，仍在ProjectSelectionJob
后台线程，先筛选再验证/创建；通过wb_tool.api导出真实复用函数，不跨内部实现。
保留原目录用于保存位置重叠判断，显式文件选择/独立灰度不套目录偏好；新工作区/项目创建
后再绑定完整筛选记录，随后正常导入/状态导出，重试保留原路径和模式。

新增发货HTML首页按钮反例：两个设备源、同设置编号变体、已导出原值TIFF。旧路径真实
4行误导入失败1项8.49秒；初次新测试用普通短名称却期待设备采集文件偏好（依旧保留普通
编号文件的契约），改为实际采集命名样本，不扩展/放宽政策；中间1failed9passed16.11秒
保留。最终10项14.07秒实际0，覆盖首页筛选报告可见和status.json、旧新建/取消/目录
重叠/独立灰度及回存，原文件集合/字节保持。全项目类型/静态后继见命令结果，绑定独审、
最终真实8/全检/视觉仍待做；不能用9fb79e2检查覆盖后继。

## 2026-10-18：真实设备TIFF分辨率等价表示兼容

5f90c40绑定独审10项14.76秒实际0，首页目录遗漏关闭。最终真实8图随后完成8个worker，
但新写后核验在自动导出遇到设备元数据6000000/10000，输出约分600/1，错误地当成分辨率
改变而拒绝，尚未最终8图成功/未回存/未截图。日志real-rational-resolution-failure.log及
新工作区保留；核对自有脚本PID16632命令行后只停止该树，外层1，用户窗口未动。

修复为Fraction精确比较物理分辨率数值，保持单位及像素/通道/位深/来源等核验。非等价
720与600仍拒绝；零分母明确失败，避免异常漏回后台回执。新增真实非约分header结构样本，
成功输出600/1且原样本像素/字节保持；注入真实错误分辨率失败并清临时文件、不发布目标。
18项8.07秒实际0、相关类型0；不是容差放宽，无公式/schema/默认参数变化。
后继提交绑定独审/最终真实8与全检/有界视觉待继续。

## 2026-10-18：有界视觉检查发现弹框迟到事件覆盖结果页

f0696ed绑定独审18项6.76秒实际0，Fraction精确比较无规则弱化。随后真实8worker和正常
自动导出完成，预测冻结后合并成图与此前已评分成图像素一致。验证器错误假设应有4个PNG，
实际格式为一个figure.png包含4 Fig/8源，因诊断断言退出1、未回存；不是产品识别失败。
后继诊断明确核对唯一成图manifest全部8源及逐源ROI/泳道范围/显示框/映射/输出框，不能
仅删掉数量断言后宣称通过。首次6张实际Qt截图已检查（1440/960，拼图/全部曲线/结果），
不是只凭DOM或GPU日志。保持绿色工作台、曲线填充和原图，整体无重画需求。

截图发现结果页右侧仍是Fig组定量：曲线原生dialog关闭事件异步到达，在立即切页后仍调用
renderQuant覆盖结果页质量说明。已在直接关闭与close事件回调核对当前mode，仅quant页
才刷新定量。真实发货HTML“打开→关闭→立即结果页”先红1failed/7.42秒
显示“定量监督”而非“输出结果”；新绿1passed7.80秒，保留质量说明文本断言。

为避免途中修改冒充同提交完整门禁，f0696ed全检在约13%由已核对PID34144的自有dev进程
树明确停止，实际1，wheel未运行，check-before-modal-fix回执/日志保留；不是原生退出复现，
不是完整通过，用户窗口未动。后继源码检查/独审/完整check/真实回存与最多一次截图确认待做。
Impeccable detector已运行一次，后续不重复。

## 2026-10-18 T044 最终本地交付

a72e7102891df287e3484f20f3724612779b53f5：733 passed in 525.53s、pytest child/全部wheel/dev实际0。最终正常Web8原图/8回存/保存重开/关闭0；8图产物独审0。API延迟依赖修复独审11项3.31秒0+隔离导入/发现0，无阻断。裁图回归1/8→8/8，积分13有效35复核不是准确率。详见work/evidence/T-044/final-delivery.md。下一步外置最终备份、阶段9草稿PR/日志/远端检查；main不直接合并。

## 2026-10-18 T044 阶段同步

本地完整check/8图/独审完成后safe push，草稿PR #15依赖stage-08，main221a2df保持；原34未提交SHA/新allrefs bundle已核验，当前4文件另存外置。最终文档后继再备份/push，远端四项检查运行中，issue6开发日志随后记录真实结果；不改产品、不合main、不删除旧树/原图/旧结果。

## 2026-10-18 CI012 远端Linux与fixture销毁

3e5cee3 Linux约29% OCR时SIGSEGV，真实非GUI线程QWidget析构；未最终通过。精准fixtureclose/wait后deleteLater/waitinvalid，回归红1/2.87秒、新11项25.58秒0。受控holder环窗口后台GC旧Aborted/3，先GUI销毁0，不能认定原对象身份。产品代码不变、旧证据保留；提交绑定独审及远端734全检待做，详见ci012-fixture-lifetime.md。

## 2026-10-18 CI012 有范围的测试窗口管理

精确清点Web/平台/共享fixture，统一仅显式自有窗口的异步close/wait→GUI销毁，不动产品/全局GC/Qt根，保留业务断言与原时限。67项157.28秒0、全类型/静态0，总736。c5 Linux735/133.44秒及wheel/dev0，Windows待；925 Linux失败/Windows取消分别保留。待本批绑定独审/最后备份push/最终736远端，实际结论写issue6/ignored receipt不重复文档触发全检循环。

## 2026-10-19 T-050 规划修订

## 2026-10-18 T045本地实现完成

从f42f069仅新增t045隔离树，产品a2cda5f/3f4c593/8246eb1和测试后继f18589a；手动泳道/UB整段/Fig自动工程闭环完成。指定图33Fig106运行成功、重开106、真实CSV/XLSX135行545值拒绝覆盖。独审原5项及Space全部resolved，schema9未知反例9→10独审14项0；最终747passed517.90秒/原child及check0、全部wheel与9合约通过。原停止/746+1失败记录不抹去。原项目/旧树/快捷方式保持，源图SHA与旧四核心文件已复核。后继仅文档/私图捕获gitignore；本地completed未push/main/发布。历史原生UNKNOWN与科学/干净机留出保留，使用候选Start脚本，详见T045验证/说明。


## 2026-10-18 T046 全组审核与边界修复

用户批准独立交互预览后，复用t045候选树，base e78a14a，992c338实现完整峰半区搜谷/质量策略、全组框/按蛋白曲线、合并表格、真实进度及轻量缓存。独审五项fix在4d4944a修正：跨组选择、保存回执、恢复缓存、刻度11px、窄屏导航，复核全部resolved/ship仅五项范围。真实图副本12框12曲线、UB16、33组135行；保存重开、手改实际重算、忙时查看与取消都通过。首全检755/3失败与次轮observer编码失败保留；第三轮最终761passed/526.85秒、原pytest child0及全部隔离wheel/dev/check0。新测试fixture初败/关闭异常明确记在validation，原生精确根因UNKNOWN，不掩盖。文档代理完成普通扩展记录，旧tokens保持。原图SHA一致，原软件/窗口/快捷方式未动；无push/main/发布。

## 2026-10-19 T047 本机安装候选交付

复用t045候选树，无新worktree。入口/恢复/同窗epoch/关闭协调已按批准预览落地；独审P1取消后草稿绕过修复53a2030，最终源码769及所有隔离wheel/dev0。AOT632安装后GUI/OCR失败、c8编译中止保留UNKNOWN。改为同一CPython3.12.14私有运行库+锁依赖+四wheel+原生Job入口，b6df40e最终installer0/install0；真实安装七检查11.516秒、OCR/定量协议/进程归属/316模块路径/原图旧快捷方式摘要通过。两项独审resolved/ship仅评分范围。实际新桌面入口已启动候选窗口供用户测试，未关旧版或用户窗口。documenter保留既有设计系统。干净Windows/DPI/物理按钮/科学留出仍未验收。无push/main/发布；详见T047 validation及任务。

## 2026-10-19 T048 Win10离线测试安装包

用户保留测试版、不正式上线，目标64位Win10版本未知。同一候选树3821c64加入独立Win10Test安装器/设置、必建桌面和开始入口、本地固定Qt VC运行库、PS5.1自检与说明。13专项与静态/政策0；真实非管理员安装卸载重装/GUI七检查/自检负测/7721文件SHA0，两项独审修复后ship。桌面交付361325507字节Setup与摘要；原数据和旧窗口保持。宿主Win11，无干净Win10/VM，未把其写成目标通过；科学语义未改、无PR/main/正式发布。详见T048任务与证据。

## 2026-10-19 T051 main规划集成

PR16四项必需检查通过，匹配cdf4b7d后合并43d520f。产品基线a234354与main存在历史文档冲突，保留产品分支完整历史，README添加新版规划入口；T050证据、规划和原main快照并入。新任务T051实现导入/清单/缩略图分配，不改变OCR功能。产品原快照归档T051-product-before-intake.md。

## 2026-10-20 E3完成，连续进入E4

产品32da9f4，T056 done：固定N槽位/原值TIFF/真实宿主复核与CAS，独审发现票据导出及桥接强退review的P2均按新提交复验关闭。完整check0：832/553.10s、原child0、9契约、全部wheel/真实离线OCR；21桌面前端18.93s，UI限定ship/documenter No changes。旧purecall UNKNOWN与344/truncated inventory转E6，不消账；真实科学/目标环境仍未验。下一项T057 E4。

## 2026-10-20 E4完成，连续进入E5

T057 done，产品ff89867：完整Fig先持久化再真实原像素运行；843/579.73s、原child0、9契约/全隔离wheel/真实OCR/check0，绑定独审通过。df轮843/570.37s后wheel因顶层PIL失败1，ff延迟导入修复，独立API无PIL/核心5探针和完整复验0。分页与回源两P2已按提交关闭，UI限定ship、documenter No changes。原生UNKNOWN/344截断inventory/真实科学与目标机限制保留，无发布。下一阶段T058，详细证据work/evidence/T-057。

## 2026-10-20 E5完成，连续进入E6

T058 done，产品8feffce：schema14稳定身份填表、冻结资产/run、新目录输出、索引CAS后完成、真实归档恢复不注册外来PID。858/623.78s、原child0、9契约/全wheel/真实OCR/check0；冻结run竞态和同步busy独审P2均resolved，最终绑定8fe无新P0–P2；UI ship/documenter No changes。823首轮类型失败1历史保留。科学/真实确认批次/干净Win10/物理DPI和main/安装版仍未验，不发布。下一项T059，详细证据work/evidence/T-058。

## 2026-10-20 E6 closeout

Completed ea7ed55 frozen render reuse, exact-owned widgets and full stage pagination. 862/624.64s + original child0/all wheels/real OCR/full gate0; independent scoped review/UI ship. Export20x2 thresholds passed; desktop20/phase1/cancel5 explicitly limited. Inventory4 does not resolve purecall UNKNOWN. Auto-next E7, including historical OCR late cancellation P2 discovered by separate high-risk audit. No remote mutation/new installer yet.

## 2026-10-19 T050 规划回复（保留main记录）

根据用户回复更新第5/6/7/8节：批准局部暂停与独立结果目录，独立灰度定量OCR作为继续支持的功能。主流程不加载OCR与安装发行拆分是不同事项，后者未决；同步任务/风险/待办和交接。未改产品/PDF/依赖，旧审查不外推本轮修订。

## 2026-10-20 E7 governance integration

INT001 resumes authorized E7 only in this temporary historical integration tree. Merged planning main43d520f into original governance0b7, retained immutable RULE001 receipt source; loaded/read exact rules and current full scope. Main PR/CI not yet accepted. WB product development/checks remain in t051, not represented by this zero-product checkout.

## 2026-10-20 E7 OCR, candidate and dependency integration

80a84ef OCR取消/CAS修复13边界与42兼容0/独审关闭；ea8f914候选与14检查自检，32d9733启动故障关闭2/8.17s0/独审关闭。首E7 gate主动中止，32d gate单一standalone失败后UTF8/GBK监视器异常，原OS exit未知/outer1/wheels未跑；8日志回归0及原页独立重放0不销未知失败。PR7经最终69a/四项CI/独审后merge7730bcd，primary合入并重载T060实际base；临时集成树继续PR3/SYNC001。暂无新安装包或正式发布。

## 2026-10-20 E7 final gate and accepted quant stage

8e11028完整910/705.48s、原pytest0/u32=0、全部隔离wheel/真实OCR/check0，inventory4非截断；单事件测试P2独审关闭。旧5bb/d7f失败保留，产品运行文件等e579。PR12/13实际四CI和独审接受main6e8b1e6，主树合1891仅元数据；77b文档刷新及交接。PR14最终b1四CI中，PR15准备3748，最终集成未完成。安装候选工程验证已通过，科学/干净Win10/物理DPI仍待验。

## 2026-10-20 E0–E7 engineering closeout

Final3680790 actualbase842独审/13历史来源规则0；产品PR17 Windows910/666.50s、Linux910/353.99s及全部wheel/真实OCR/四检查SUCCESS，精确merge main0f358ac（00:29:51Z）。本机8e910/705.48s与安装e579工程验证另列，不混作服务器证据；运行文件相同。桌面setup SHA复核一致，旧原图/历史/安装/用户窗口保留。当前仅更新任务done、README/验收索引和handoff；旧validation已先复制校验再归档。科学留出/明确样本配对、干净Win10/物理DPI仍未验，原失败和UNKNOWN保留，无正式发布/定时任务。

2026-10-20 CI收尾：main0f的910/762.24s及wheel功能通过后清理遭15分钟取消，整命令未通过；旧main3b702/590.48s后原退出0xc0000005/wheel未跑，原因UNKNOWN。原306四CI通过不销旧失败。仅foundation TEMP/TMP同盘与实际路径诊断实验，保留时限/测试/退出检查；新head待绑定独审及四CI。详见work/evidence/T-060/ci-temp-filesystem.md。

2026-10-20 T061：导出组/角色/候选原坐标与集中确认已接入；真实82图仅开发候选无监督真值；新增必要4core、11Web相关、1host重开及1回执修正通过，首次核心2fail及原因保留。完整门禁/最终独审/安装候选待验，状态与细节见T061任务。

T061收尾：冻结710一次916/763.69s及全wheel/OCR/check0；非作者接受、安装/PS5.1双流程/新私有识别probe0，用户数据不变。三旧安装卸载0与桌面旧包/过期shortcut移除；递归残余清理被自动审批blocked by policy阻止，未绕过。最终PR19四检查待验，详见T061/validation.md。

2026-10-20 T063：用户批准完整采集组交付计划；新受管wb-grouped-intake树从main f3fb2ff建立，uv sync0，原t051/T062未提交资料保留。规划/导航和历史基线标识更新，尚无产品改动/测试/独审。

2026-10-20 T064：PR21已合main1625ae5并重载；新增v3采集组草稿/稳定投影、正式无侧栏网格及后台大图预览，70相关测试0/类型静态0。三目录95图只读识别19信号/23区域，仅开发证据；具体首败及修复见T064。后续独审/产品PR/快捷键/精简/完整验收/新包仍待。

2026-10-20 T065：T064已完成冻结实现与界面原问题复审，PR22创建并附着；Linux/规则/桌面环境成功，Windows仍运行。新codex/intake-crop-revision分支接候选区域与完成后原图范围修正，保留其他Fig及全部历史文件/修订；核心33与网页/宿主41实际0。冻结非作者审查、集成基线重载和总计划后继继续，未全量候选门禁/新离线包。

2026-10-20 T063–T069本机交付收尾：完整P0–P8工程范围经PR21–24/26–28独审及四检查集成。PR28最终93d1ef0双平台956/全部wheel/OCR成功，精确合main6080867；手动完整原生取证956/382.32s debugger0，旧失败UNKNOWN保留。真实19组主链/4A局部重算/两份新旧输出/重开已独审，114原文件与旧树dirty保持。冻结608构建并非管理员安装新GroupedIntakeTest候选，7,749载荷文件相同、分组17项及灰度OCR/PS5.1双流程实际0；安装包361,584,364字节、SHA99c0ec55…bb6d97。非作者绑定608只读交付接受；首观察器null和首审查归档假设错误均留证。桌面交付BioImage-WB-采集组测试版-T069，索引docs/wb-grouped-intake-delivery.md；最终收尾分支仅文档，不改已验产物。干净Win10/物理DPI/独立科学真值仍待外部验收，无正式Release或依赖升级。

## 2026-10-21 T071 Fig顺序工程交付

产品5f独审Accepted，PR30四必需检查后精确合main710bb85；最终Linux979/332.14s/debugger0与Windows979/615.77s/raw0、全部wheel/OCR/check0。本机a952完整979/825.65s0，不冒充覆盖后续诊断。冻结main新FigSequenceTest构建/安装、三流程OS0、PS5.1随包三流程0、7751载荷校验0，桌面新交付已生成，旧成果摘要不变。首PS5.1外层脚本无BOM中文路径失败保留，仅补本地BOM后新轮0；原CI初败/native/手工坐标UNKNOWN不销账。最终交付审计及记录集成见T071任务。此前新段按维护器顺序归档仍保留；本段按时间追加于尾部。

最终包态独审Accepted：冻结main/安装器、41校验成员/37证据副本、源码302/四wheel176包文件/7751载荷及1257额外pyc核对，无新增P0–P2；CIM采样不声称采全。当前安装根进程0，旧成果保持。最终记录随文档PR正常集成，不重建已验包。

## 2026-10-21 T072 自动流程与预览修复交付

获批六项及128缩略图误作中央图问题已修：source_signal/guide共享原信号校验、机器采纳不冒充人工、按Fig显示纠偏、灰度图/区域、统一表和说明折叠。初审两P1/一P2及衍生caller问题修复后44a非作者Accepted；PR32最终46a四检查正常合main0630604。两平台各1013、本机1013/880.70s及全部wheel/OCR/check0。干净冻结main构建独立AutomaticFlowTest安装69.395s0，四单独流程OS0、PS5.1新轮56.548s0、7753载荷一致。首外层observer误收旧OneDrive并停止，已同exe重启确认，修为严格时序/身份且完全不自动终止，非作者Accepted，原失败永久保留；产品字节未变。桌面交付与最终审计/限制见T072任务及交付记录；旧dirty/原图/历史/安装保持，不扩展新任务。

收尾PR33/be38双平台全检各1012/1失败于既有双Fig测试抢读1行占位；原始日志保留，明确本轮wheel未运行。仅补等待完整9行、可见与results模式，原断言/10秒截止不变，作者两相关E2E17.54s0及静态0。真实重载增加tests范围，a65经非作者Accepted/独立两项15.66s0；最终head全部检查及merge按PR33实际记录，不拿旧头代替。安装器继续冻结0630604，不为测试等待重打包。

## 2026-10-21 T073 频繁裁图确认诊断与待审方案

用户明确先查原因列清单、审核后修复。新规划分支基于main941b424，仅记录文档；保留T072安装/窗口。只读一致快照rev11和两例重放确认：N2假3槽、唯一两泳道旧候选被源图后置膜校验清零；所选10张均被角色启发式分merge，伙伴角色条件使白光未执行，另有≥3条带方向硬门槛。已确认第一人工后自动进入第二，重点是判定而非继续按钮。30原资产SHA保持。六项原因/修复/正反验收在T073，等待审核，未产品实现/独审/PR/打包。首诊断脚本dataclass取值错误与后继0均留证。T072收尾278两平台1013及全wheel/OCR四SUCCESS，正常合PR33→941b424，原失败不销账。

## 2026-10-21 T073 批准执行与UI原型

- 用户批准六项及追加UI完整方案，create_goal记录全部范围；新树wb-reliable-crop-ui/main941b424，分支codex/t073-reliable-crop-ui。旧四树SHA/HEAD/dirty保存，新树只复制旧T073文档，不动旧文件。
- 研究Linear/Figma/Carbon与MDN/web.dev，写研究和本地HTML原型并打开IAB；合成图/示例流程，未接科学计算。第一轮视觉含1440/1024/390；确认真实示例自动暂停→一次继续→5行结果。检测一次及JS语法已执行，最终视觉和代码独审待完成。
- uv sync0；既有两模块28用例110.36s0。一次浏览器reload/检查批次超时，重取原tab成功，不作产品失败；一次动态页签旧名称定位失败，按实时名称成功。产品算法/安装未改。

## 2026-10-21 T073 固定网格与精简验证

用户补充固定N、原像素槽宽和5N:4比例，已实现整排对齐，不再强求N个独立连通组件；手动确认范围完整保留。只读最终重放为1行保留人工、8行自动、1行首带与标记相连仍暂停；原图SHA不变。补安全采样Y边界阻止背景扩展重新读入排除结构，并把局部第二目标传至真实quality_review。UI预审问题关闭、最后3项定向0；新两个科学反例首轮37过1败为测试构造先触发原有扩展保护，改用合法25%范围内越限反例。首全门禁8项类型错，pytest尚未启动；修正类型，无ignore/放宽。按用户要求不反复冒烟，保留必需检查。新ReliableCropTest独立安装身份，随包仅相关自动流程自检。尚未提交独审/PR/构建。

## 2026-10-21 T073 PR34与最终修复

2026-10-21最终增量：首提交a0e8e77已推送草稿PR34。精确独审指出隐式配准范围外较窄第二排漏检、角度草稿冲突时按钮重启用，现已修复。全门禁第三轮本机1157过2败/562.98s，Linux1157过2败/411.84s，Windows1157过2败/658.70s，失败均为窄斜第三带误吸收和安装诊断仍检查旧geometry@1；原日志保留，未到wheel步骤。补原连通身份及初始网格单向冲突拒绝，诊断明确检查geometry@2，亮背景信号使用可验证同组白光轮廓。定向33项首轮31过2败/18.83s：窄屏GPU上下文丢失及诊断旧版本；仅重跑两项，用CI相同--disable-gpu环境后2过/11.55s。受影响6文件Ruff/format/pyright0；无断言放宽、无门禁/锁变更。最终只读10行仍1人工保持、8自动、1暂停，30资产SHA保持。按用户要求不再本地全量或冒烟，下一步绑定最终提交静态复核及PR必需检查。


## 2026-10-21 T074 曲线与整版拼图

批次封底复用独立曲线、CAS后重测；单Fig定位与裁剪分开；schema15网格持久化与同布局导出。独审修复来源草稿/分组顺序/后台有界预览；包态修复JSON数组边界及view字段保留。最终569674a新独立安装19checks通过。PR35待用户决定集成；旧目录/安装/数据保持。详见T074任务与delivery证据。


## T074 用户实测补齐

用户确认全部泳道并排点选封底编辑，e47af46补固定高度卡片/编辑器、整卡点击、拖动反馈/过期保护及原图视口，独审Accepted后新安装19checks通过。另修已保存阶段即时发布防快compose漏页。最终服务器门禁以PR35当前HEAD为准；保留真实失败记录，不追加无关测试。
