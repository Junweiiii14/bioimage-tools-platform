# R09 基准工具非 GUI 自验

2026-10-28；新增工具基于 `ad12225d95a1dd7bffbf53e989ab7c1ce267b34c`，本记录对应尚未提交的 R09 差异。提交绑定、独审与实际 GUI 测量由 root 在 R03/R05 桥接冻结后安排。未改产品、共享 task/config/规则回执，未启动 QApplication 或 WebEngine。

环境：Windows 本机，仓库锁定 uv/Python 3.12.14；所有命令从活动 worktree 显式运行。实际性能预算及限制见 [冻结方案](r09-benchmark-plan.md)。

| 检查 | 结果 |
| --- | --- |
| `uv run --locked --no-sync python -m tooling.benchmark_workbench_snapshot --validate-fixtures` | exit 0；rows/intake 两类的小规模 4×6 与上界 512×96 全部经公共模型验证；上界各 49,152 个 pending 状态项 |
| `uv run --locked --no-sync ruff check tooling/benchmark_workbench_snapshot.py` | exit 0 |
| `uv run --locked --no-sync ruff format tooling/benchmark_workbench_snapshot.py` | exit 0；最终无需改动 |
| `uv run --locked --no-sync pyright tooling/benchmark_workbench_snapshot.py` | exit 0；0 errors/warnings |
| 非 GUI 负例探针 | exit 0；513 行/97 泳道拒绝；空样本/NaN/负耗时拒绝；1..30 的 nearest-rank p95=29；Windows 当前进程 PSAPI 数值为正且 peak working set≥current；确认未导入 QtWidgets |
| `node --check` 经 stdin 检查 CLICK_DRIVER | exit 0；只检查 JS 语法 |
| 默认 CLI 输出 JSON | exit 0；四场景、`performance_measured=false`，没有触发测量 |
| `git diff --check` | exit 0；不代表其他并行差异已由本作者复核 |

首次 Ruff/Pyright 报出的长行、闭包捕获、QApplication 类型、可空输入目标及 protected cache 访问已修正；最后检查如上，无 ignore/skip/阈值放宽。冷缓存改为基准中的临时 `patch.object`，保留真实 snapshot 实现与原缓存，未改产品。

**尚未验证**：真实页面点击驱动、正常 GUI 关闭、冷/热/idle 实测、状态字节与内存/预算对比。此时只能认定非 GUI 工具准备通过，不能将性能条件项或 R09 整项标为完成。若真实 GUI 暴露工具问题，应修正工具并保存原失败，随后在新的准确提交上测量；不得把驱动失败改记为产品性能超线。

## 独立预审失败与完成判据修复

2026-10-28，root 转交非作者预审：旧 CLICK_DRIVER 只比较 projectId/revision/rowcount，生产处理器未运行也可能通过。该旧工具仍未提交，复现时 HEAD 为 `45106f99e7d684fc1fb4b961afe642dfdc948b32`；旧工具完整文件 SHA256 为 `c651bc4647faffd4d4a844738d18b35d1872cb599526cb3a37559660547c9e3`。这个预审意见有效，前述语法/类型/夹具检查没有证明点击完成判据。

先增加 `tests/test_workbench_snapshot_benchmark.py` 的非 GUI Node VM 行为反例，再运行旧驱动：

```text
uv run --locked --no-sync pytest tests/test_workbench_snapshot_benchmark.py -q --tb=short
exit 1: 8 failed, 1 passed in 2.22s
```

原反例观察：没有生产 handler 时 `productionRenderCalls=0` 仍有 1 样本；只改 state 不 render 也有 1；render 抛错后仍加样本；旧/错误 nonce 被接受；重复回执或绘制前被旧状态覆盖产生 2 个样本；第二次点击收到第一次回执仍增加样本。正常流程 1 个对照通过。这些是基准工具错误，**不是产品性能故障**，也没有真实 GUI 测量可供作废。

修复只在基准工具中进行：标记 refresh 请求的唯一 nonce 仅在真实 request/publish 所调用的真实 snapshot 中附加；JS 实际 render 成功返回才记序号/nonce，双帧完成前再次校验；旧/缺失/错误回执、未 render、抛错、重复及迟到情况不能计为新的成功。snapshot 方法在返回或异常时恢复，非标记请求仍沿原验证，构造/JSON/idle 数据不含此包装。没有更改产品方法实现、CI 门槛或科学结果。

修后最后检查：

| 检查 | 结果 |
| --- | --- |
| 同一 9 个驱动用例 | exit 0；9 passed，修复前 8 红转绿 |
| 扩充至 16 项：缺 nonce、原请求参数原样转交、原 snapshot 确被执行、源字典不变、正常/异常恢复、非标记/其他动作/非法 payload 保留产品验证 | exit 0；16 passed in 2.17s |
| Ruff check / format（工具+新增测试） | exit 0 |
| Pyright strict（工具+新增测试） | exit 0；0 errors/warnings |

Node VM 只测试驱动逻辑与受控生产回调替身，不是 WebEngine、Qt slot 派发或肉眼呈现验收。仍须后续独审及无并行 GUI 的真实测量；本次没有启动窗口，也没有改变原预算以促成通过。全部 R05/发行并行差异均不在此次修改/复核范围。
