# T-004：WB 手工标注分析用例

- 状态：review（实现与自验完成；独立审查尚未执行）
- base commit：93a84bb
- 上位目标：T-003 持续开发至 WB 软件完成，当前阶段实现后台/界面共用分析入口。

## 范围与必读
允许 tools/wb、tests、docs、work、.agent-handoff、pyproject.toml、uv.lock、.importlinter、tooling/installed_wheels.py。
必读根规则、架构、代码规范、WB README/参考契约。实现 WB 自有 application，不创建无真实消费者的公共平台包。

## 输入输出与不变量
输入不可变泳道/条带标注、原始图像、SHA256 与草稿 revision。领域和 application 不导入 UI 或具体 I/O 适配器。
输出稳定身份、revision、算法版本、原始积分、有效状态、失败原因与质量提示。原图、草稿和已完成结果不修改。
未检出/排除/无效不伪装零；饱和区域不冒充可信信号；有效平坦区域可以为零。
取消应中断且不返回成功结果；源摘要不符拒绝分析；独立泳道错误保留明确失败状态。

## 验收
解析三点三角形信号 10；两泳道身份保留；空白/缺标注/排除/无效窗口有独立状态；位深上下限质量提示；源摘要不符失败；取消无成功结果；输入对象不变。

## 验证与审查
2026-10-14：pytest tools/wb/tests/test_analysis.py -q 退出 0，12 个解析/状态/取消用例。
dev.py check --all 退出 0：90 测试、Ruff、Pyright strict、4 import-linter 合约、隔离 wheel。
隔离产物在独立 venv 中执行 TIFF 写入/读取到手工分析，信号 10 和 revision 7 均通过。
新增 application 禁止 GUI/具体适配器合约及传递负例，原图/数值语义和测试预期未削弱。
wb-tool 0.3.0 新增 API；profile_integral@1 不变，quality_policy dtype_limits_review@1 与 schema_version 1 明确记录。
依赖没有新增或升级；uv.lock 只更新本地包版本。独立审查未执行。
后台进程、工作区存储、GUI 本任务不宣称完成，后续继续实现。
