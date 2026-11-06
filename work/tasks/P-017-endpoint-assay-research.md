# P-017 明确孔板终点实验与成熟方法研究

<!-- PROGRAM_TASK_META {"id":"P-017","status":"in_progress","work_package":"W07","depends_on":["P-013","P-016"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex endpoint assay research","base_commit":"6bd4680530dc4697f8d394a96fd288723222ddb8","head_commit":null} -->

## 授权与范围

2026-11-06上游依用户持续推进及每实验新窗口要求派发本研究；goal已创建，无token预算。上游已明确释放共享树，核实ac10a07收尾与干净状态，保留全部收据随本任务集成。仅操作bioimage-plan-sync，不触碰旧dirty树、原图、历史或安装。必要PR/独审/检查/回传已授权；不外联、不花费、不上传私有数据。

## 完成条件

1. 在P013资料基础上比较CCK-8存活率与标准曲线蛋白定量，选一个明确assay和学生从仪器导出到结果表图的最小场景；公开来源与真实访谈/需求证据分开。
2. 先查官方方法和优质公开实现，固定版本/许可/依赖/支持接口；直接调用少量候选，在隔离研究环境验证，不先自写拟合或校正。
3. 寻找合理规模公开原始读数、板布局、空白/对照/重复及参考结果，核许可。报告逐孔和样本级结果、失败及质量异常；工程复现不冒充独立科学真值。
4. 给主选及改变选择的条件、平台公开接口复用与具体缺口、下一最小实现范围/验收。不得扩为万能孔板或统计平台。
5. 研究材料准确提交独审、适当检查与正常PR必需CI集成，更新handoff及回传上游。产品/正式依赖不变；旧科学/学生/环境缺项保留。

## 当前状态

已恢复资料并查重无P017；已建codex/p017-endpoint-assay-research。合并已验P016 main产生squash历史交接冲突；已核16d32b1与origin/main树无差异，按ac10a07保存全部较新收尾，先加载规则再解决。
