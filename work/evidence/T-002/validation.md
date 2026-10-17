# T-002 / P0 本机验证记录

状态：2026-10-14 收尾。本机便携包、自动进程和性能验证通过；源码原生窗口实操通过。用户按物理 Esc 停止 Computer Use，包态原生窗口实操与 125/200% 进程缩放尚未完成，不能宣布完整本机 P0 或整体 P0 通过。

## 范围与环境

用户授权本机验证和便携包，无 Python 的干净 Windows 验收待后续。仅合成图，不含 WB 科学分析或私有科研数据。主机详见 host.json，样本生成算法与逐文件 SHA256 见 fixtures.json；原始 PDF 未变。

源码应用实现提交 d81350859588；裁剪构建提交 293c6c0632e2。后续只有构建脚本/证据/文档变化时，不将其冒写成重新编译的 EXE 提交。全部构建从起始干净已提交源码开始。

## 已执行

- 基线 29 tests passed；P0 新增协议、原值、解析常数、真实进程故障测试后 `dev.py check --all`：Ruff / Pyright strict / 35 tests passed（23.74s）。
- GitHub 四项必需检查在 293c6c0 均通过；[quality](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/38425626944)、[rules-context](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/38425626382)。Linux 首次缺 libEGL 已补系统依赖，无跳过测试或更改预期。
- 源码真实窗口：2048²/4096² uint16 和 4096² RGB 载入；后台拖 ROI 更新原始剖面；取消→确认退出、故意 exit 23→界面仍可用→20 图新任务成功。RGB 和 16-bit 原值哈希不变。
- 原生控制工具将原始 pythonw 误关联 IDLE；以独立命名的开发解释器消除歧义，保留实际开发环境，不把此别名解释器算作 portable。

## 源码进程基准

固定 3 次 float32 Gaussian reflect/sigma=1；每个任务 fresh worker，未清空 OS 文件缓存，首个样本计入。终端打印编码无损性以 UTF-8 JSON 为准。nearest-rank p95；n 小时接近最大值。

| 任务 | n | 中位数 / 秒 | p95 / 秒 | worker RSS 峰值 / MiB |
|---|---:|---:|---:|---:|
| 2048² uint16 | 5 | 0.614 | 0.632 | 105.4 |
| 4096² uint16 | 5 | 1.385 | 1.397 | 225.3 |
| 4096² RGB（红通道技术负载） | 5 | 1.396 | 1.398 | 241.4 |
| 20×4096² uint16 整批 | 3 | 19.464 | 19.524 | 225.5 |

源码合作取消：ack 0.435ms，停止 155.194ms；强停注入：ack 0.497ms，停止 5009.584ms。两者仅进程退出后记录 cancelled。崩溃和故意卡死无最终峰值帧，协议默认的 peak_bytes=0 表示未报告，不能解释为 0 内存。

源码桌面在系统实际 DPR=1.5、编译并行运行期间：原生拖动样本 n=4，后台 ROI 事件处理至画布 paint 完成 p95=26.817ms；样本少，包态将继续采样。测量不包含 OS 输入延迟、物理屏幕扫描或整窗曲线绘制完成。另有事件循环延迟记录。GUI RSS 高水位 315.6MiB（先后加载三类图）；不是 worker 内存。

## 打包与剩余步骤

首轮 broad build：1025 个 C 模块，Pygments 325 / SciPy 465，主动中止以收窄明确未使用的依赖。缓存和退出 1 manifest 留 `.local/p0/build-d81350859588`。第二轮保留实际加载的 linalg/ndimage/special 等，降为 359 个模块、364 个 C 编译文件，713.239 秒构建成功（exit 0）。本轮 ccache 364 miss / 0 hit，未证明增量加速。运行目录 107 个文件、183.465 MiB。

构建提交完整哈希、锁文件 SHA、逐二进制 SHA 和工具版本在 build-manifest.json；大编译日志/XML 留本地，哈希在 build-audit.json。初始 PDF 不变。

便携 ZIP：`C:/Users/70236/ResearchVault/Codex-Workbench/deliverables/BioimageP0-Windows-x64-293c6c0.zip`，832523276 bytes（约 794 MiB，包含约 728 MiB 固定未压缩合成图）。SHA256：`277bee1aa99c0fb92a87af0742aeeecec72f1913b2d2dbf3bad15e553dcb3399`。ZIP 已解压到仓库外的 `deliverables/P0独立验收/BioimageP0-293c6c0`，330 个文件逐个核对 SHA256 通过。未将大样本或二进制提交 Git，也未发布 GitHub release。

## 包态固定基准（exit 0）

同样的固定负载与计时方法，完整原始结果在 benchmark-package.json；没有同时编译或执行桌面操作。源码与包态运行时间不同，不能据此声称 Nuitka 加速数值计算。

| 任务 | n | 中位数 / 秒 | p95 / 秒 |
|---|---:|---:|---:|
| 2048² uint16 | 5 | 0.587 | 0.853 |
| 4096² uint16 | 5 | 1.476 | 1.495 |
| 4096² RGB（红通道技术负载） | 5 | 1.492 | 1.505 |
| 20×4096² uint16 整批 | 3 | 21.819 | 21.977 |

worker 进程 RSS 最高 257.855MiB。合作取消 ack=0.751ms / 停止=177.227ms；故意卡死的强停 ack=0.728ms / 停止=5004.787ms。包态故意崩溃后新进程恢复任务成功；所有 hello 均报告 Qt 尚未导入。此处验证的是同 EXE 的 worker 自动进程路径，尚不等于包态 GUI 按钮实操。

最小子进程环境已启动 EXE，PATH 仅 Windows 与 System32，未设置 Python/Qt 路径；cwd 在上述中文目录。启动记录见 desktop-package-launch，Python/Qt/platform DLL 的实际加载来源见 gui-loaded-modules.json。进程启动与 DLL 自给性已观察；随后原生工具报告用户物理 Esc 停止，因此未读取包态窗口截图、未执行包态载入/拖 ROI/取消按钮，也未做 125/200% 进程缩放。

本机仍安装 Python；上述结果不等于无 Python 干净机。包态 GUI 载入大图后的峰值与原生交互 p95 未测，不能将源码窗口指标直接填入包态结果。EXE 窗口留在本机，用户可自行关闭；后续继续须重新选择当前窗口，禁止复用旧 handle。

独立审查未进行，[PR #3](https://github.com/Junweiiii14/bioimage-tools-platform/pull/3) 保留草稿。干净 Windows、包态原生交互与缩放、跨显示器切换、签名安装器/升级、正式包边界与科学参考验证不在本轮已通过范围。最终本地全检查 35 passed（27.22s），Ruff/Pyright strict 通过；最终远程状态以 PR 对应 head 为准。
