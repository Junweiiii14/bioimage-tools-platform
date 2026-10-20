# T-051：仪器目录与Fig清单分配闭环

- 状态：complete（本机源码与隔离wheel阶段）；日期2026-10-19。安装包及完整自动化后续阶段另计。
- 产品base：a23435471742b69adbc800bad0b1b8fe58872bd3；规划main合并43d520f49507f12995eb3220beab9fd78f4adda7。
- 用户授权：PR16必需检查通过后合并，按新规划实现仪器文件夹导入、Fig/蛋白/N录入与缩略图批量分配，保留独立灰度OCR。
- 已执行：PR16 head cdf4b7d四项必需SUCCESS，匹配head合并，远端state MERGED。
- 范围：当前WB领域/用例/适配/UI与桌面装配、相应测试/契约/README/设计surface/任务/交接。采用scope .覆盖规划合并及功能集成。
- 第一阶段闭环：仪器TIFF目录原名导入（不按命名推断曝光或蛋白）、可见缩略图，Fig及蛋白行/N清单，批量明确分配、确认与保存重开；来源不可覆盖；N含空位不含Marker，同Fig仅共享N，行槽位独立。
- 不在范围：自动定位/裁剪算法、自动拼图定量、表格填值、安装包重建/发布、依赖升级/OCR拆分；现有独立定量OCR保留。
- 验收：未知编号/重复蛋白/混合大小/坏图/未分配/缺图/批量分配歧义、取消/切换/保存失败/重开、schema兼容与显示不进入数值；相关及完整门禁、独立wheel、绑定提交独审；真实仪器准确率未验证明确保留。

## 2026-10-19 本轮中断时状态
- PR #16 已在四项必需检查通过后合并；merge 43d520f49507f12995eb3220beab9fd78f4adda7。
- 当前 HEAD ab8b033：已集成 schema10 清单核心、核心测试/契约和网页分配 UI。桌面宿主/bridge/真实存储集成测试仍为本树未提交修改；其他用户工作树未改。
- 子任务验证：18项核心/Qt与64项旧功能回归通过；核心树完整独立wheel含真实OCR通过。UI新增3项通过；旧会话取消草稿测试组合及单独失败，未修改断言。
- 主树定向 Pyright 0。首次真实桌面3项测试未通过（FEFEF）；新导入 preview_edge=192 超过 FigureView.install_thumbnail 的128上限，已修为128，修后未复测。测试随后在关闭阶段出现Windows原生异常0x80000003；不能认定全部由尺寸错误导致。被测进程56832/57216已结束。
- 未完成：修后定向复验、旧取消草稿失败诊断、完整门禁/集成wheel、绑定提交独审、界面finish review/documenter、宿主提交与最终交付。未制作/替换安装包，独立灰度OCR未移除。
- 恢复从本树继续，优先运行 pytest tests/test_instrument_intake_desktop.py -x -q，避免并行多个Qt测试。子任务截图和日志位于 t051-intake-ui/.impeccable/review 与 .local/t051-ui/validation.md；核心wheel日志位于 t051-intake-core/work/evidence/T-051/core-wheels.txt。

## 2026-10-19 继续修复
- 用户要求缩略图与Qt退出排查、完整门禁及独立审查完成后汇报。
- 产品65ff278：128边预览并在资产导入前拒绝异常预览；取消期旧position心跳不可清除草稿。修后12项相关通过。
- 独审9a0c465发现4项P2：名称空格/逗号往返、跨根同名同SHA候选丢失、字体/OCR误读缩略图、已确认复用阻断无关分配。65ff278逐项修复，并保存追加导入。
- UI独审两项修复完成：误增未保存项可单独撤销，intake不调用旧CtrlZ；原审查者对65ff278两项评分均resolved、ship仅在该评分范围。
- 最新24项真实Qt/WebEngine/View/会话通过16.60s；全项目Pyright0。65ff278最终全门禁含Windows异常观察执行中。原生Qt历史根因仍不作全部解决结论。
- 当前源码没有新依赖、算法或门禁规则变更；版本10是本阶段新持久化清单，旧1–9保持。

## 最终验收
- 产品 `65ff278f4d11bbd089cd9df28aabaa3359b04958`：完整dev.py check --all外层0，801 passed / 549.84s，原pytest子进程0 / 0x00000000；9导入契约、格式/类型/边界与所有隔离wheel完成。
- Windows native observer实际附加PID52244，无新NATIVE_EXCEPTION；已知测试进程退出。历史Qt6WebEngineCore.dll 0x80000003精确根因仍UNKNOWN，未将通过复测写成历史根因已完全解决。
- 真实隔离OCR/worker/PNG及桌面异步关闭通过；doctor、smoke-env、当前启动器verify-launch均0。
- 独立代码增量审查绑定65ff278，四项P2均关闭；UI verdict两项resolved/ship仅限修复评分；documenter No changes。
- 记录：work/evidence/T-051/validation.md、independent-review.md、visual-review.md、final-exit-observation.json；原始失败/中止/最终长日志保留.local/t051-logs。
- 尚未执行安装包重建/替换或发布、main产品集成；真实仪器留出、干净Windows、DPI及后续自动裁剪/拼图/定量仍不属于本阶段通过结论。
