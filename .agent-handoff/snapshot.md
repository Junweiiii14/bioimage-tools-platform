# Handoff Snapshot

- 更新2026-10-14；用户授权持续开发至WB自动化软件完成，Goal active，无token预算。整体软件未完成，不以阶段测试标整体完成。
- 活动分支feat/T-020-direct-figure-image，base 3a38af6，产品待本轮提交；最终HEAD见git。任务状态唯一来源work/tasks：T-020 review待独审，T-021 ready。当前无运行中测试/工具进程，未推送/PR/main集成/发布。
- 用户明确忽略CLX；TIFF设备原图/TIF裁剪，_0/_1语义未知，不猜定量源。归一化偏好尚未回复，不推断实验配对。用户材料仅作证据，本轮没有修改原资料/执行附带程序。
- wb-tool0.18.0/app0.13.0/runtime0.2.0：新增export_figure_image与桌面直接TIFF/PNG按钮；沿现有完整render_figure，RGB8、16位整除257、原裁剪几何，无缩放/反相/自动增强；来源JSON和DPI一致。项目schema1–6、原值裁剪/积分/归一化不变。
- TIFF单页未压缩contig/INCH、ImageDescription ASCII JSON、Software=bioimage-wb figure_display@1；PNG仍wb_provenance。量化load_tiff拒绝已知显示Software或operation/purpose，load_ocr_image专用TIFF分支允许并提示；旧TIFF预处理ID不变。未知第三方或剥掉来源标签不能自动判源。
- 后台自有临时文件写入/关闭/fsync/重读完整像素与标签，再取消检查/无覆盖发布（Windows rename，POSIX link）。PNG64MiB/TIFF128MiB/来源16MiB，完整3200万像素/32768边长。源/字体额外核验声明字节数。直接图像不含完整原资产，恢复仍用ZIP。
- Qt先精确保存后导出；保存回调也检查取消/关闭，不让_start清掉旧取消后重启。渲染期间编辑/关闭/取消拒绝晚到发布，已发布文件保留；真实TIFF OCR明确关联原图后4000/缺失/0、归一化0.5与重开保持。
- 425全量143.71秒、Ruff251、Pyright0、9合约、4wheel/4个隔离环境退出0；27新增（18核心/9Qt），另28核心+原有1.21秒/9Qt17.48秒专项通过。锁仅2个本地包版本，无旧预期/容差/skip/ignore削弱；PNG新DPI容差0.013来自整数像素/米半步0.0127dpi。日志.local/requirements-review/T020-check-all.txt，证据work/evidence/T-020/validation.md。
- 真实00060322.tif（1347×902）全幅包装为1577×988 TIFF/PNG，仅格式几何测试；N=1非实验声明，未做定量。完整输出/来源与原画面显示像素相等、原SHA保持，真实OCR17token含包装文字，0确认/0绑定，4.07秒非基准。已看私有display.png和源码Qt T020-direct-image.png；不称准确率验收。
- T-019产品6a06369已有schema6归档历史/原ZIP/复制请求结果，外来run不登记本机PID或收据；Workspace.import_draft_snapshot只导入一个原修订，普通CAS不变。ZIP成员/CRC/SHA/表/像素重建、专用恢复线程/SQLite关闭后无覆盖发布、重开核验/编辑失效/真实重算和再次恢复均保留。完整限制见T-019契约/证据，不重做该阶段。
- 下一步T-021-laboratory-figure-layout.md：已只读查看样图00060263(1)/02360643(1)预览，存在同Fig并排段/不同高度/重复蛋白/列内纵向独立排列/字号差异。建新分支/context，先冻结新布局模型与旧v1–v6/ZIP渲染兼容；显式row_id/段来源与分界，禁止按同名猜配或拉伸补齐。可视化布局、模板保存/复用、TIFF/PNG/ZIP/OCR保持一致。
- 其他首版缺项见work/wb-acceptance.md：缩放句柄、旧灰度工具实际衔接、真实标注/效率/用户工作流、大项目性能、独审/CI/最终Windows包/DPI/干净机/FAT/签名许可证。OCR首版仍必需，T-021不替用户确定实验样本/参照。
- 旧Qt Aborted与T-017约72项停滞根因UNKNOWN；本轮全量正常完成，不因此声称已修。PYTHONUNBUFFERED/faulthandler_timeout=20仅诊断。不自启子代理、不恢复归档workflow、不调用被用户Esc停止的原生CUA。作者验证不是独审。
