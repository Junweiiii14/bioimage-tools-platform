# Handoff Snapshot

- 更新：2026-10-14；当前目标持续规划开发至 WB 自动化软件完成。
- 当前任务唯一状态源：`work/tasks/T-003-wb-product.md`，用户已明确扩展 WB 授权。
- 分支 `feat/T-003-wb-product`，起点 d83e4a0；继承 T-002 分支，PR #3 仍未合并。新任务未创建 PR。
- 已实现 WB 纯数值包 `tools/wb` / `wb_tool.api`；参考积分、闭区间、人工基线与失败类型。8 来源文件 SHA/本地快照冻结，原方案第 18-19 页核对。真实标注集尚未冻结。
- 完整质量检查 61 测试通过，2 import-linter 合约及正/负图，隔离 wheel 安装通过；证据 `work/evidence/T-003/validation.md`。
- 下一步：TIFF 输入、位深/极性、半开泳道 ROI 和原始剖面，再 worker/UI 手工闭环。可选用户问题：先自动候选还是首版也含 Fig/行名 OCR；等待异步回复，不阻止共用部分。
- 待完成：真实参考集、自动候选、归一化、保存恢复/导出、产品 GUI、产品包、绑定提交独立审查。当前只有核心，不可宣称软件完成。
- T-002 缺项保留：包态原生交互/ROI/DPI 与 GUI p95 未测；干净 Windows 按用户先前决定后续。技术包位置与历史证据见 T-002 文档，不重复编译技术探针。
- 原始 TIFF/PDF、旧 wbquant-improvements 未修改；不恢复归档项目。不启动其他工具。
