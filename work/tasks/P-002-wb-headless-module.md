# P-002 V0成熟WB方法独立调用与真实成果对照

<!-- PROGRAM_TASK_META {"id":"P-002","status":"in_review","work_package":"W02","depends_on":["P-001"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a199d4-dac3-7dd3-af35-cdad7d361934","base_commit":"29930f62a0b158189b76e0fad7d090d632f149d6","head_commit":"2591309eecffeb07558d3492bc3f69425dc6d24a"} -->

## 执行状态

机器元数据是本卡状态的唯一字段；planned表示尚未执行。B-008发布方案和修订任务卡不等于本任务已经实施。激活时核对编号、授权范围和前置任务，把执行权威移交到正确产品树；记录实际execution_root、owner及base/head，源副本改为带目标路径和提交的只读指针，不同时更新两套状态。

## 输入

P-001接入并确认的实际产品树；B-007第2/3/4/12.2/13.1节；冻结旧方法、历史样例、package.api及现有worker/Workspace提交契约。样例优先采用有独立预期的合成或许可明确的小型输入，原图/ROI/旧方法参数均固定。

## 允许范围

一个成熟WB用例及公开API、最小模块和worker适配、既有工作台内的薄对照入口、相关测试/证据。保持实验公式、旧uint8/uint16入口、当前界面风格和历史语义；不引入自动校正、新方法、通用SDK、任意DAG或新实验工具。

## 执行步骤

1. 选择成熟定量用例，记录原入口、位深、极性、坐标、参数、错误状态、方法版本与旧输出。冻结正常样例及不支持dtype/非法ROI/无效归一化分母等适用反例；独立预期和容差在运行前约定，旧结果是兼容参考而非新方法科学真值。
2. 由本任务统一最小ModuleSpec、ExecutionRequest、OutputManifest契约及实际端口；保留既有AssetRef v1的严格物理引用。后续科学元数据用ScientificAsset组合AssetRef，事件名为ExecutionEvent，工作流为WorkflowSpec；只实现本次真实用例需要的字段，不先建空的全套协议或第二套资产身份。P-004/P-005沿此命名和版本演进，外部只经package.api调用。
3. 无GUI入口与原界面调用同一成熟用例，不复制算法；固定注册、导入无副作用。纯domain不依赖Qt、Workspace、子进程或任意I/O；适配层负责受限输入读取和输出封装。
4. 用真实worker执行冻结请求，复用Workspace的运行、退出凭据与结果提交路径。保存请求/模块/方法/参数/输入摘要、真实RunRecord和正式输出的关联；worker输出manifest后，宿主确认真实成功退出并校验必需文件才提交。失败、取消或非零退出不得得到成功结果；不以伪PID、直接复制旧表或绕过提交替代运行。
5. 关闭并重开测试工程，从已提交结果打开数值、差异和来源；失败运行仍有原因，旧项目及历史结果仍可打开。提供v0-compare/measurements.csv、differences.csv、run-manifest.json，字段含样本/指标/值/状态/方法与源引用；结果实际生成，不将空差异表当对照通过。
6. 在现有WebEngine工作台内增加薄的“旧方法对照”验收入口、运行反馈与结果打开按钮。按第4章沿用主题、导航与控件；用户可点运行、看实际输出及差异、重新打开工程。较大读取和计算不阻塞GUI；不重做工作台或平行三屏。
7. 用既有入口与独立入口处理同一冻结样例，逐项比较数值、失败语义、来源及历史读取；拒绝显示资产、未知dtype、错坐标及非法身份。验证manifest已发但进程失败、输出缺失等适用反例不会提交成功；不能为一致性放松旧校验或科学容差。
8. 运行受影响数值/契约/worker/存储/GUI及反向依赖检查，并在隔离wheel安装环境通过同一无GUI用例。新增公共包若确实必要，补真实依赖边界与独立安装证据；集成按目标树既有门禁执行。
9. 提交可运行代码、样例/操作单、输出与差异证据，交非作者按准确base..head独审；处理发现后复核最终提交。记录旧调用兼容、回退入口、未覆盖科学/目标环境范围；满足本卡验收与约定集成后才能done。

## 验收与退出

同一冻结旧方法由真实worker独立运行并经Workspace持久提交；正常/失败两条入口行为一致且证据可追溯；关闭重开仍能打开真实成果；原界面和历史保留；隔离wheel运行通过；薄GUI对照入口可按中文操作单使用；绑定准确提交的独审及约定集成完成。仅交协议类、CLI打印、模块清单或静态截图不满足V0。

## 失败与待决处理

需要改变公式、反相上限、预处理或结果定义时另立科学变更任务；不把旧方法工程等价宣传为新自动校正验证。独立科学材料或外部电脑缺失单独保留，不冻结可完成的V0工程；安装器发布和替换在用版本不由本卡自动授权。

## 用户可见验收安排

按B-007第12.2/13.3节交付可运行入口、冻结样例、5–10分钟中文操作单、真实对照表/来源和已知限制。展示“运行→打开差异→关闭重开→旧项目仍可用”；工程测试与用户尚未体验分别记录，未取得确认不能代签，也不额外冻结内部工程。

## 验证和审查记录

产品实施和验收未运行；B-008仅修订任务卡。实施后记录命令、退出码、环境、base/head、样本/资产摘要、独立预期、真实结果、未覆盖项及审查者。产品检查按实际目标树已有命令执行，不发明dev.py子命令。产品变更须绑定准确提交独审；约定集成完成前保持in_review，未经发布不写已发布。

## 继续入口

本卡未完成步骤为继续位置；主依据为docs/plans/research-platform-rd.md第2/3/4/12.2/13.1节。V0交付是本次第一阶段终点，不自动推进V1、IF或Agent；后续按已授权范围与前置依赖激活。修改规则或范围后重载context，收尾更新任务与handoff。

## 2026-11-02实际接手与完整门禁核实

接手分支codex/p002-wb-headless-module、HEAD78403be43b225da3626e3a6ef0a8aeda2cbbbaec；新执行聊天01a199d4-dac3-7dd3-af35-cdad7d361934独占产品实施。真实goal为active、无token预算，初始证据work/evidence/B-010/goal-state.json。4.0同步成果保留；本卡仍只收拢原P002范围。

通过旧聊天原生命令记录核实`uv run --locked --no-sync python dev.py check --all`实际completed、exit0、890398ms；对应日志.local/p002-check-all-a.txt。Windows/Python3.12.14，工作区TEMP/TMP，Qt offscreen/disable-gpu。1537 passed、10 warnings、796.95秒；Ruff、format、Pyright（0 errors）、导入契约、JS检查与独立wheel安装均通过；隔离桌面wheel实际验证4000精确对照、正式资产和重开。没有从失效句柄或日志23%猜测成功。此为原产品HEAD的工程门禁；新文档规则/PR仍需正常集成检查。

同样从原生命令记录核实冻结证据脚本exit0、26145ms，五组真实运行位于work/evidence/P-002/frozen-runs/，source_commit为78403be。接手后重新对原五个Workspace执行`python -I -m bioimage_app --v0-open`，逐组exit0、真实RunRecord一致，并校验每份保留成果SHA256；恢复验证命令exit0，证据recovery-verification.json。原冻结证据和历史运行未重写。有效40/4000/0、无效ROI空值、位深端点待复核空值分别保留。

已向非作者审查者派发准确29930f62..78403be的只读审查，尚无最终结论；不得据既有局部UI审查宣称产品独审通过。PR与必需CI尚待完成。中文操作单docs/wb-v0-acceptance.md已存在；用户尚未实际体验，科学/目标环境未验，不代签。

## 2026-10-31激活

P001已独审并经PR47四必需CI正常合main29930f62，当前从该准确main建立codex/p002-wb-headless-module（执行树bioimage-v0）。成熟用例冻结预期与旧worker真实证据见work/evidence/P-001/frozen-case-design.json和frozen-baseline-result.json；无归一化公式扩展。接入调查是候选，按实际代码验证，不以空接口、单元测试或文档代替完整V0。

## 2026-10-31局部实现验证

当前未提交模块契约及成熟用例适配；未修改原科学公式、AssetRef v1或旧storage schema。Win11/Python3.12.14，base/HEAD29930f62，执行 `.venv/Scripts/python.exe -m pytest tools/wb/tests/test_module_execution.py tests/test_workspace.py::test_contract_schema_snapshot -q --basetemp=.local/pytest-p002-module-b`：exit0，12 passed，3.30秒。覆盖解析独立预期40/4000、旧调用一致、原图不变、请求摘要/角色/修订/实现拒绝、非法ROI空值及原因、取消、未知dtype、JSON异常、成果端口和事件身份。此为局部检查；新worker、持久成果、薄GUI、隔离wheel、全门禁、独审及PR集成尚未完成。

## 2026-10-31真实worker与持久化增量

已实现静态wb_v0_compare worker与工具独立module_worker；旧分析和新模块分别真实计算，生成两张非空CSV、来源清单及两份机器结果。RunSession沿原PID/退出/取消路径，在存储线程验证候选成果、导入登记资产并最终commit_result。格式与兼容边界见docs/contracts/wb-module-v0.md。现有原方法/旧默认运行路径保持。

本树未提交增量，base29930f62，Win11/Python3.12.14。指定工作区TEMP/TMP=.local/p002-process-temp后，执行 `.venv/Scripts/python.exe -m pytest tools/wb/tests/test_module_execution.py tests/test_module_run_session.py tests/test_run_session.py tests/test_async_storage.py tests/test_workspace.py::test_contract_schema_snapshot -q --basetemp=.local/pytest-p002-integrated-c`：exit0，34 passed，21.99秒；日志.local/p002-integrated-tests.txt。证明真实新worker数值40/4000、身份/文件摘要、无覆盖/非法ROI空值；真实RunSession成功重开、manifest后退出7、输出缺失/同尺寸篡改、取消，以及原RunSession/异步存储行为。

首次组合检查16 passed/1 failed：既有import_bytes测试因沙箱默认TEMP写入PermissionError失败；独立TemporaryDirectory写入复现权限错误，未改产品或测试预期，改为工作区TEMP后该项1 passed，再完成上述34项组合验证。初始JSON极深嵌套测试发现仅依赖Python递归上限不确定，改为显式32层准入后通过；首轮Pyright提示未知容器类型，已用边界cast明确类型，无ignore。受影响文件Ruff、Pyright（0errors）和dev.py policy（180产品文件）均exit0；全门禁、隔离wheel及独审未运行。

下一步：共享会话控制器与完整无GUI宿主命令、现有工作台薄对照入口及中文验收流程；扩大路径/成果准入负例，最终全门禁与准确提交独审/PR集成。不得据本增量将P002或V0标done。

本阶段实现已提交 `725fc6aef8df192f46fdceb122f6ff669251dd72`；提交钩子Ruff/format/policy通过。已请求独立审查者按29930f62..该head只读审查，结果待回报，不代替完整V0验收。

## 2026-11-02完整入口增量（等待最终门禁及独审）

在725fc6a基础上接入共享ComparisonSession、无窗口命令--v0-compare/--v0-open和现有工作台薄对照入口；原图读取、请求冻结、CSV解析在后台完成，真实worker及Workspace服务关闭后才报告会话完成。支持五个冻结样例及CLI显式原图/参数，成功、失败与取消可追溯；重开核验请求、输入及所有输出。中文操作单为docs/wb-v0-acceptance.md。

阶段独审p001_review对29930f62..725fc6a给出Request changes：模块codec遗漏宿主绑定会落入旧发布路径，候选manifest可能错误提交。现已通过ProcessEvent.payload_kind及RunSession强制匹配拒绝，回归包含missing_binding；本轮修复尚待准确新提交复审，不沿用旧结论。

Win11/Python3.12.14，当前未提交增量：`uv run --locked --no-sync python -m pytest tests/test_module_cli.py tests/test_module_run_session.py -q --basetemp=.local/pytest-p002-final-target-a`，工作区TEMP/TMP与Qt offscreen/disable-gpu：exit0，16 passed/56.81秒。覆盖五样例独立预期、重开、原输入不变、拒绝已有目的地、篡改后重开拒绝、运行前/中取消、float失败持久化、manifest后非零/缺失/篡改/硬链接/绑定遗漏拒绝。日志.local/p002-final-target-a.txt。完整Pyright exit0（0 errors），日志.local/p002-final-pyright.txt；旧会话63032恢复时句柄不存在，不据此猜测旧运行结果。

上一轮真实工作台两项测试2 passed/5.64秒，日志.local/p002-ui-capture-check.txt，1440与960宽截图在.impeccable/review/p002。impeccable_finish_reviewer局部视觉ship，documenter No changes；代码最终独审仍待执行。初始沙箱QWebEngineProfile异常退出0x80000003，使用既有CI离屏环境后通过，不宣称根因修复。CLI首次Windows -I忽略PYTHONIOENCODING导致输出gbk，改为显式UTF-8字节后8 passed/46.37秒；无放松断言。

门禁变更仅在tooling/installed_wheels.py追加验证：裸WB安装调用新公共用例得4000且不加载Qt/数据库；桌面wb extra安装通过真实CLI运行、差异与关闭重开，并检查UI资源随wheel存在。原安装检查、边界和阈值不删改，锁文件无变化。完整`dev.py check --all`当前运行中，不能提前写通过。最终准确提交独审、PR/CI及正式冻结输出证据待完成；P002保持in_progress。

## 2026-11-02最终独审与PR

非作者p002_independent_review已对准确29930f62..2591309eecffeb07558d3492bc3f69425dc6d24a给出Accepted，无阻断发现；独立34 passed/53.11秒、同尺寸输入篡改拒绝探针及全套同步/冻结成果摘要核验通过。详见work/evidence/P-002/review-final.md。状态in_review，PR48已创建，需四个必需CI通过后正常合并；未提前记done。此次后续仅记录报告/任务交接，不更改已审产品。
