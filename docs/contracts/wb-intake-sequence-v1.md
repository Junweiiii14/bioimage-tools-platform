# Fig顺序草稿与整批执行 v1

T071按已批准方案增加IntakeGrouping@2/IntakeManifest@4及intake_workflow@3。旧grouping@1、manifest1–3、workflow@1/@2的wire shape和摘要保持；旧项目不因打开而自动重排或升级调度。原项目schema10–14及定量算法保持，不修改原图或历史结果。

顺序草稿由唯一figures列表（稳定Fig身份、标签、唯一N）和sequence蛋白条目（稳定entry_id、figure_id、单行label）编辑。按Fig列表和组内条目顺序展平非空名称，与完整groups列表顺序一一对应。groups的figure_id/protein_label为受校验投影，禁止独立改写；原group_id/来源成员/selected_source_id保持在采集组上。空名不占组，多于组数的蛋白条目可保存但不能执行；标签中逗号/斜杠不拆分，重复蛋白名不合并。

组剩余时，excluded_group_ids明确保存此次不处理的未分配组身份；选源的未分配组不能被默默排除。新增组不自动继承排除确认。所有已配置Fig必须有名称、1–96整数N及至少一个非空蛋白条目；所有匹配组须手选组内原图，额外条目必须有组。完整性、引用唯一性和原有参考/失败来源/复用约束仍在后端核验。

configure_intake_sequence纯用例重建确定性投影；save_intake_grouping沿用CAS与来源/位深/历史规则。N、移Fig、来源和区域变化按已有失效矩阵处理；标签变化不充当新来源身份。旧采集组可显式转换，转换预览不写历史。

workflow@3采用整批阶段屏障：所有crop done后才能claim任一compose；所有compose done后才能claim任一measure，最后export。任何needs_review/failed/cancelled/interrupted暂停整批claim，须明确修正/重试再继续。旧@1/@2保留就绪Fig优先语义。已完成且仍有效的其他Fig证据在局部修正后保留，不能因当前阶段屏障而倒判历史done无效；屏障作用于新claim/running。

单一启动对精确提交草稿串行保存、校验确认、准备@3账本和启动真实会话；任何一步取消、CAS失败、会话/代际变化即停止，不把草稿后继安装为成功。输出新目录在执行前明确。真实持久快照与当前活动阶段驱动页面导航；人工编辑/复核时不被后台进度抢走。旧账本恢复不自动续跑或静默变策略。
