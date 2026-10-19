# T-005：WB 后台分析协议与真实进程

- 状态：review（实现与自验完成；独立审查尚未执行）
- base commit：45d0c5f
- 上位目标：T-003，持续开发 WB 软件。

## 范围与必读
允许 tools/wb、tests、tooling/installed_wheels.py、docs、work、.agent-handoff、.importlinter、pyproject.toml、uv.lock。
读取根规则、架构、WB README、manual-analysis/reference 契约。上轮已提交分析用例，无源树未提交改动。

## 目标与不变量
严格序列化请求/结果 schema，固定 protocol@1、run/attempt/request 身份与序号；真实 worker 接收一个分析请求并返回结果候选，stdout 只用有界 UTF-8 NDJSON。
拒绝额外字段、非有限值、错误版本/身份/重复消息；保持来源摘要和 revision、失败/缺失/质量复核与真实零。
大图仅使用文件路径和摘要，不把原图数组放入消息。取消监听并在计算检查点合作退出；未知或被杀任务由后续宿主标 interrupted，不能假成功。
worker 不提交结果到数据库，不宣布宿主终态。结果封装可被工作区保存/恢复及 GUI 共用。

## 验收
严格 schema 正反例、来源/revision/标注一致性；真实子进程 TIFF→分析返回解析 signal 10；错误源/协议失败；取消不返回有效结果；stdout 可逐帧解析；安装 wheel 中可启动 worker。

## 验证/审查
2026-10-14：最终 dev.py check --all 退出 0，123 测试、Ruff/Pyright strict、4 导入合约和隔离 wheel。
33 个协议与真实进程测试含 strict 类型/字段、版本布尔值、NaN/Inf、身份/顺序、重复/旧结果、合作取消及错误取消身份。
生成并冻结 schema 快照，通过漂移检查；没有手写平行字段 schema 或放宽原语义。
worker 从源码及隔离安装 wheel 启动，解析 signal 10、revision 7 通过，错误源退出 2。
包 0.4.0 引用既有锁版本 Pydantic 2.14.1；无第三方版本升级，积分算法版本不变。
首轮测试调用的 raises 参数写错、默认 GBK 小修命令失败已修正；反例暴露 Literal 布尔值和 JSON before validator 的 tuple 模式问题，已按原字节 JSON 解析修复，未改预期/skip。
独立审查未执行。GUI、工作区事务及宿主强停在后续继续，不以协议 tests 宣称全部软件完成。
