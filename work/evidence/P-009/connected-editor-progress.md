# P009 已连接编辑器的阶段验证

本记录为工程进度，不是最终M2验收。基线main275560475d39426434416c74feeb0c2f259d1402，分支codex/p009-visual-workflow。当前提交前源码摘要见connected-editor-progress.json；最终独审和CI尚未进行。

## 实际实现

- 单一AsyncStorage拥有Workspace；新编辑服务与既有WorkflowBatchSession共享存储，不新造运行器。固定后台命令负责保存/预检/冻结/绑定/导出/成果核验；GUI不读取大图或运行科学方法。
- 不完整草稿允许保存；只有严格WorkflowDefinition及同一编译器预检通过才冻结真实批次。CAS保留历史，布局与计算定义分离。
- 工作台WebChannel已接真实模块目录、DOM/SVG画布、步骤选择、增删替换/端口编辑、schema参数表单、高级JSON、保存/运行、暂停继续取消及已提交成果。不同操作的覆盖见下，不将控件存在当作全部行为通过。
- 保存回执不替换活动表单DOM；新草稿不被旧运行投影替代。原始输入、RunRecord、资产摘要核验仍由同一后台负责，失败不冒充有效零。
- 模板新增template_version=1封装，包含definition及layout。GUI导出使用新封装；GUI及CLI共用加载器，继续接受原P007/P008定义格式。计算定义格式没有改变；模板封装不是新算法。
- 原图新建沿既有公开suggest_analysis_for_crop方法生成全图原整数坐标建议，不宣称新几何方法或科学验收。

## 已取得证据

- `.local/p009-authoring-connected-targeted.log`：最新关联四文件store/session/bridge/web共11项通过，47.73秒，退出0，涵盖下列后台生命周期和两批真实界面链路。最后`.local/p009-connected-web-final-static.log`的npm run check:web退出0；全部新增Python文件与测试目标Ruff退出0。
- `.local/p009-portable-template.log`：存储3项通过，15.51秒，退出0。覆盖不完整草稿/CAS/布局不改变计算键、实际三批4000.0→40.0/样式缓存及核验成果、导出重开保留布局并绑定另一输入。新CLI加载器的传统格式兼容在此直接覆盖，尚未用新封装启动CLI子进程。
- `.local/p009-web-two-batch-values.log`：真实QtWebEngine/WebChannel界面1项通过，13.03秒，退出0。实际按钮新建合成输入、改标题保存、选择分析步骤/ROI表单、保存保持输入DOM及焦点、第一批真实worker出4000表和报告、绑定另一合成输入再运行，表格单元格精确40.0，旧WB项目保持空。程序化DOM点击不等于物理鼠标/输入法或最终用户体验验收。
- `.local/p009-template-web-types.log`：pyright退出0，0 errors/warnings/informations。目标Ruff退出0。`.local/p009-web-schema-static.log`：npm run check:web退出0；既有checkJs检查范围不冒充整个编辑器的完整类型证明。
- 后台较早定向验证的当前范围：pending freeze前cancel/close不启动worker；已提交中间成果可读；真实暂停后关闭/冷重开awaiting_resume，显式继续才派发；原生宿主关闭等待两个所有者排空。最新四文件关联测试结果随后补记，不用较早结果宣称后续全部修改通过。

## 失败与修正

- 首次Web测试固定假定4个成果，但实际后台成果数量更多，造成40秒等待超时。测试改为对应后台真实逐项成果数；产品执行和成果读取当时已完成。
- 表单初版漏掉schema prefixItems固定长度数组，出现undefined.$ref；补齐固定元组投影及布尔控件后通过。保留`.local/p009-web-schema-first.log`和`p009-web-second-batch.log`，不称原测试通过。
- 第二批绑定回执原只更新saved投影而未替换前端当前输入，已明确将bind作为替换编辑图/布局的操作，避免继续向旧输入提交。
- 精确表格测试最初写成字符串40，而真实CSV契约是40.0。原始第二批资产已核为40.0；修正测试为精确40.0。`.local/p009-template-web-targeted.log`保留1failed/3passed，不缩小断言为任意文本包含40。
- 静态检查最初发现fixture导入F811/unused及长行，改用仓库既有显式同名导出和拆行，未增加ignore。

## 剩余验收

完整界面增删替换/非法连线解释、保存重开、实际实验室模板第二批GUI链路、计算依赖/样式/布局复用的GUI证据、IME/旧任务新草稿、所有表单边界与恢复、四主题/1440×940/960×640/窄窗、P006范围性能、操作说明、隔离wheel、绑定准确提交独审和PR/必需CI。没有重复跑本地全部测试，没有最终视觉截图/审查，不宣告M2或全目标完成。科学留出、干净目标Windows、物理DPI/GPU及真实用户体验限制继续保留。
