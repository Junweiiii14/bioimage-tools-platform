# Handoff Snapshot

- 更新2026-10-14；用户授权持续开发至WB自动化软件完成，Goal active，无token预算。完整软件未完成，阶段测试不能标整体完成。
- 活动分支feat/T-018-project-result-archive，产品c5f5787，base ba8a678；最后HEAD见git。任务状态唯一来源work/tasks：T-018 review待独审，T-019 ready。当前无运行中测试/工具进程。未推送、PR、main集成或发布。
- 用户明确忽略CLX；TIFF设备原图/TIF裁剪，_0/_1语义未知，不猜定量源。归一化偏好问题未回答，不推断样本/参照。材料只作证据，未改用户资料。
- wb-tool0.16.0 / app0.11.0：T-018源/OCR/归一化CSV与XLSX共用表构建器，CSV所有数据文本前置可逆text:，数字/真实0/None保持。CSV后缀入口/按钮已接桌面；无第三方版本或科学公式/schema变更。
- 统一ZIP新增archive.json v2：原图/字体/OCR源、原值裁剪、PNG与旧manifest、精确project.json、各CSV/XLSX、原始已核验请求/结果、声明run记录、每成员SHA/大小/角色/缺项原因。索引自身无自引用SHA，但计入4096成员/2GiB预算；单成员512MiB，结果累计64MiB、每表20万格。低层API ArchiveRunEvidence是宿主证据，非本机执行收据。
- 宿主ProjectArchiveSession精确保存后通过存储逐个核对完整run/资产路径；WB后台重读严格请求/结果，坏run单独unavailable，其他行保持。即使旧缓存曾显示有效值，损坏资产也不能导出旧数值。取消/关闭/代际变化撤销待发布输出；完成发布先于取消时保留文件。正式拼图仍需全部行审核。
- 最终dev.py check --all退出0：364测试113.15秒、Ruff235文件、Pyright0、9合约、4wheel/5隔离场景。新增25核心/4Qt并扩展真实完整PNG OCR重开归档；35定向2.07秒、27Qt/项目41.93秒。首轮全门禁363通过115.73秒，随后补索引预算反例并重新完整验证。最终日志.local/requirements-review/T018-check-all.txt，证据work/evidence/T-018/validation.md。
- 中间8核心失败因新测试夹具误用OCR绑定API与pairs字段，已修正测试，未改旧预期/容差/skip。类型/格式问题已修；本轮两次完整门禁通过。旧Qt Aborted及T-017约72项停滞的根因仍UNKNOWN，不能由本轮通过称已修复。启用PYTHONUNBUFFERED及faulthandler_timeout=20仅打印栈，无测试标准放宽。
- T-017只读元信息/严格匹配/显式选行原子应用/共同参数/文件名字面分段/128边缩略图已保留；元信息导入来源审计不持久化。实际用户表50×49/190公式、47未绑定/0应用及2原图缩略图的旧只读证据见T-017；本轮未重新做真实实验准确率/外部Excel/DPI/FAT/大项目性能。
- 下一步T-019-project-archive-restore.md：先读wb-project-archive-v2与实际导出/存储/项目契约，冻结有界ZIP检查、恢复到新工作区、历史证据和本机run区分方案，建立分支/context后实施。不得extractall/覆盖旧工作区/伪造PID/退出/成功，也不能静默丢弃旧结果。现ZIP不是完整数据库或全部编辑历史；跨工作区迁移需明确缺失历史来源的状态。
- 其他首版缺项见work/wb-acceptance.md：直接TIFF成图、模板精修/横向分段、缩放句柄、旧工具实际衔接、真实标注/用户工作流、大项目性能、独审/远程CI/最终Windows包/DPI/干净机/物理FAT。当前版本/通过测试不等于软件完成。
- 不恢复归档agent-workflow/lab-workbench，不自启子代理，不调用用户Esc停止的原生CUA。pytest-qt不是包态/人工准确率验收；原始图、已提交结果与数值预期保持。
