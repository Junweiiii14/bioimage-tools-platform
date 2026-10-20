# E0–E7需求与验收索引

依据[执行计划](wb-execution-plan.md)。当前任务状态只在[T-060](../work/tasks/T-060-integration-installation-acceptance.md)维护；本表区分已验证的工程行为与尚缺外部条件的验收，不代表正式发布。

| 阶段 | 落地行为 | 提交与证据 | 当前边界 |
|---|---|---|---|
| E0 | 核对有效入口、四产品包、依赖、远端缺口与基准 | T-053，[基线](execution-baseline.md)、[验证](../work/evidence/T-053/validation.md)、[独审](../work/evidence/T-053/independent-review.md) | 历史工作树/原安装保留 |
| E1 | 确认清单生成稳定Fig/蛋白行/槽位计划；失效与空表状态明确，规划不调用OCR | f975809，[验证](../work/evidence/T-054/validation.md)、[独审](../work/evidence/T-054/independent-review.md) | 基于schema10纯派生；同名/重排/来源与N变化不以显示位置串值 |
| E2 | 持久化阶段票据、串行调度、异常定位与取消；坏Fig不阻塞其他就绪Fig | b4b519f，[验证](../work/evidence/T-055/validation.md)、[独审](../work/evidence/T-055/independent-review.md) | schema11；首次全量purecall保留UNKNOWN，后继通过不抹记录 |
| E3 | 固定N槽位、原坐标/来源/复核证据、原值TIFF；缺弱信号进入待复核 | 32da9f4，[验证](../work/evidence/T-056/validation.md)、[独审](../work/evidence/T-056/independent-review.md) | schema12；合成精确像素通过，独立真实定位真值未验 |
| E4 | 完整Fig提交后才启动原像素定量；布局占位与分析输入分离 | ff89867，[验证](../work/evidence/T-057/validation.md)、[独审](../work/evidence/T-057/independent-review.md) | schema13；显示变换不进入原值计算 |
| E5 | 按稳定身份填表；原值/显示/表格/来源/归档输出新目录；导入历史后可恢复输出 | 8feffce，[验证](../work/evidence/T-058/validation.md)、[独审](../work/evidence/T-058/independent-review.md) | schema14；缺失/失败不伪零，半成品重跑而非虚构算法断点 |
| E6 | 冻结渲染复用、阶段列表分页与焦点稳定、所属资源关闭；保留独立灰度/OCR/手工入口 | ea7ed55，[性能](../work/evidence/T-059/performance-comparison.md)、[验证](../work/evidence/T-059/validation.md)、[独审](../work/evidence/T-059/independent-review.md) | 20次新进程/模式，旧导出p50改善28.91%，清单17.78%；不是科学准确率或真实批次承诺 |
| E7 | 高风险OCR/CAS、会话身份及关闭修复；依赖PR逐批集成；独立E7离线包双流程和生命周期 | [OCR](../work/evidence/T-060/ocr-validation.md)、[裁剪](../work/evidence/T-060/crop-identity.md)、[定量会话](../work/evidence/T-060/quant-session-identity.md)、[包态](../work/evidence/T-060/package-validation.md)、[最终集成](../work/evidence/T-060/final-integration.md) | PR17最终3680790绑定独审/两平台910项及四必需检查通过，main0f358ac；本机Win11安装工程通过，科学/干净目标机/DPI未验 |

## 兼容与证据口径

- 原始输入和历史结果不覆盖。schema1–13按原语义读取，新增状态不将缺失/失败转换成数值0。显示数组、预览旋转/对比度不替代原坐标和原像素。
- 独立灰度、OCR、模板、历史读取与手工定量保留正式入口；同项目新会话同样必须拒绝旧手势和旧任务，不能只检查项目ID。
- 产品0c927f5全量900项/691.23s及全部隔离wheel/check退出0。e57949b随后仅修诊断caller的当前epoch，真实CLI3项/15.29s及静态/类型、非作者审查通过；900不冒充e579重新全量。
- 后继8e11028完整910项/705.48s、原pytest0/u32=0、全部隔离wheel/真实OCR/check0；产品运行文件仍等同e579。测试修复及该提交非作者独审见T060 fullcheck-diagnostics，旧908/1fail与909/1fail仍保留；这不代替最终主线服务器检查。
- 最终产品3680790在actualbase842918a绑定独审/13历史来源规则校验通过；PR17的Windows910/666.50s、Linux910/353.99s及全部隔离wheel/真实OCR/check0、桌面与规则检查全通过，已精确合main0f358ac。包态运行文件仍等e579；文档收尾不改二进制。
- 旧原生purecall、历史超时与两次页面间歇失败继续保留原日志/原退出状态。后继绿色、进程清单变少均不等于旧根因已确认。

## 明确保留的验收缺口

| 项目 | 缺失条件 | 处理 |
|---|---|---|
| 科学真值 | 独立留出原图、逐槽人工标注、明确样本对应 | 不声称定位/灰度科学准确率；开发图与合成图只作工程回归 |
| 跨蛋白生物学映射 | 用户确认的配对/归一化关系 | 只接受显式映射，不按行号或外观猜测 |
| 干净目标Win10 | 当前没有可用目标机/VM | 本机Win11非管理员证据单列；最低1809限制不等于目标通过 |
| 物理DPI/输入 | 125/150/200%实际屏幕与物理交互；用户已停止原生CUA | 离屏真实DOM/worker测试不外推这些项目；不恢复被停止的原生控制 |
| 正式发布 | 外部验收及另行发布授权 | 仅交独立测试候选，保留原版和原有数据 |
