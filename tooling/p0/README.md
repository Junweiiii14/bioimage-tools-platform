# T-002 / P0 技术探针

这是可丢弃的技术验收程序，不是平台 SDK 或 WB 算法。正式产品包仍须遵守 src/API/import-linter/隔离 wheel 测试规则，不从本目录复制未审查的架构。P0 不写数据库，不修改输入文件，不联网。

## 分层与语义

- `p0_probe.py` 在导入 Qt 之前分派 `--worker`；发布态为同一 EXE。
- `imaging.py`：TIFF 读取和只读原始数组；Y/X 半开 ROI，列剖面平均 Y。RGB 明确仅红通道；显示 uint16 全范围映射到 uint8，与定量分离。
- `numerics.py`：SciPy 窄类型边界。技术负载为 3 次 sigma=1、reflect、float32 Gaussian，两个交替缓冲；不是实验预处理建议。
- `protocol.py`：p0-v1 / protocol=1 / attempt=1，1 MiB UTF-8 NDJSON，run_id 和单调 seq。一次 worker 一个任务，无重试、子进程或插件加载。
- `worker.py` / `pipe.py`：控制线程、合作取消、单输出锁；进度不超过 10 Hz。Windows 直接 ReadFile 避免 CRT 阻塞读取与数值 DLL 加载冲突。
- `controller.py`：QProcess 异步信号；取消 5 秒宽限后强停，收到 finished 才决定终态；取消请求先于 finished 时取消优先。300 秒总任务超时失败。Windows 开发态绕过 uv 的 venv 启动器直接启动真实解释器，包态直接启动同 EXE；当前 worker 不产生子进程，未来增加外部程序必须补进程树机制。
- `gui.py`：异步加载、QGraphicsView、512² ROI、原始剖面、运行/取消/故障按钮，退出先收敛 worker/加载线程。
- `fixtures.py` / `benchmark.py` / `build.py`：固定样本、真实进程、干净提交构建。

## 复现（仓库根）

```powershell
uv sync --locked --all-groups
uv run --locked --no-sync python dev.py check --all
uv run --locked --no-sync python -m tooling.p0.fixtures .local/p0/样本
uv run --locked --no-sync python p0_probe.py --fixtures .local/p0/样本 --evidence .local/p0/desktop
uv run --locked --no-sync python -m tooling.p0.benchmark --fixtures .local/p0/样本 --output .local/p0/benchmark.json
# 必须先提交且 Git 工作区干净；失败构建保留原目录，重试用新提交。
uv run --locked --no-sync python -m tooling.p0.build
# 将以下路径替换为实际生成的包
uv run --locked --no-sync python -m tooling.p0.benchmark --fixtures .local/p0/样本 --output .local/p0/benchmark-package.json --executable <包目录>/BioimageP0.exe
```

样本生成拒绝覆盖目录；基准和界面证据拒绝覆盖文件。手工 GUI：依次加载三种图、拖动 ROI；批处理时拖动、取消；模拟崩溃后再运行并保存记录。不要在未观察完成时将失败改为成功。

## 验收口径

三类单图各 5 次、20 图批次 3 次，fresh worker，未清空文件系统缓存。median/nearest-rank p95 同时报 n，小样本 p95 近似最大值。固定尺寸见 manifest；不得为达标缩图。

ROI 延迟是 Qt mouseMove 处理开始至画布 paint 返回，目标后台 p95≤100ms；不包含物理输入/屏幕扫描。事件循环延迟单列。真实原生输入与 Qt 自动事件不可混称。内存记录 OS 的进程 RSS 高水位；GUI 峰值与 worker 峰值之和为保守上界（含共享页双计），1 GiB 为观察预算，不是 OS 硬配额。

CI foundation 增加锁定的 desktop 组，以便严格类型检查与真实 worker 测试在 Windows/Linux 都运行；Qt 使用 offscreen。检查名称和服务器要求保留。新增依赖为零，锁文件不变。CI 不代替真实 Windows 窗口或干净机。

125/150/200% 的进程缩放仅能证明 Qt 在相应 DPR 绘制；必须与实际系统缩放、多显示器切换验收区分。用户已指定干净 Windows 无 Python 验收为后续待办。本机移出仓库、清空 Python/Qt 环境的成功不能替代该验收。

当前限制：仅可信合成 TIFF，未做恶意 TIFF 沙箱/压缩炸弹防御；不包含发布签名、安装器、升级与生产持久化。构建日志/XML 留 `.local`；小型 JSON 和结论进入 `work/evidence/T-002/`。
