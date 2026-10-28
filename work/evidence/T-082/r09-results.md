# R09 冻结基线实测：上界触发性能整改

2026-10-28，本机 Windows 独占工程测量。准确源码/工具运行提交 **`244c5da1b03e47f6d17801912cb38003e8edab27`**，包含已独审的 R09 工具 `8d26a9c`。开始及四场景之间工作树保持 clean，全部按[事先冻结方案](r09-benchmark-plan.md)运行，没有调整规模、次数或预算。

**结论：两个小规模样例未触发预设预算；两个上界样例明确超预算，R09 已触发有限性能整改，不能以“测完”宣布整改完成。** 空闲缓存四组均正常命中；超线发生在全量构造/序列化、刷新显示和载荷/内存。结果只覆盖合成工程输入，不宣称真实实验项目、所有用户设备或科学适用性已达标。

## 环境和原始证据

- OS：Windows 11 家庭版中文版 10.0.26200；CPU：Intel Core Ultra 7 255HX，20 核/20 逻辑处理器，WMI MaxClockSpeed 2400 MHz（不是实测持续频率）。物理内存 16,496,738,304 B，启动前 FreePhysicalMemory 3,615,612 KiB；不声称系统内存/其他程序负载完全空闲。
- Python 3.12.14、Qt 6.12.0；每进程局部设置 `QT_QPA_PLATFORM=windows`、`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu`，QT_OPENGL/QT_QUICK_BACKEND 未设置。本机软件渲染诊断，不是 GPU 修复证明。
- 逻辑屏幕 1707×1067，devicePixelRatio 1.5、logicalDPI 96；窗口 WebEngine viewport 1440×940。仅这一个 DPI/本机屏幕，不代替物理 DPI 全矩阵。
- 启动前电源方案 Performance（GUID `27fa6203-3987-4dcc-918d-748559d549ec`）；全部结束后 13:54:21 +08:00 的 Win32 电源查询为 ACLineStatus=1、BatteryLifePercent=80。后一次采样不证明整个区间电源状态从未变化。
- root 已确认其他 agent 暂停 GUI、构建、pytest，仅进行少量只读复核。四个场景逐一单进程执行；用户其他负载没有被控制，也不假称已消除。未强杀进程，成功写报告前均经过正常 close/drain/deleteLater；结束后按记录 PID 查询，四个本工具宿主和对应页面 renderer 均已退出。
- 原始 JSON、完整 stdout/stderr log、逐例 exit/起止时间、环境、汇总及 SHA 清单位于 ignored `.local/T082/r09/run-244c5da-20261028054722415/`。`sha256.json` 自身 SHA256：`196d0a65db576da8c6246442e04e8fdbea861c190484ddd1bf7e5753d9d36e89`。这些本地原件不随 Git 克隆迁移；本页保留可对照摘要与测量结果，后续交接需保留该目录。

## 命令与退出

统一前缀为 `uv run --locked --no-sync python -m tooling.benchmark_workbench_snapshot --run`，各次加入下表 `--case` 与对应新 JSON 输出路径；没有重试。默认每段预热 5 次、保留 30 次，p95 为排序第 29 项（nearest rank），原始样本全部保留。

| case / 输出文件 | 本次进程总耗时（秒） | exit | 夹具 |
| --- | ---: | ---: | --- |
| rows-small / rows-small.json | 10.055 | 0 | 4 行、2 Fig、每行 6 槽、24 个 pending 状态项 |
| rows-limit / rows-limit.json | 114.897 | 0 | 512 行、128 Fig、每行 96 槽、49,152 个 pending 状态项 |
| intake-small / intake-small.json | 10.382 | 0 | 同小规模，4 个来源/缩略图 |
| intake-limit / intake-limit.json | 176.975 | 0 | 同上界，512 个来源/缩略图 |

所有结果均为原生 trusted 点击，真实 nonce 回执与成功 render 序号/双帧检查通过。没有驱动故障、超时或被丢弃的性能样本。小规模不是用户实际项目分布；上界也不表示所有 schema/文本/历史/原图尺寸同时达到最坏值。

## 结果

以下耗时为 ms。构造、JSON、总耗时的分位数各自计算，不能把两个分段 p95 相加当作总 p95。冷段只清 PNG 字典，不是冷启动。

| case | 冷构造 p95 | 冷 JSON p95 | 冷合计 p95 | 热构造 p95 | 热 JSON p95 | 热合计 p95（预算 50） | 点击 p95（预算 200） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rows-small | 0.1048 | 0.0574 | 0.1622 | 0.0954 | 0.0744 | 0.1675 | 177.20 |
| rows-limit | 524.7926 | 127.0882 | 651.8808 | 529.5591 | 130.1224 | 657.7564 | 1221.50 |
| intake-small | 1.7929 | 0.3896 | 2.1875 | 0.3547 | 0.3833 | 0.7327 | 191.60 |
| intake-limit | 776.8921 | 199.4586 | 973.1616 | 626.5718 | 197.7324 | 824.3042 | 2162.90 |

两个小样例的最大点击耗时分别为 233.60/240.10 ms，虽 p95 没有超线，并非“每次点击均小于 200 ms”。对应上界最大点击为 1238.20/2193.60 ms。点击起点为 event.timeStamp，handler 起点 p95 分别为 175.70、1220.10、190.70、2161.40 ms；均包含基准 nonce instrumentation，双 rAF 不是显示像素落屏证明。

| case | idle publish p95（预算 1 ms） | idle snapshot / state emit | UTF-8 最大字节（预算 16 MiB） | host+renderer private 前→后（GiB；预算 2） |
| --- | ---: | ---: | ---: | ---: |
| rows-small | 0.0076 | 0 / 0 | 15,252（0.015 MiB） | 1.600 → 1.629 |
| rows-limit | 0.0098 | 0 / 0 | 25,009,484（23.851 MiB） | 1.905 → 2.352 |
| intake-small | 0.0126 | 0 / 0 | 195,697（0.187 MiB） | 1.605 → 1.693 |
| intake-limit | 0.0104 | 0 / 0 | 48,294,826（46.058 MiB） | 2.017 → 3.198 |

private 是 Windows private commit，不是物理 RSS；前/后仅两个采样点，不是峰值，不含 GPU/utility 子进程。逐进程 working set 和 lifetime peak working set 在原始 JSON。仪器上界在采样前已略高于 2 GiB；这些数据不足以诊断泄漏。180/150 ms 的两个窗口定时器按冻结方案停止以隔离采样，所以没有测生产后台任务竞争或多窗口争用；不能把结果泛化成所有交互。

## 日志与下一步

四个日志均保留 Chromium GLES3→GLES2/shared context 回退错误；intake-small 还记录 SharedImageManager non-existent mailbox 信息。所有进程最终 exit 0 和成功 nonce/render 检查不代表这些历史图形问题已解释或消失。本轮没有把软件渲染下的通过写成 GPU 修复。

实测已把同步代价拆到构造与 JSON：两上界的热 JSON 本身已超过 50 ms，单纯加速构造仍不足以满足原预算。源码只读定位的候选包括 `web_bridge.py` 按每一行重新过滤全 cells（512×49,152 扫描），以及顶层 cells、逐行 results、仪器 visibleTable/inline 缩略图的载荷重复。这里只是结合分段数据的优化候选，尚未做函数级 profile，不能宣称某一行是唯一根因。

建议 root 先限定处理真实重复扫描与大状态载荷，必要时采用现有分页/资产引用；保护稳定身份、缺失状态、草稿与全部导出数据。必须用同一夹具 SHA、次数/预算、尽量同一机器/电源/Qt 环境复测，并保留当前基线。不得削减到更小规模、增加缓存旁路或改预算后宣称原问题解决。此次执行者仅提交测量证据，**未优化产品、未更改任何阈值或导出行为**。

## 摘要锚点

| case | 结果 JSON SHA256 | 完整日志 SHA256 |
| --- | --- | --- |
| rows-small | `e420c18b61e32bbc1ec04a195d4f95f15b3bbb1131211fa66c1e41848a9c2f80` | `73501ed942ba58b9c37373e698afaf43d0611711b214695ceeca294e425312aa` |
| rows-limit | `e5477621f30c5511d3af98fd0ea047d7529161ed9c10e00050b3169700a20fd3` | `773b696d048388b241000dc1787b5ab409803b07dcf0cca3dd735f808af187b5` |
| intake-small | `a414cded8e3ee28838ee8955d7f8f917485cb1e148ca5d04df1873935ded2010` | `3035b97f1e8a78ed72b5b366e0ac21dd336e6b25d11a76a460263da19aa93686` |
| intake-limit | `1c5feb092f989c1bba2c81faf8b7a5d277caa8d35092a90fcbb29fa5c43dd99e` | `b9dacf87898e03e6b3fe4f2be1e4e44d9e27c5184a63bd7ef76e2b8fde1ad2f0` |

夹具 JSON SHA256（与将来复测逐一比对）：rows-small=`3c0ea28cb00661130229c501ff5ce7374a3caf33e71d0c0b77ad39c5b17002af`；rows-limit=`06b5c973121a21adf15b19a6469f1b92cbb97041cc7d00de45c014f3b3c8145e`；intake-small=`11f185a269ff4f46e11622a0a203f451f4d8d36427084c68d24fb04cb72302c4`；intake-limit=`ae39df820412576fe4e37dacde87b45e4afc31911b28abe7722120f79c3ed573`。
