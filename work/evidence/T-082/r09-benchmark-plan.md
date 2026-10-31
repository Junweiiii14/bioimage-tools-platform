# R09 快照基准：测量前冻结方案

2026-10-28，准备基线 `ad12225d95a1dd7bffbf53e989ab7c1ce267b34c`。本文件和 `tooling/benchmark_workbench_snapshot.py` 是测量工具与预设判定；当前 **尚未运行 GUI 性能基准**。实际性能证据必须绑定后续冻结提交。R05 仍可能改变桥接，等待 root 通知无并行 GUI/构建负载后执行；不会用当前工具自检代称 R09 已验。

## 问题和边界

现有 `WorkbenchBridge.publish()` 使用 presentation key 缓存，180 ms timer 不等于每次重建全量快照。要区分 PNG 缓存失效、热快照构造、JSON 编码、idle publish 和实际 WebEngine 往返显示。本工具只收集证据，不优化产品、不修改 CI 阈值、不安装依赖、不对真实工作区写入。

没有用户真实代表性实验项目，因此“小规模”是**有契约依据的设计样例**，不是统计意义上的典型用户分布；大规模是当前行数/来源数/泳道数边界的合成组合，不等同于所有 schema、最大文本/原图像素/历史次数同时取极值。无论结果如何，均不得宣布真实实验场景性能达标。

## 固定输入

| 用例 | 类型 | 行/来源数 | Fig 数 | 每行泳道 | 显示状态项 |
| --- | --- | --- | --- | --- | --- |
| rows-small | 行式项目 | 4 | 2 | 6 | 24 |
| rows-limit | 行式项目 | 512 | 128 | 96 | 49,152 |
| intake-small | 仪器清单 | 4 | 2 | 6 | 24 |
| intake-limit | 仪器清单 | 512 | 128 | 96 | 49,152 |

依据：`WBFigureProject.rows` 最大 512；`IntakeManifest` 的 sources/proteins/assignments 各最大 512；`FigureRow`/`IntakeFigure` 的 N 为 1..96，行式默认 6；`docs/contracts/wb-instrument-intake-v1.md` 的当前合同明确这些边界与 128 边长缩略图。既有 `installation_check_sequence.py` 采用两 Fig 工程诊断；小例扩为每 Fig 两个蛋白，用于覆盖组内与组间路径，不声称它来自用户样本。

模型全部通过公开 `wb_tool.api` / `tool_contracts.api` 构造验证，使用不同身份的合成 AssetRef；不写假 TIFF、不读取合成引用、不创建工作区、不生成测量值。固定种子 8209 产生 128×128 的显示专用噪声，故意避免纯色 PNG 过度压缩掩盖传输量。逻辑原图元信息为 1024×512/16 bit，仅供合法元数据投影；所有状态项都是 `pending_review`、value=None，没有伪造 run/已测量结果。输出保存模型 JSON SHA256、规模和缩略图尺寸以便重跑。

行式桥接不会自动把全部缩略图放进状态，仪器桥接会携带 source pool 的缩略图；这是当前真实实现差异，不能人为把缓存预填成同一载荷。未覆盖真实大图解码、保存、定量、完整成图及历史回放。

## 预设工程触发预算（测量前确定）

| 指标 | 触发调查的预算 | 依据与限制 |
| --- | --- | --- |
| 构造+JSON p95 | 50 ms | 参考浏览器长任务定义，保守用于同机 Qt 主线程同步区段；是工程触发线，不是科学标准 |
| 原生刷新点击至返回后 double-rAF p95 | 200 ms | 参考 web.dev INP 的良好交互线；本指标是合成诊断，不等于真实 INP 或屏幕物理呈现延迟 |
| idle publish p95 | 1 ms | 180 ms 轮询周期的约 0.56%，将空闲开销限制在很小比例；同时必须零 snapshot 调用、零 state emission |
| 状态 UTF-8 字节 | 16 MiB | 与宿主既有文档/读取消息量级保持保守对照，只触发载荷调查；不是 Qt WebChannel 硬限制 |
| host+本页 renderer private bytes | 2 GiB | 现有编码规则以 16 GB 主机单计算任务为起点，为单工作台先预留不超过约 1/8 的设计份额；不是 OS 限额或全进程树总量 |

官方依据：[长任务](https://web.dev/articles/optimize-long-tasks)、[INP](https://web.dev/articles/inp)、[Windows 内存字段](https://learn.microsoft.com/en-us/windows/win32/api/psapi/ns-psapi-process_memory_counters_ex)、[Qt WebEnginePage](https://doc.qt.io/qtforpython-6/PySide6/QtWebEngineCore/QWebEnginePage.html)，2026-10-28 读取。Web 来源只支持阈值语义与 API，不替代本项目性能测量。

超线后才按实际热点考虑索引、分页或资产引用；在同一输入、提交/环境可比的前提下比较前后，并保留身份与草稿正确性。合成上界超线不自动授权整体重写。若所有指标均未超线，只能对这组工程样例结论“未触发优化”。

## 采样与限制

- 每次进程仅运行一个用例，窗口 1440×940，真实 Windows Qt/WebEngine。默认每段预热 5 次、记录 30 次，原始样本全部保留；p95 为排序后第 `ceil(0.95*n)` 项，30 次即第 29 项，不插值、不删除异常值。有限样本不保证总体尾延迟；环境受扰时保留本次结果，说明原因后单独重跑。
- `snapshot()` 与紧接的生产同参数 `json.dumps(... ensure_ascii=False, allow_nan=False)` 分段以 perf_counter_ns 计时；UTF-8 字节换算在计时外。冷段仅临时清空 PNG 字典，**不代表冷启动/磁盘/模型冷缓存**；热段使用现有缓存。模型、Qt 控件和显示栅格预先装载。工具不改产品缓存框架。
- idle 段先 publish 一次，用 wraps 仅计数 snapshot 是否被实际调用，再测重复 publish；0 次不表示没有 key/progress 检查开销。为固定采样间隔，停止此窗口的 180 ms bridge 与 150 ms session 定时器，只由探针调用；生产定时器并发、后台运算与多窗口竞争不在本轮测量范围。
- 点击由 QTest 向 WebEngine 原生输入目标发出，要求 JS event.isTrusted。发货页面临时添加基准按钮，每次以 crypto.randomUUID 产生不同 nonce 放进 refresh payload。本工具仅为这个可弃窗口装配 WorkbenchBridge 子类：Qt request slot 转交真实 super().request，且仅在带有效 nonce 的该次 refresh 调用中临时包装真实 snapshot，使其附加同一个 `__r09Nonce` 字段；真实 request→publish→snapshot→JSON→stateChanged 路径全部执行。离开调用（含异常）即恢复原 snapshot；构造/JSON/idle 测量段均调用未添加 nonce 的原方法。此包装是基准 instrumentation，不修改产品源码或产品协议。
- JS 包装发货页面实际 render 函数，仅成功返回后增加 render 序号并绑定当时 state nonce。完成需要本次回执 nonce、已接受 state nonce、成功 render nonce 相同，且序号大于点击前序号；双 requestAnimationFrame 结束时再次确认状态仍对应本次点击。旧/缺失/错误 nonce 不计样本，同一回执最多排一次帧回调；无生产处理器、跳过 render、render 抛错或等待绘制期间被旧状态覆盖均不能产生成功样本。反例与原预审失败记录见 r09-tool-validation.md。
- 以 event.timeStamp 计点击至上述双帧边界的响应，同时记录 handler 起点耗时；仪器化请求的解析/nonce 附加/包装成本包含在点击数据内，不宣称零开销。它不代称已验证所有产品按钮、物理鼠标或肉眼显示；双 rAF 是下一次绘制机会的保守近似，不是像素呈现证明。
- 在实际 renderer 执行后读取小型结果，轮询往返不作为耗时终点。生产页面边界诊断、身份/行数/nonce不匹配、未成功 render、非原生点击或超时均使测量失败，不能把旧页面当响应成功。
- Windows PSAPI 只读取本进程和 `renderProcessPid()` 对应本页进程，记录当前 private commitment、working set、进程生命周期 peak working set；前后两个 private 样本不是全程 peak，也不含 Chromium GPU/utility 子进程。记录 CPU/OS/Python/Qt、Qt 环境变量、屏幕 DPI、viewport，实际运行记录另需写空闲环境与电源状态。
- QApplication 和窗口均由本工具拥有。结束前复用 `close_and_dispose_window` 正常 close/取消或放弃合成草稿/drain/deleteLater；不杀进程、不调用 terminate，不删除其他窗口。关闭失败不能写成功性能报告。

## 执行方式

非 GUI 校验：

```powershell
uv run --locked --no-sync python -m tooling.benchmark_workbench_snapshot --validate-fixtures
uv run --locked --no-sync python -m tooling.benchmark_workbench_snapshot
```

冻结源码和本工具为干净提交、确认没有并行测试/构建/GUI 后，各用例分别运行（输出必须是新文件）：

```powershell
$env:QT_QPA_PLATFORM = 'windows'
uv run --locked --no-sync python -m tooling.benchmark_workbench_snapshot --run --case rows-small --output .local/T082/r09/rows-small.json
```

其余依次改为 rows-limit、intake-small、intake-limit。不自动串行循环、改阈值或清理已有报告；报告成功写入前正常清理窗口。汇总时记录全部命令/退出码、最终提交、资源占用环境、失败与预算对比。真实测量前的脚本验证单独见后续 r09 验证记录。
