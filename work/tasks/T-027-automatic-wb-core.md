# T-027 自动泳道、裁剪与积分边界建议子任务

状态：review（本地实现/作者验证完成，待协调分支独立审查与 UI 集成）

工作树：t024-auto-core；基线2442d40811c0d9770eb7fe5ac1986b65d2cfadd0；当前产品提交以git HEAD为准。

完成：原像素自动泳道/裁剪候选；自动积分边界；schema8机器建议证据与过期校验；用户图上调整后原几何重算；无人工审核伪造；公开API及针对性测试。

范围：tools/wb 新领域/用例/适配器及API，project_analysis自动就绪/结果来源标注，crop_suggestions schema8读取；既有crop_detection只新增内部公用检测原语别名，旧算法不变。

验证：40 targeted passed/1.31s；Pyright0；Ruff通过；真实10TIFF只读探针详见work/evidence/T-027/automatic-core-validation.md。未跑全仓（由协调分支集成验证）、未独审、未验证真实科学准确率。任务最初尝试T-024A被规则加载器拒绝（ID格式）；随后T-024成功生成回执，不弱化规则。

协调：根代理负责平台/宿主/后台任务/渲染导出保护，UI子代理负责图上调整与三栏。机器证据不改变原图，不推断蛋白/样本/归一化关系。

协调分配唯一T-027后重新生成作用域回执；原T-024回执未提交避免冲突。
