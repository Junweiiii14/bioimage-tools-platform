# P-009 M2真实工作流可视编排与模板复用

<!-- PROGRAM_TASK_META {"id":"P-009","status":"in_progress","work_package":"W13","depends_on":["P-006","P-008"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0","owner":"chat-01a199d4-dac3-7dd3-af35-cdad7d361934","base_commit":"275560475d39426434416c74feeb0c2f259d1402","head_commit":null} -->

## 输入与前置

4.0第4章/12.4；P008真实执行器、P007同一工作流契约，P006可重复性能/交互基线。沿用QtWebEngine宿主、四主题及现有导航/结果来源，CLI与GUI不建立不同执行器。

## 用户可见成果

实际模块目录展示版本、端口、资源/质量限制及不可用原因；用户从模板创建、添加/删除/替换允许节点、编辑连接和schema参数，保存重开仍保持，保存为实验室模板后绑定第二批输入一次运行并定位成果。预设流程动画、只读流程图或空模块清单不满足验收。

## 范围与实施

先真实context并读产品/设计上下文，应用impeccable的Operate工作流。宿主增加目录/命令/投影，web_ui增加有键盘操作的节点画布、步骤列表、参数表单和成果定位；不替换原WB工作台。技术选型先做有限节点的连接/键盘/布局探针，确需依赖才固定版本独立审查，不直接更换框架。

图的计算定义与节点位置/视图状态分离；全部编辑经同一确定性预检。保存失败保留草稿、选择和焦点；旧后台事件不覆盖新revision，不夺取IME/文本焦点。移动不重算，分析参数只重算依赖链，样式仅重做报告。运行中可浏览中间/已提交结果；暂停请求与安全节点边界已暂停区分，取消等待真实退出/排空。成果链接只能来自已提交并核验资产。

## 验证与完成

真实QtWebEngine按钮与键盘路径覆盖新增/连线/删除/参数编辑→保存/重开→模板复用→第二批真实worker出表图。非法连接具体解释；输入异常隔离及运行状态真实，取消/关闭、旧任务新草稿、焦点/IME、主题及窄窗均有证据。1440×940、960×640与适用窄窗按现有规范截图和有界独立视觉审查；性能沿P006实际范围测量，不用截图证明原生目标机/DPI。中文5–10分钟操作单、真实成果、来源/已知限制、全门禁/隔离wheel及准确提交独审、PR/必需CI后才done。未取得用户体验不代签。

## 当前状态

进行中，依赖已完成；后台和首版实际界面已实施，仍需完成交互覆盖、视觉/性能验证、准确提交独立审查及PR/必需CI。其他实验/Agent/安装器发布不在本卡范围。


## 2026-11-02激活

P006已done；P008准确b4847a5独审/四必需CI/双侧wheel后PR53正常merge2755604，已核候选与main同tree。当前codex/p009-visual-workflow从同main激活真实Web编排，先加载scope .规则和设计上下文；不以CLI/预设流程替代M2，不扩新科学算法或其他实验。入口校验一次，已有授权内连续推进，集中可运行候选独审，本地定向/最终CI全量。


## 有限画布交互探针

已运行并完整读取P009 scope .上下文707行，绑定main2755604。按既有Operate设计体系，新增原生DOM/SVG图组件，有限3节点实际P007定义投影；原生focusProxy键盘移动/删除、端口按钮连线、布局不改计算定义、960×640无页面横溢的探针通过，npm check:web退出0。无需新增画布依赖。初次两轮探针的焦点目标/JS对象序列化错误保留，不算产品引擎失败或通过；修正探针后组件源码未变。work/evidence/P-009/graph-probe.json及可复现probe记录范围。当前尚无编辑器宿主/保存/表单/实际执行连接，不能将此探针称M2完成，后续接同一P008执行器。

## 2026-11-02 已连接后台与实际编排界面

后台固定命令、单一共享存储所有者、真实批次执行/暂停恢复/取消排空及成果核验已接WebChannel。图/步骤/目录/schema表单、保存运行和成果区已有首版。模板template_version=1封装保存definition+layout，GUI及CLI加载器接受新旧格式。完整范围与失败修正见work/evidence/P-009/connected-editor-progress.md。

最新定向四文件11passed47.73秒，退出0：store/session/bridge/web。界面实际按钮完成两批合成输入4000.0→40.0，保存保持ROI输入DOM/焦点；模板布局跨项目保存/重绑定验证通过。pyright0 errors，目标Ruff通过，web静态检查通过（范围保留）。本轮未运行本地全量、隔离wheel、最终视觉/性能或独审/CI。仍in_progress，不能作为M2完成。

## 2026-11-02 完整界面链路及有效视觉采集

真实Web五流程5passed39.93秒，覆盖节点编辑/预检/重开、GUI实验室模板新TIFF+CLI、参数边界/模拟IME、依赖复用和运行中新草稿焦点。Ruff/type/web静态通过。有效原生Windows12图采集15.42秒，通过非纯色/颜色一致性校验；离屏纯色/旧帧/RAF失败原证据保留，不算视觉通过。一次detect无主要项、有1backdrop advisory。详见work/evidence/P-009/ui-edit-validation.md/json。已写中文操作单和模板v1契约；视觉独审/性能/wheel/准确代码独审/PR必需CI仍待做，不改in_progress。

## 2026-11-02 独立视觉修正与确认

Fresh reviewer首轮bb42有效12图结论fix，唯一问题为窄窗任务密度。一批顶部/高级元数据折叠/图起点修正后，同12图确认15.57秒，原独立审查者评分resolved，disposition ship仅覆盖该fix。完整原结论visual-review.md，设计一致性documenter证据design-conformance.md。真实Web5流程+原生图探针6passed41.34秒，type/web/Ruff通过。所有失败和原图保留；有效主检+确认预算已用完，不再自主视觉循环或第二detector。性能、wheel、最终准确代码独审和PRCI仍未做，保持in_progress。

## 2026-11-03 正式性能/隔离安装准备

新增原生采样工具及performance-measurement.md，r5两场景1+0诊断退出0，非正式分布。最小Qt等待实验定位旧qWait线程饥饿，新AsyncEventPump的真实存储创建/回执/排空1passed1.80秒；失败不改写为通过、不改产品/P006旧工具。type/Ruff通过。tooling/installed_wheels.py新增实际已安装Web编排资产/保存重开/4000→40/6worker/布局模板+CLI校验，已静态编译但还没运行，不能当安装通过。正式默认5+30冻结后新目录串行运行；详细样本与终点边界按新测量说明。

## 2026-11-03 已安装编排器验证通过与测量修正

全环境wheel第二轮exit0，新P009独立GUI探针验证真实已安装JS/CSS、保存重开、4000→40、6实际RunRecord/PID和布局模板CLI；旧probe全部保留，-u只增强输出。第一轮app.quit轮询问题已记录为主动终止/exit1，不算通过。坏TIFF混合输入GUI1passed9.48秒，坏输入隔离、有效40、原字节保留。正式5d0c355采样exit1，8组UI数据完整，控制第二轮顶层const重复声明修为IIFE并检查true回执；2轮诊断过，待重新冻结完整默认采样。无阈值/超时/断言弱化；.gitattributes只追加P009 frozen-runs字节保留规则。详见delivery-probes.md/json及原始失败数据。
