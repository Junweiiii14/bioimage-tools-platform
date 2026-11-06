# Current Work Log

## T074 用户实测补齐

用户确认全部泳道并排点选封底编辑，e47af46补固定高度卡片/编辑器、整卡点击、拖动反馈/过期保护及原图视口，独审Accepted后新安装19checks通过。另修已保存阶段即时发布防快compose漏页。最终服务器门禁以PR35当前HEAD为准；保留真实失败记录，不追加无关测试。


## T074 整个Fig矩阵交付

用户明确整组Fig展示，现为蛋白行×泳道列，跨蛋白编辑等正确快照、缺项保留草稿入口。86c9产品及c90诊断独审Accepted；新包19checks/11.437秒通过，首重开超时真实保留。使用与交付入口已更新，最终服务器检查看PR35，合并另行确认。

## 2026-11-02 P005正常集成与P008激活

最终2258独审Accepted/四必需CI全SUCCESS，PR52正常merge4d6ee6c/tree一致。Windows1659pass1185.30秒/Linux1655pass4既有skip508.51秒及双wheels真实三节点通过，P005工程done/科学现场用户验收不代签。用户追问全量用途，明确以后本地定向、最终候选CI全量，减少重叠。P008从新main激活并完整读541行新规则；WorkflowSession初步共享父存储、两个顺序子图6真实run，关联4pass26.27秒，Ruff/type0。批次索引/隔离/恢复/CLI仍未实现，不认完整M1。B012外部规划dirty保留不提交，待其最终指引。


## 2026-11-02 P008真实批次候选

父索引/共享WorkflowSession顺序执行、样本隔离、暂停取消恢复、真实claim后进程崩溃对账、CLI及模板第二批/分支图/缓存重算贯通。批次8pass51.87s、CLI3pass63.01s、关联80pass236.02s。最后取消问题均实际先失败后修：坏源回执双终态1fail2.40s；重开提前取消/父取消阻塞2fail8.81s；最终相关16pass50.04s。static/policy/9边界过；最后源码只定向检查，不重复全量。新增wheels探针/集中准确独审/PRCI待做，不认整卡/M1完成。外部B012规划dirty未提交。

## 2026-11-02 P008 final candidate review/CI

323d59f isolated wheels exit0 including batch/template; independent P2 pausing/resume stall genuinely reproduced then fixed53892fd. Author batch10passed68.35s; independent frozen correction3passed30.69s Accepted full4d6..53892fd. PR53 ready; finalquality41434643209 live, rulescontext success, nativecase expectedskip. Await actual requiredCI then normalmerge; P009 stillplanned. Rawfailed/contaminatedrun retained; no repeatedlocalfullsuite. Evidence/handoff edits await integration closeout, do not push sameproduct documentation merely to restartCI.

## 2026-11-02 P008 merged / P009 actual activation

PR53最终b4847a5 Accepted，四必需CI SUCCESS后正常merge2755604，候选/main tree同98754bdd。Windows1675pass1306.50s/Linux1671pass4旧skip930.49s，双侧全部新wheel过；旧超时及夹具失败保留。P008done。P009在codex/p009-visual-workflow真实激活，scope .707行完整读，已有impeccable context/具体surface/craft-floor实际读；原生DOM/SVG有限图交互探针+web静态检查过，无新依赖。仅图组件，不冒充M2；下一步宿主草稿/预检/表单/实际运行。独审集中完整可运行候选，不审每小提交。B012保留。

## 2026-11-02 P009 connected editor checkpoint

后台/桥/首版schema表单接同一真实批次执行；11项定向47.73秒过，两批4000.0→40.0/保存保焦点及模板版本布局证据见P009/connected-editor-progress。修复真实schema固定元组和bind图同步问题，测试固定成果数/40字符串误写分别记录，不增ignore不改科学结果。尚无最终UI视觉/性能/IME全矩阵、wheel/独审/PRCI，继续P009。保留B012他人untracked。

## 2026-11-02 P009 full web flows and valid capture

五流程通过39.93秒；布尔false/空数组添加/IME标记/窄窗步骤选择/模板初始化N及bridge-ready修正，完整GUI模板新TIFF与CLI、缓存/新草稿焦点验证。12图有效采集15.42秒，失败和颜色/RAF/readback范围完整保留ui-edit-validation。一次detect0主要+1advisory。原生性能、集中视觉/代码独审及wheel/PRCI待做；不重复本机全量。

## 2026-11-02 P009 bounded visual finish

独审首轮唯一窄窗密度fix，一批压缩顶部/高级元数据后置/图起点修正，相同12图确认15.57秒，原reviewer scored fix ship。6相关tests41.34秒过，type/web0。documenter只写conformance，保留既有系统/旧drift。视觉两轮预算耗尽，后续性能/wheel/最终代码独审/PRCI，不重复本地全量或截图循环。

## 2026-11-03 P009 performance/wheel preparation

最小实验qWait无Python存储执行，nestedLoop立即执行/回执；只新工具改AsyncEventPump，不修改产品或旧P006。1test1.80s过，r5原生prefs/前台/trusted两场景1+0诊断过；正式5+30待冻结。wheel probe增加真实已安装编排GUI/模板链，仅编译未运行。所有旧失败保留，视觉预算结束。

## 2026-11-03 P009 installed authoring passed / formal fix

隔离wheel全环境第二轮exit0，旧探针不删，新独立GUI进程避免app.quit轮询/Chromium生命周期冲突；原自建PID29120核CommandLine/父52988后终止，旧exit1保留。坏TIFF混合输入GUI1pass9.48s。正式5d0首轮控制第二次注入顶层const失败，IIFE修正/2轮诊断过，数据不覆盖。P009 raw字节属性仅保留CRLF。下一步新冻结完整采样及准确独审/PRCI。

## 2026-11-03 B018提交收尾候选

F008四项必需检查通过，PR56合入5d6e03b，旧依赖PR/Issue已关闭。文档修复、P009收据与模块历史边界已核验，旧dirty主目录恢复路由已转本树。PR54等待本次准确候选CI/正常集成后才完成；新方案仍未开始。

## 2026-11-03 B019方案候选

先完成B018/PR54及F008/PR56正常集成，再重写5.0主方案/开发流程/实验路线。默认完整实验向导，复用有效算法与既有执行器；专业模块和Agent逐步扩展。P010仅登记planned，未运行实验/访谈。五HTML与链接/归档/登记表/格式/policy检查通过；等待准确候选PR检查集成。

## 2026-11-03 B019完成

PR58四必需检查成功并合入c8f1bcb，5.0方案和GitHub组织完成。Issue59是未启动的下一调研，57是未验边界。用户要求不要过度防御、不纠结小问题；仅补本地真实合入收据随下次正常PR带入，不额外开检查轮次。

## 2026-11-04 P010首轮调研与新窗口交接

核对WB官方方法说明、归一化公开用例和当前三节点宿主，形成完整结果/路径/差距底稿。P010已激活；未运行原软件或学生试用，不冒充完成。下一步新窗口真实目标模式接续，优先一份代表性材料和首个最小WB闭环，避免过度设计。

## 2026-11-04 P010调研接续

已恢复bf52b61干净树并实际创建无预算goal；只读核验两份表格及代表TIFF，明确自动裁图与归一化审核标记断点、最少重复身份缺口。归一化15测试、网页2测试、源码自动诊断17checks通过，GPU日志和原生绑定失败保留。用户不知道实验语义并要求少问；按明确合成样例推进P011，真实科学/用户验收未通过。详见P010记录，未修改产品代码。

## 2026-11-04 P011候选与前置集成

P010调研PR61全部必需检查成功，正常merge为87dba64；产品PR60保留草稿。918af16实现自动证据归一化、身份与有界背景上下文，e349b2e修正测试入口/同步。35cfe双平台全门禁成功，当前候选需新基线回执及最终CI、独审。CDP视觉证据已查看；本机5fail与后续诊断、工具原生异常均保留于P011/progress。原始输入与历史不覆盖，原生探针窗口已正常退出。

## 2026-11-04 P011独审与修复

用户允许只读子代理；初审7e875d1发现身份草稿共享P2，真实网页先确认误存，4dcd41e深拷贝修复后2测试通过，独审复跑1例通过并关闭P2。110项非GUI和200个边界反例独立通过。最终服务器CI及正常PR60集成待完成；未改门禁/公式/阈值。见P011/independent-review.md。

## 2026-11-05 P011完成

最终f3a7d86四必需检查成功，PR60正常merge至8299f71，文件树相同。Windows首次旧OCR关闭挂起超时，局部3例通过后仅重试已终态job，第二次1702passed及wheel全通过；原失败/root cause UNKNOWN保留。Linux1698passed/4skip；独审4dcd41e通过。P010/P011工程done，科学/学生/目标环境未验，合入后收据本地保存随下一正常任务带入。用户要求回传上游，目标聊天已核验。

## 2026-11-05 P012完成

真实GUI走查闭环、非私有练习与学生短任务完成。76bd5b7两项P2修复独审通过，最终dd99855经PR62正常合入f30ea5d且树相同。Windows1703passed、Linux1699passed/4skip，双平台wheel/check--all和必需门禁通过。本机两项旧canvas失败及GPU日志保留，定向6例/独立wheel通过不销账。用户要求连续自动推进，已转达上游并获接受，最终回传后上游派发下一项。详见P012/final-delivery。

## 2026-11-06 P013研究和正式准则完成

三候选比较、公开CC0核标注CPU探针及独审完成；PR63/d85c3e5研究，PR64/cddf759成熟算法优先准则MD/HTML，准确树比对一致。两PR双平台完整门禁通过，无重试。计数最差误差71.01%不授予科学准入，下一项成熟实现真实调用和训练重叠核验。用户要求连续回传/派发，最终交接以P013/final-delivery与任务回执为准。

## 2026-11-06 P014完成成熟核计数直接调用研究

CP4.2.8/StarDist0.9.2真实CPU对照，冻结3开发/10评估，20行独审复算一致。PR65候选c86e3db合入main07838c2且tree一致；最终双平台全门禁/wheel成功。规则清单初失败已保留历史并修复，旧CI取消不计通过。研究结论/成本/科学限制和下一范围见P014/final-delivery；原dirty树和安装保留。

## 2026-11-06 P015 isolated nuclei adapter

独立轻量nuclei-tool及显式CLI接既有WorkflowSession，固定进程外StarDist环境/权重，uint8准入/原坐标标签/核数/出处/零与失败区分。真实对照及独审修复signed TIFF、长错误原因、venv入口；补传递边界负例，所有必需CI后正常合PR66/main a761284，正式回传上游自动接续。未改WB、未扩科学准入或安装发布。

## 2026-11-06 P016研究用户流程完成

最终验收：PR67已合入main 6bd4680530dc4697f8d394a96fd288723222ddb8，与候选16d32b12f3980cf2dcaeb3ec9d145488378c6dcd文件树diff退出0。quality42157212799成功：Windows1737 passed/10 warnings/1410.11s；Linux1733 passed/4既有Windows专用skip/10 warnings/951.94s；两平台随后wheel/check --all完整通过。rules42157213226、desktop-environment通过。只读独审绑定候选通过。2026-11-06已成功向上游01a19bfd-f3ab-7502-86da-9f61953d1c8a(local)发送正式入口/截图/证据/CI/独审/PRmain/边界和下一建议，要求自动接续。观察进程87597已exit0。 科学/学生/环境边界见P016/final-delivery，不由工程通过关闭。

## 2026-11-06 P017 孔板研究

收到释放后保留P016收尾并合入main；上游B020规划随本任务集成。冻结公开BCA原表/布局/参考摘要，直接运行SciPy与statsmodels，发现LoQ及体积/空白风险，不授科学准入。当前独审与PR未完成，详P017任务与研究证据。

## 2026-11-06 P017最终验收

PR68/main f8f69b5与独审最终b2eaccd树一致；quality42164152689双平台check --all/wheel成功（Windows1737passed/10warnings/1132.98s；Linux1733passed/4既有skip/10warnings/909.25s），rules42164152703及desktop成功。指定独审与增量pass。研究完成，未授科学/学生准入；收据本地提交随下一任务，树释放，下一任务上游新窗口。详P017/final-delivery。

## 2026-11-06 P019单板CSV研究适配完成

独立bca_tool 0.1.1贯穿严格CSV/记录、逐孔插值、真实worker/提交和核验重开；独审修复资产完整性及ULP端点，PR71正常集成。未改第三方/P018参考/旧UI，未扩科学准入。一次本地收尾后释放树，上游新窗统一入口/结果与编排。

## 2026-11-06 P020统一工作台候选

三卡/真实BCA桌面闭环/核分割帮助/真实WB编排入口完成，未动方法或门禁。定向22+10通过、WB3通过、真实核分割46核与新进程重开通过；16图核验。全check仍在运行，初轮格式失败和GPU中断保留。待准确候选独审、CI和上游集成，唯一写入权未释放；详P020/README与任务卡。

## 2026-11-06 P020统一工作台交付

三工具入口/BCA真实桌面提交结果/核分割帮助/真实WB编排入口完成。独审R01/R02及CI旧等待竞态最小修复，PR72正常集成main aa3302a，与0d83f4d树一致。一次本地收尾后释放，下一任务上游新窗；详P020/final-delivery。

## 2026-11-06 P021工程交付

P021核分割/BCA固定研究方法接入既有画布/模板/执行成果，真实模型与同输入数值一致。R01/R02经指定增量独审关闭，PR73按上游安排正常合入main2a3c7a3，与3f425b5同树。一次本地收尾后释放，下一任务上游新窗；详P021/final-delivery。

## 2026-11-06 P022工程交付

P022可选装配完成，R01/N01经指定独审关闭；准确47ded5e全部必需CI成功，PR74正常合入main b13e71a，完整树一致。首轮Linux关闭挂起保留UNKNOWN，单次重跑后固定独审允许集成。一次本地收尾后释放树，上游新窗派下一任务，详P022/final-delivery。

## 2026-11-06 P023独立目录交付

六wheel私有运行时/原生EXE与构建身份、目录说明完成；真实三工具/模板/冷重开及最终工件独审通过，PR75在四必需CI成功后正常合入main d3733a7。一次本地收尾后释放共享树，由上游新窗推进；不替换旧安装、不发布，不把工程证据当科学准入。
