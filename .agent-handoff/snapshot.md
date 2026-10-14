# Handoff Snapshot

- 更新2026-10-14；用户授权持续开发至WB自动化软件完成，Goal active，无token预算。整体软件未完成，阶段测试不能标整体完成。
- 活动分支feat/T-019-project-archive-restore，base f79b7b3；产品6a06369，最终HEAD见git。任务状态唯一来源work/tasks：T-019 review待独审，T-020 ready。当前无运行中测试/工具进程，未推送/PR/main集成/发布。
- 用户明确忽略CLX；TIFF设备原图/TIF裁剪，_0/_1语义未知，不猜定量源。归一化偏好问题未回答，不推断样本/参照。材料只作证据，本轮未修改用户资料。
- wb-tool0.17.0/app0.12.0/platform-runtime0.2.0：T-019有界ZIP普通/ZIP64检查、生成内部暂存路径、CRC/SHA/大小/成员集合/角色、原请求结果/OCR副本/CSV/OOXML重建及原通道裁剪/显示像素核对；不extractall、不执行成员。
- 新schema6/WBRestoredProject保留原ZIP/archive_sources和历史imported_runs，本机AssetRef重映射，原RunRecord内部声明保持。v1–v5继续读；当前运行结果须重读核验并标为历史，本机数据库不登记外来run/PID/退出收据。真实重新计算沿RunSession，新run成为本机运行；旧历史保留，二次归档/恢复保留链。
- 通用Workspace.import_draft_snapshot只允许无文档/run的新工作区，保留一个外来修订、不补造旧草稿；普通save_draft首修订0/+1 CAS不变，DB/文件格式仍v1。专用恢复线程创建自有临时工作区，关SQLite后Windows无覆盖目录rename，实际线程退出后通知GUI；关闭不打开晚到项目。POSIX标记发布未在实际目标环境验证。
- 398全量124.27秒、Ruff244文件、Pyright0、9合约、4wheel/5隔离场景退出0；此前396全量128.27秒通过，补DOS目录/强加密标志反例后完整重验。首批13核心3.41秒、19核心/Qt7.61秒、70核心/Qt/存储17.92秒。首次全门禁仅Ruff行长失败已修，没有削弱旧测试/容差/skip；类型告警均实修。最终日志.local/requirements-review/T019-check-all.txt，证据work/evidence/T-019/validation.md。
- 真实Qt/本机worker闭环：恢复后4000/空/0/8000/16000/0和OCR表保持；改基线旧值为空，真实复算2500，其他历史8000保持。首次恢复runs空，复算仅1条真实本机run；二次恢复2归档来源/4历史。8/16位/RGB/MINISWHITE、旧无索引、坏表/源/结果/CRC/路径、取消/关闭/无覆盖/发布失败/发布后关闭已测。截图T019-restored.png已看，源样例为受控合成，未新增真实科学准确率结论。
- 预算：4096成员/2GiB解压总计、原ZIP容器额外8MiB、中央目录4MiB；普通成员512MiB，历史ZIP可大于512MiB但仍受总预算；JSON16MiB/PNG与单表64MiB/TIFF解码512MiB及3200万像素/历史8代。源及旧格式超过恢复预算明确失败；大项目性能/FAT/断电未验收。单条本地历史资产损坏不影响其他值，完整再次ZIP不伪装缺失资产。
- 下一步T-020-direct-figure-image.md：直接TIFF/PNG成图，先冻结8位显示拼图/原16位定量来源的边界，读现有渲染/裁剪/OCR及官方TIFF资料，建立分支/context再实施；复用完整渲染与内嵌来源，精确保存后后台/取消/无覆盖，做直接TIFF到OCR往返。不要重新做T-019。
- 其他首版缺项见work/wb-acceptance.md：精确实验室模板/横向分段/模板库、缩放句柄、旧工具实际衔接、真实标注/使用工作流、大项目性能、独审/远程CI/最终Windows包/DPI/干净机/FAT/签名许可证。首版OCR仍必需；归一化实验配对不替用户决定。
- 旧Qt Aborted与T-017约72项停滞根因UNKNOWN。本轮两次全量通过，日志中段进度暂留后正常完成，无确认的新停滞；不能因此声称旧问题已修。PYTHONUNBUFFERED/faulthandler_timeout=20仅诊断。
- 不恢复归档agent-workflow/lab-workbench，不自启子代理，不调用用户Esc停止的原生CUA；pytest-qt截图不是包态/人工准确率验收。私有材料、模型和探针只在忽略.local，未改用户资料。独审必须绑定最终产品提交，作者验证不替代独审。
