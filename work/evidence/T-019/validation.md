# T-019 ZIP恢复验证

日期2026-10-14；分支feat/T-019-project-archive-restore，起点f79b7b3。作者自验，不等于独立审查。产品提交ID在阶段收尾后记录；整体WB软件尚未完成，Goal active。

## 实现与边界

- wb-tool0.17.0 / app0.12.0 / platform-runtime0.2.0；第三方依赖锁版本未改，uv.lock只改这3个本地包版本。
- 项目schema6保留原项目/行/lane/band/run身份与原修订、归档来源和复制历史资产；v1–v5继续读取。外来RunRecord不登记本机数据库runs/PID/退出收据；真正重新计算仍走RunSession。
- ZIP预检中央目录/普通及标准ZIP64、成员/压缩/路径/链接/预算，流式复制原ZIP和生成内部文件名；核对CRC/SHA/大小/成员集合/角色、项目/原始请求结果/OCR副本、CSV和OOXML实际内容，重建原通道裁剪/显示记录与像素。无extractall、无执行归档文件。
- 宿主专用线程导入新工作区，显式初始快照导入保留外来修订，不补造旧草稿；普通保存仍从0开始/+1 CAS。关闭SQLite后Windows无覆盖目录rename，实际线程退出后通知。关闭/取消/晚到结果有明确状态，已有目标保持。
- 历史结果与本机运行在结果表、持久来源提示及schema6 CSV/XLSX中区分。重开损坏的一条历史结果为空，其他结果保持；新计算保持旧历史记录，再次ZIP导出/恢复保留来源链。
- 容量/格式范围见wb-project-restore-v1.md：8代历史、4096成员、2GiB解压总计、普通成员512MiB、TIFF解码512MiB/3200万像素、PNG/单表64MiB、JSON16MiB。大项目/旧软件归档不保证支持；原ZIP历史不递归解包，超预算明确失败。

## 命令与结果

| 命令 | 结果 |
|---|---|
| dev.py context --task T-019，WB/app/platform-runtime/tests/tooling/docs/work/handoff/lock范围 | 已记录rules-context.json；module-map更新后重载并读取 |
| pytest tools/wb/tests/test_archive_restore.py -q | 首批13通过，3.41秒；未修改原数值预期 |
| pytest tests/test_archive_restore_ui.py tools/wb/tests/test_archive_restore.py -q | 19通过，7.61秒，含真实WB重算/两次恢复 |
| pytest tests/test_archive_restore_ui.py tools/wb/tests/test_archive_restore.py tests/test_workspace.py -q | 70通过，17.92秒；存储普通CAS/快照、损坏/取消/发布失败/发布后关闭、8/16位/RGB/MINISWHITE |
| 首次dev.py check --all | Ruff行长未通过，未进入pytest；已修正安装烟测脚本行长，无放宽门禁 |
| 完整dev.py check --all（成员标志补充前） | 退出0；396测试128.27秒，Ruff243文件，Pyright0，9合约，4wheel/5隔离场景 |
| 最终dev.py check --all | 退出0；398测试124.27秒，Ruff244文件，Pyright0，9合约，4wheel/5隔离场景；补充DOS目录/强加密位反例后完整复验 |

最终全门禁日志.local/requirements-review/T019-check-all.txt；上次完整日志T019-check-all-before-member-flags.txt。PYTHONUNBUFFERED=1及PYTEST_ADDOPTS='-o faulthandler_timeout=20'仅启用输出/栈诊断，不改变数值、预期、超时通过标准或skip。中途观察进度停留，进程继续完成；本轮没有确认的新停滞，旧Qt Aborted与T-017停滞根因仍UNKNOWN。

## 实际检查

原冻结期望4000/空值/真实0/8000/16000/0保持；修改基线后旧值为空、真实新worker结果2500，其他历史8000保持。源/OCR同名蛋白两行身份独立，OCR结果重开可读，归一化配置/表通过重建比较。首次恢复无本机run，实际复算后仅1条真正succeeded/PID运行；二次恢复共2个归档来源/4条历史记录。

新增夹具用真实500×1000 TIFF承载受控OCR token，替代该新测试中的b'composite'占位；不修改旧科学期望或伪造真实识别准确率。实际离线OCR工作进程仍由原全量/隔离安装用例验证。所有测试为作者验证，没有独立审查者。

已通过QWidget.grab检查源码Qt恢复界面，截图.local/requirements-review/T019-restored.png（私有忽略）：历史来源提示、4000/空/0、来源列可见；随后将列中完整SHA移至提示，保留短来源标签。没有启动原生CUA，没有修改用户WB资料。没有新的真实实验准确率、外部Excel、物理FAT、非Windows逐项发布、断电或大项目性能结论。

未完成：绑定提交的独审、远程必需CI/PR/main集成、直接TIFF/PNG成图（T-020）、精确实验室模板/横向分段/模板库、缩放句柄、旧工具实际衔接、人工真值/工作流及最终Windows安装包/干净机/DPI/签名许可证验收。
