# Handoff Snapshot

- 更新2026-10-14；用户授权持续开发至WB自动化软件完成，Goal active，无token预算。阶段自验不能标整体完成。
- 活动分支feat/T-017-project-metadata-batch，产品9ea4089，base0c8fc3f；最后HEAD见git。T-017 review待独审，T-018 ready，任务文件是状态唯一来源。无后台测试进程；所有本轮任务已终止。未推送、PR、main集成或发布。
- 用户明确CLX忽略；TIFF设备原图/TIF裁剪，_0/_1语义未知，不猜定量源。归一化偏好问题未回答，不推断实际样本/参照。
- wb-tool0.15.0/app0.10.0：已含多源固定N定量、原曲线/明确边界基线、真实进程/自动项目表；离线OCR/原文/人工校正/明确原图绑定/XLSX、显式样本参照对照归一化；T-016接通PNG与完整生成图OCR，原图定量仍TIFF。
- T-017新增只读XLSX/UTF-8 CSV、表头/列/完整row_id/SHA/文件名匹配、重复/未匹配提示、可修改目标和值、显式勾选行/字段原子应用；共同参数与字面分段文件名。名称排序保留测量，N/空位撤回审核使旧值无效。v1–v5/schema/科学公式不变，原run/OCR/归一化保持。元信息表和规则当前仅在预览会话，不持久化导入来源审计。
- 原图列表后台128边缩略图，SHA缓存最多512源，重开按需加载；坏图继续/SHA去重。取消关闭沿用完成当前接受一张、停止后续的旧契约；代际变化拒绝附着旧原图。元信息解析取消/关闭/后到编辑保留旧表/草稿，修改导入设置清空旧预览。格式/预算详见wb-project-metadata-v1.md。
- 最终dev.py check --all退出0：335测试110.95秒、Ruff224文件、Pyright0、9合约、4wheel5隔离场景通过，新增31测试。最终启用PYTHONUNBUFFERED及faulthandler_timeout=20仅打印栈，无测试标准放宽。完整日志.local/requirements-review/T017-check-all.txt，证据work/evidence/T-017/validation.md。
- 首次全门禁1失败332通过：关闭导入回退丢当前接受行，已恢复旧行为，保留原预期，13桌面组合通过。第二次全门禁约72项后停滞约3分钟后停止；随后带线程诊断的145仓库测试98.74秒通过、无超时栈，根因UNKNOWN。新测试同步guard放入finally释放/超时ValueError，不把最终通过说成根因修复。旧Qt Aborted同样未定位，详见risks与T-017证据。
- 实际材料只读probe_metadata.py：用户Excel1表50×49/190公式，47提议0绑定0勾选；2原图/2缩略图，预览不改草稿，保存重开一致，Excel/TIFF源SHA不变。全包约59MB主要嵌图，仅解析所需XML（单16MiB/累计32MiB），不解码图像。报告/工作区/截图均ignored .local/requirements-review；T017-metadata.png和T017-user-metadata.png已看。未据订单/条数推断真实映射。
- 下一步T-018-project-result-archive.md：结果CSV与包含已核验结果/原始资产/OCR证据/归一化配置的统一归档导出。先恢复根/handoff/module-map/任务，读figure_export与各结果导出/存储契约，按实际scope建立分支/context记录后实施。统一ZIP导入需另行明确历史run来源与验证，不能伪造本机PID/退出/成功记录。
- 其他首版缺项见work/wb-acceptance.md：ZIP导入/迁移、直接TIFF成图、模板精修/横向分段、缩放句柄、旧工具实际衔接、真实标注/用户工作流、大项目性能、独审/远程CI/最终Windows包/DPI/干净机/物理FAT。当前版本/通过测试不等于软件完成。
- 不恢复归档agent-workflow/lab-workbench、不自启子代理、不调用用户Esc停止的原生CUA。pytest-qt/截图不等于包态/DPI/干净机验收；原始图、已提交结果、数值预期与容差保持。
