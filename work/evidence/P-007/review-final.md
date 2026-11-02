# P007准确候选独立审查

非作者/root/p002_independent_review，产品范围dc9618e7000eb7793067556e99d50a0d0509423d..6bb3168ad145a70d0851703826b4813057ae42e5：Accepted，无阻断。独立31tests passed/4.00秒、旧实现AST/28显式导出/23schema基线重算、六组计划攻击（重复节点/跨样本/错上游键/混合环境/额外参数/篡改输出类型）均拒绝。准确规则回执与diff0；首次独立脚本默认GBK失败，明确UTF-8后完整执行，不改产品/断言。未启动Qt、未跑完整门禁/wheel、未写文件。

最终准确范围dc9618e7000eb7793067556e99d50a0d0509423d..23d405645097fa07b7949522e020b75a7a4cd3cf：Accepted。6bb后只有9份证据/状态/交接，无Python变化；四冻结Git原件与原路径/大小/SHA一致，计划重编译与receipt摘要/节点键一致；v1 Git blob逐字节相同，实际wheel原日志SHA及所有通过行匹配；in_review/head6bb合法，plan checker/规则/diff0。

只接受P007契约/纯预检/保存重开，不证明真实图执行、实际磁盘载荷符合声明、环境准入或S1。P005仍须核验实际输入、当前环境、worker退出、提交与恢复。

## 首轮CI失败与显示修复后的审查

上述23d为首轮准确Accepted历史：Linux完整1596passed/4既有skip/613.11秒并通过wheel，Windows旧manual pan1failed/1599passed/929.22秒，实际失败，未合并。原证据ci-failure-r1.json保留；旧Accepted不覆盖后继UI代码。

非作者新准确完整范围dc9618e7000eb7793067556e99d50a0d0509423d..dc4cc24a0248396de711b1e7f820280cc23de157：**Accepted，无新增阻断**。

独立检查：普通/扣留初始布局的完整WebEngine流程exit0、2passed/17.23秒；实际同步函数与指针处理器12组不同offset/同新视图/延迟fit/取消组合均过（调度探针不替代真实Qt）。七份回归原件及CI完整日志SHA核验；准确规则、diff、plan checker、机械设计检测[]均0。源码在pointerdown抓取offset前同步视图原点，fitImage沿用同规则，同视图保留偏移、新视图保持重置策略；未改科学坐标/ROI/数值/超时或容差。

新分支增加覆盖，原40/25与5000ms保留；修前受控失败、修后通过，不把受控因果关系冒称历史CI完整定因。非作者未写文件、未跑全量。新最终状态记录后须准确增量复核及当前HEAD四必需CI，正常PR集成后才done。
