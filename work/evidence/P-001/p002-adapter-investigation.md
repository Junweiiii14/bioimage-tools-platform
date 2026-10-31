# P002接入调查（候选，未实施）

已读当前四包公开API与README、analysis/worker_protocol/worker、process/run_session/storage和Workspace提交路径；下面是P001调查结果，实施须在P001完成、激活P002并加载context后进行，不能据此宣称新接口已存在。

## 确定复用的边界

成熟用例为analyze_annotations的legacy_bounds@1/fixed_grid@1；profile_integral@1与dtype_limits_review@1不改变。原uint8/16、半开ROI、闭区间band、明确极性、缺失/失败/真实零保持。冻结解析5例已实际比较公开API与旧worker，后续加入不支持dtype、显示资产拒绝和进程故障等适用反例。该用例不含归一化，不为不存在的分母算法增加公式或声称覆盖。

保留ProcessRunner的真实PID/有界帧/进程树退出与RunSession的PID保存后放行、取消先记账、成功退出后commit。保留AsyncStorage唯一线程和Workspace CAS/不可变导入。CLI可以运行QCoreApplication事件循环复用宿主，不打开GUI；wb_tool.api与计算worker仍不得依赖Qt。

## 拟实施的最小闭环

- tool_contracts.api导出严格版本化ModuleSpec/ExecutionRequest/ExecutionEvent/OutputManifest；只实现一个固定粗模块需要的身份、冻结参数与资产引用，不预建DAG或通用SDK。AssetRef v1不变，区分worker候选文件与宿主导入后注册资产，不能假装候选已提交。
- wb_tool.api提供固定WB模块描述与执行适配，内部调用原analyze_annotations；只接受本次准入的旧策略。实现摘要按实际代码确定，环境版本与参数/输入摘要绑定。静态worker路由，不接受用户模块导入字符串。
- 新对照worker用同一冻结原图/标注真实执行旧调用与新模块调用，生成measurements.csv、非空differences.csv、run-manifest.json及必要机器结果；不复制旧表伪造。只写宿主分配的本次暂存目录；事件不代替真实退出。
- 宿主根据冻结ModuleSpec/请求校验候选身份、必需输出、路径/摘要/大小和失败状态，在存储线程导入成果后再经Workspace.commit_result提交最终manifest。资产导入与结果CAS不是整体文件系统事务，失败/取消保留孤儿/诊断但不宣称成功。旧RunSession默认路径保持。
- 相同会话控制器由无GUI入口和既有WebEngine薄对照页调用；按钮进入“打开验收样例→运行→差异→打开成果→重开”。保持现有绿/青柠/Noto控件与导航，无另一套应用。耗时文件/解析/导出在后台，源修订/关闭/取消防迟到结果覆盖。

## 必须证明的反例与交付

原请求/位深/坐标/方法不变；显示图、未知dtype、错摘要/模块版本被拒；局部invalid/null与质量待复核不冒充valid0。候选manifest已发但进程非零、必需文件缺失/篡改、路径越界、取消与提交竞争均不成功。关闭重开能读正式成果，旧历史schema继续可读。安装独立wheel运行同一headless用例；契约/worker/存储/GUI及反向依赖、现有门禁与准确提交独审通过。中文操作单5–10分钟，用户未实际验收及科学/目标机缺口独立标记。

上述是实现前边界，若实际代码证明更窄复用能满足同一验收，可在P002证据解释；不得因测试方便缩减真实worker、Workspace持久化、三个产物或薄GUI要求。
