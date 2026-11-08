# P028 固定独审：本地目录候选通过

2026-11-09，Windows 本机，独立 detached 工作树；审查范围是沿用构建器刷出的本地交付。无新产品实现。本结论绑定以下源码和工件；不是公开发布批准。按规划窗口确认，无需以纯收据 PR 作为本工件通过的前置条件。

| 对象 | 标识 |
|---|---|
| Git 产品源码 | `3103063d1abf116ef1d98694b9cc57f4dc70ae22` |
| 版本与通道 | `0.14.0 / wb-acceptance-p028-local / Acceptance-p028-local` |
| BioImageWB-Acceptance.exe SHA256 | `c296f84d2b661386ba0fd6ff1b18b51803ebac529edbe45145b1592398847992` |
| build-manifest.json SHA256 | `2b318419fa25d541503debb563d17cd884a69336e905319667cb0df360141424` |
| payload-files.json SHA256 | `367473a38d51c01b28ff70c735abf6a1aa46b92e3edc467ea578848cda6518fd` |
| P024 练习 ZIP SHA256 | `73ccd34c0ed1dbb971241edf200c90ccbe58539f1188189a31f387e423944d2c` |

**工件来源。** 独立 Python 3.12.14 运行 `-I -B .local/provenance/verify_p028.py`，exit 0。[逐项核验回执](provenance/receipt.json)：核对 7,900 个冻结文件大小及摘要、506 个 Git 归档成员和 308 个安装源码/资源。另有生成的 1,006 个 pyc，不属于冻结摘要。与 P023 的六个 wheel 比，五个相同；桌面包只变动 intake_groups.js 及其 RECORD。没有发现本次更改开源算法原件。核分割沿用未变工程覆盖，外部 worker 在位、三项固定模型文件摘要吻合，本轮未重跑推理。未从头重建包或跑全仓门禁。

**WB 单图草稿。** 由审查侧的 IOCBIO 归档取 gel1_GAPDH_expo1min.tif（SHA256 af35f27d9171f1699a8247611dc48683833f03eae1ed30a1e795ad5966ab3a64）。从冻结包的私有 runtime/python.exe 以 `-I -B -X utf8 .local/wb/probe.py save|reopen` 启动两个实际进程，使用独立 INI、项目父目录和 offscreen Qt 文件夹对话框。通过真实页面控件从 WB 选择普通文件夹，点“识别来源与参考图”，得到 unknown、无区域、无错误；加 Fig、填 GAPDH、选原图、保存。第一个进程正常退出；第二个进程在 WB 页按完整路径匹配可见的最近项目，恢复同一项目。比较了完整分组草稿和选中源标识，两个进程均为 Fig 1/GAPDH、N 为空、原图已选、开始自动处理禁用，项目 runs/results 空，输入摘要未变。两次 GUI 资源正常关闭，进程退出码均为 0。[保存](wb/save.json) · [冷重开](wb/reopen.json)。第一次重开探针不限定页面，匹配到隐藏的首页副本，超时 exit 2；改为 WB 页可见控件后通过，未修改产品。

**原生入口与练习。** 实际启动同一 Win32 EXE，以独占回环调试端口和 offscreen 模式打开包内页面，由首页进入 BCA。选择 CSV、加载板记录和打开项目均可用；无输入时运行禁用。从界面正常退出，EXE exit 0；其验收设置摘要前后一致。[原生入口](practice/native-2/receipt.json)。第一次驱动在创建进程前因环境变量名大小写停止，不是产品退出。另用包内 `python -I -B -m bioimage_app.bca_cli` 对 P024 ZIP 内实际合成 CSV 和板记录运行、换进程重开，命令及摘要见 [练习回执](practice/cli-1/receipt.json)：两次 exit 0，S1 为 5008.680555555556 µg/mL，4 个部分结果的均值留空，三个输出摘要一致。并非从 GUI 选文件完成 BCA 计算。

**证据边界及整改。** 作者还实际用 EXE 和 Windows 原生目录框保存、另起 EXE 重开同项目；首轮关闭无数字退出码，第二轮为 0。独审 WB 使用包内运行时的独立 INI，不混称为独审操作原生系统选框；独审原生 EXE 的无编辑入口退出另有记录。离屏运行有 GPU/GLES 诊断信息，未将其计为物理显示、真人、其他电脑或科学准确性验收。P028 走查说明原写另一分组页的“识别来源与 N 建议”，已反馈，并在活动树确认改为与包内实际按钮一致的“识别来源与参考图”。无未关闭的本轮工件阻断。
