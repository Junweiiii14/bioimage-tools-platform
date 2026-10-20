# T-051 验证记录

环境：本机 Windows x64，锁定 CPython 3.12.14 / PySide6 6.12.0，
工作树 `t051-instrument-intake`。产品基线 `1ec1233`；当前修复提交 `65ff278`。
此记录只覆盖仪器导入/清单/分配阶段，不外推裁剪算法、科学准确率或安装包验收。

| 命令／检查 | 结果 |
| --- | --- |
| PR16 四项 required checks / match-head 合并 | 全部 SUCCESS；已合并 `43d520f` |
| `uv sync --locked --all-groups` | 0；未改依赖或锁文件 |
| `dev.py doctor` | 0；Windows11 build26200、CPython3.12.14、锁定开发工具版本 |
| `dev.py context --task T-051 --scope . --record` | 0；读取规则并保存回执 |
| 最初桌面集成三项（旧 192px） | 失败 FEFEF；关闭时异常 `0x80000003`，不算通过 |
| 128px 修正后 `pytest tests/test_instrument_intake_desktop.py -x -q` | 3 passed / 15.74s / 0 |
| 旧取消草稿单项及消息跟踪 | 失败；真实消息显示 cancel 时 `draft=True` 被旧 `position(False)` 覆盖 |
| 草稿消息修复后，会话＋导入＋UI | 14 passed / 13.08s / 0 |
| 异常缩略图拒绝与取消回归 | 12 passed / 11.77s / 0；包含模拟超预算结果，不挂起 busy |
| `9a0c465` 初次完整门禁 | 静态/类型/9 import contracts 通过；pytest 到18%后为整合独审修复，主动终止本任务 PID5088 树，退出1；未宣称完整通过 |
| 独审修复首轮定向 | 4 passed / 1 failed / 1；新增测试错误假定不同导入的整个 AssetRef 相等 |
| 修正新增测试预期后，桌面/UI/View/会话四文件 | 24 passed / 16.60s / 0 |
| 全项目 `pyright` | 0 errors / 0 |
| Ruff / format / commit hooks | 最后通过；中间长行/格式失败均已修正，未改规则 |
| `65ff278` 最终 `dev.py check --all`＋Windows fault observer | 801 passed / 549.84s；原始子进程0 / u32=0x00000000；全部隔离wheel/真实OCR完成；外层0 |
| `dev.py smoke-env` | 0；依赖、uint16 TIFF、QProcess、offscreen widget通过，仅环境烟测 |
| `Start-BioImage.ps1 --verify-launch` | 0；入口、desktop模块和web_ui均解析到当前T051树 |

最终完整门禁命令设置 `BIOIMAGE_WINDOWS_FAULTS=1`、
`PYTEST_ADDOPTS=-o faulthandler_timeout=60`；只增加既有原生观察及故障栈，
不修改成功状态、测试预期、skip、超时上限或 GPU 产品配置。
完整输出留在本树 `.local/t051-logs/final-check-native.txt`；失败及中止日志也保留在
该目录，不提交长日志。精简机器记录为 `final-exit-observation.json`。

## Qt 退出异常范围

Windows Application Error 1000 记录：2026-10-19 22:51:14，测试 Python PID56832，
模块 `Qt6WebEngineCore.dll`，异常 `0x80000003`，偏移 `0x6237b45`。
精简原始事件保存在 `native-exit-event.json`，未复制内存转储。
先前失败发生于缩略图回调抛错后，导入保持 busy，随后测试资源关闭超时；
同期存在 Chromium/Skia/D3D context lost 信息。

已修复可确定的 Python 回调与取消消息问题：请求128px、在资产导入前拒绝异常缩略图、
取消期间不让旧心跳清除草稿。此因果范围不等于证明 Chromium 内部断点的精确原生根因；
历史异常继续保留。最终完整测试的原生观察器实际附加到PID52244，没有记录新的
NATIVE_EXCEPTION；801项通过，原始子进程与外层均0。结束后核对已知pytest进程2272/52244
均已消失。真实隔离wheel包含桌面异步关闭、PP-OCRv6、本地OCR worker与PNG OCR，
全部退出0；这证明本轮复测通过，不删除此前原生根因UNKNOWN记录。

## 测试预期与范围说明

- 新增跨目录测试最初比较整个 `AssetRef`，但存储每次导入可以分配独立 `asset_id`。
  改为验证 SHA 与字节数一致、来源 ID 不同，并验证保存重开及同物理路径再次选择去重。
  该调整匹配既有存储契约，没有削弱独立候选身份断言。
- 旧取消草稿测试保留原预期，并新增确定性的旧 `position(False)` 对抗事件。
- 新增标签空格/逗号往返、字体不进入图像解码、既有复用不阻断无关分配、
  误加项单独撤销和 intake 不调用旧撤销的真实控件回归。
- 未生成或替换安装包；真实仪器留出、干净 Windows、物理 DPI/交互均未新增验收。
