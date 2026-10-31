# P-002 V0成熟WB方法独立调用与真实成果对照

<!-- PROGRAM_TASK_META {"id":"P-002","status":"in_progress","work_package":"W02","depends_on":["P-001"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a190e6-02b1-74e3-a7b9-bd5fbc3f36fe","base_commit":"29930f62a0b158189b76e0fad7d090d632f149d6","head_commit":null} -->

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

## 2026-10-31激活

P001已独审并经PR47四必需CI正常合main29930f62，当前从该准确main建立codex/p002-wb-headless-module（执行树bioimage-v0）。成熟用例冻结预期与旧worker真实证据见work/evidence/P-001/frozen-case-design.json和frozen-baseline-result.json；无归一化公式扩展。接入调查是候选，按实际代码验证，不以空接口、单元测试或文档代替完整V0。

## 2026-10-31局部实现验证

当前未提交模块契约及成熟用例适配；未修改原科学公式、AssetRef v1或旧storage schema。Win11/Python3.12.14，base/HEAD29930f62，执行 `.venv/Scripts/python.exe -m pytest tools/wb/tests/test_module_execution.py tests/test_workspace.py::test_contract_schema_snapshot -q --basetemp=.local/pytest-p002-module-b`：exit0，12 passed，3.30秒。覆盖解析独立预期40/4000、旧调用一致、原图不变、请求摘要/角色/修订/实现拒绝、非法ROI空值及原因、取消、未知dtype、JSON异常、成果端口和事件身份。此为局部检查；新worker、持久成果、薄GUI、隔离wheel、全门禁、独审及PR集成尚未完成。

## 2026-10-31真实worker与持久化增量

已实现静态wb_v0_compare worker与工具独立module_worker；旧分析和新模块分别真实计算，生成两张非空CSV、来源清单及两份机器结果。RunSession沿原PID/退出/取消路径，在存储线程验证候选成果、导入登记资产并最终commit_result。格式与兼容边界见docs/contracts/wb-module-v0.md。现有原方法/旧默认运行路径保持。

本树未提交增量，base29930f62，Win11/Python3.12.14。指定工作区TEMP/TMP=.local/p002-process-temp后，执行 `.venv/Scripts/python.exe -m pytest tools/wb/tests/test_module_execution.py tests/test_module_run_session.py tests/test_run_session.py tests/test_async_storage.py tests/test_workspace.py::test_contract_schema_snapshot -q --basetemp=.local/pytest-p002-integrated-c`：exit0，34 passed，21.99秒；日志.local/p002-integrated-tests.txt。证明真实新worker数值40/4000、身份/文件摘要、无覆盖/非法ROI空值；真实RunSession成功重开、manifest后退出7、输出缺失/同尺寸篡改、取消，以及原RunSession/异步存储行为。

首次组合检查16 passed/1 failed：既有import_bytes测试因沙箱默认TEMP写入PermissionError失败；独立TemporaryDirectory写入复现权限错误，未改产品或测试预期，改为工作区TEMP后该项1 passed，再完成上述34项组合验证。初始JSON极深嵌套测试发现仅依赖Python递归上限不确定，改为显式32层准入后通过；首轮Pyright提示未知容器类型，已用边界cast明确类型，无ignore。受影响文件Ruff、Pyright（0errors）和dev.py policy（180产品文件）均exit0；全门禁、隔离wheel及独审未运行。

下一步：共享会话控制器与完整无GUI宿主命令、现有工作台薄对照入口及中文验收流程；扩大路径/成果准入负例，最终全门禁与准确提交独审/PR集成。不得据本增量将P002或V0标done。
