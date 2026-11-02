# P-003 方法和数据验证登记及评估基础

<!-- PROGRAM_TASK_META {"id":"P-003","status":"in_progress","work_package":"W01","depends_on":["P-001"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a199d4-dac3-7dd3-af35-cdad7d361934","base_commit":"f2dc5ad44fba2e4f951b8987f0babb6b41c1d1a2","head_commit":null} -->

## 执行状态

机器元数据是本卡状态的唯一字段；planned表示尚未执行。B-008发布方案和修订任务卡不等于本任务已经实施。激活时核对编号、授权范围和前置任务，把执行权威移交到正确产品树；记录实际execution_root、owner及base/head，源副本改为带目标路径和提交的只读指针，不同时更新两套状态。

## 输入

B-007第7/8/9/13.3章、work/evidence/B-007/public-development-data.json及其来源/下载核验证据；B-004科学研究、T-082科学缺口、旧方法说明与解析参考。公开登记记录不等于文件已经取得、许可已覆盖全部用途或具备科学真值；按逐文件状态读取。

## 允许范围

方法/数据记录契约、合成参考与评估工具、文档；不上传私有数据，不将公共数据自动加入安装包或训练集，不生成虚构批准。本卡不开发后续实验算法；首阶段仅接入V0实际需要的验证能力。

## 执行步骤

1. 列出旧方法、拟新增校正方法、支持范围与UNKNOWN项，明确每项所需证据、负责人角色和方法/实现摘要；工程等价、设计准备D1与正式方法准入S1分别登记。
2. 按B-007数据登记保存dataset/file ID、版本、来源URL、许可及用途、实际下载/解码状态、文件摘要、标注类型、样本/技术/生物重复和单位；unknown不补成通过。私有路径保持本地，取得数据仅按本任务明确的文件白名单、用途和资源范围执行。
3. 开发/调参与独立留出按真实实验来源分组，原图派生裁片、同视野时间点、同供者事件等保持分组闭包。合成算术预期、软件示例、人工标注与独立真实真值分开，数据集入口或论文配图不冒充原始文件。
4. 根据开发集及独立参考制定逐例参考、指标、容差、排除规则、错误放行和完整分母，在独立留出评测前冻结；缺少正式值时拒绝输出科学通过。实现输出不得回填为期望，留出成绩不能用于反向放宽门槛。
5. 用解析/合成图和类型化表建立可运行评估脚手架，保存失败样本、尝试版本、适用域和机器可读报告。证明同源泄漏、缺参考、未批准方法及未知阈值不会产生正式准入；研发候选报告仍可生成。
6. 独立审查登记结构和验证限制；为每个后续方法晋级单列任务，不等真实材料才做工程。P-003完成只表示D1与评估基础具备，不把T-082科学待办或任何新方法S1自动标通过。

## 验收与退出

可运行验证框架及独立合成预期；来源/用途/数据状态可追溯，真实未知项明确保留；无伪造科学签字/成功；D1、方法S1及工程完成分开。

## 失败与待决处理

未经授权样本不用；同源派生物跨留出需修复。科学负责人/容差未定只阻止对应方法晋级，不阻止本任务工程完成。

## 用户可见验收安排

按B-007第8/9/13.3章提供科学证据与准入状态说明；不要求用户签署未知容差。未取得的体验或方法负责人确认写待验；工程框架可独立完成。

## 验证和审查记录

产品实施和验收未运行；B-008仅修订任务卡。实施后记录命令、退出码、环境、base/head、样本/资产摘要、独立预期、真实结果、未覆盖项及审查者。产品检查按实际目标树已有命令执行，不发明dev.py子命令。产品变更须绑定准确提交独审；约定集成完成前保持in_review，未经发布不写已发布。

## 继续入口

本卡未完成步骤为继续位置；主依据为docs/plans/research-platform-rd.md第7/8/9/13.3章，B-005仅作治理历史。修改规则或范围后重载context，收尾更新任务与handoff。

## 2026-11-02激活

P002已PR48正常合main f2dc5ad，四必需CI及准确独审通过。本树codex/m1-workflow-foundation在8710d76接续，B011已拆清M1/M2依赖并重载真实新main规则，最终增量独审进行中。先实现通用数据/方法评估契约、分组泄漏拒绝、独立解析期望的实际WB用例评估和机器报告，保留B007源记录的逐项unknown；不下载新数据、不伪造负责人/科学准入，不改旧算法/容差。公开入口仍package.api，现有四包内实现，不新建空公共包。

## 首个实现与局部验证

已在tool_contracts公开API增加独立schema v1来源/分组、冻结计划/观测/报告及D1方法登记；runtime纯评估解析父子闭包、冻结身份及状态/空值，不授予S1；tooling.wb_method_validation先写计划再调用真实WB公共用例，完整保留B007原目录记录而不冒称源文件已下载。旧AssetRef/存储schema、WB公式/容差、依赖锁不变。安装门禁仅追加runtime/contracts独立环境的有效0、来源泄漏拒绝与无科学批准验证。

Win11/Python3.12.14，当前未提交实现：`uv run --locked --no-sync python -m pytest tests/test_method_validation.py tests/test_workspace.py::test_contract_schema_snapshot tools/wb/tests/test_module_execution.py -q --basetemp=.local/pytest-p003-integrated-c` exit0，30 passed/3.85秒；包含Hypothesis合成数值不晋级S1、派生链分组闭包，身份/输入/单位/缺参考/无效空值及实际40/4000/0/空值报告。局部评估首次12passed/1failed发现model_copy的True经JSON变1.0，现先严格Python重新校验，再序列化；后13项exit0/2.35秒，未改测试期望。早期工具适配字段误用已按实际request/x0/y0/x1/y1 API修正，保留.local/p003-first-run部分失败目录，不冒充成功。

真实命令`python -m tooling.wb_method_validation --output .local/p003-analytic-run-b` exit0，五例工程通过，scientific_admission=not_granted。全仓Ruff/format（1109文件）、policy（185产品文件）与完整Pyright（0errors）exit0；最终完整门禁/隔离wheel、冻结证据、准确提交独审与PR集成尚待完成，不据局部结果标done。

## 初次独审Request changes与修复

准确f2dc5ad..debeb3e被非作者提出P1共同父身份未闭包导致同源泄漏漏判、P2冻结polarity/band_bounds/quant_policy被工具忽略；独立反例均实际复现。报告work/evidence/P-003/review-request-changes.md，不把初次13项通过当独审接受。现闭包同时跟踪祖先record身份/分组，严格核对全部实际设计参数及整数类型；新增性质/真实评估拒绝与三字段/布尔坐标反例，18 passed/3.08秒、局部Pyright0。源debeb3e的全门禁在pytest阶段因这些缺陷主动停止，exit1；通过CIM核对本树python/uv及所属shell后停止自己进程树，复查遗留子PID均已退出。该次仅早期Ruff/类型/导入/JS通过，不宣称完整门禁通过，旧冻结证据与execution.json原样保留，新候选另冻结/全验/独审。追加方法登记断言时曾误插到纯性质测试导致NameError及precommit失败，已移到实际文件测试，未改期望/容差，修后13passed/2.43秒且提交钩子通过。
