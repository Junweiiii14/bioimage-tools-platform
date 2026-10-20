# T-054：E1清单生成不可变执行计划

- 状态：done（E1纯派生计划；后续执行阶段另计）；依赖E0/T053独审无阻断。
- base commit：631b059；产品base65ff278。
- 授权：用户批准E0–E7连续实施，不逐步询问，不设定时任务。
- 范围：tools/wb/src/wb_tool/application、wb_tool/api.py、tools/wb/tests、tooling/installed_wheels.py、docs/contracts与README、work任务/证据、.agent-handoff。
- 必读：根规则、包README、wb-instrument-intake-v1、wb-development-plan-v2与E0基线。
- 目标：已确认schema10清单→稳定行/槽位ID、受限相对输出路径、布局位置、待计算空值表格。纯派生计划，不读磁盘/运行OCR/建目录，不在schema10夹带ROI或测量。
- 接口：build_intake_execution_plan(project, expected_digest=...)返回不可变IntakeExecutionPlan，计划版本intake_execution@1；输入摘要过期/未确认拒绝，加载项目仍用原schema10并可重新构建计划。
- 验收：同名/特殊标签路径安全、跨Fig/跨行槽位独立、重命名不改变身份或几何键、重排只改布局、N/来源变更让相关键失效、保存重开相同计划、revision不伪造重算、所有数值None/pending；相关/性质/完整检查与wheel、提交独审。
- schema/算法/依赖/门禁：无格式或数值算法变更；新增派生策略版本；扩展已有wheel用例，不削弱旧断言。
- 回滚：撤销新API及调用者增量，不改输入/历史文档。
- 独审：independent_review绑定7d7eedb..f975809，无阻断；独立7项2.68s及无I/O/最大容量/重排探针通过。

## 最终验证

- 产品f975809：完整dev.py check --all退出0，808 passed/554.07s，9导入契约及全部隔离wheel/真实OCR通过；格式/类型/边界通过。见work/evidence/T-054。
- 未改schema10、旧格式、积分算法/默认值、依赖锁或门禁。新工作流执行/安装包/科学留出未冒充本阶段通过。
- 下一阶段E2/T055：版本化阶段状态及宿主调度；开始前按新范围加载规则。
