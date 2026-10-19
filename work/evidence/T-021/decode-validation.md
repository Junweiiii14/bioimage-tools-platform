# T-021 分段原图解码复用自验

- 日期：2026-10-15（Asia/Shanghai）；Windows，独立 worktree `t021-decode/bioimage-tools-platform`，分支 `codex/t021-decode-reuse`。
- 基线：`82d673ac98920e9f5ebf7216ee12d96677065165`；实现与本证据同一提交，最终集成提交由主任务记录。
- 环境：CPython 3.12.14；uv 0.13.0；锁定 NumPy 2.5.4 / tifffile 2026.9.20 / Pillow 12.3.0。未修改依赖、schema、算法标记、测试容差、skip/xfail、类型忽略或门禁。

## 修改与验证范围

按显示顺序建立清单及框线/占位，再将非重叠原图区域按 SHA 分组绘制。每源完整解码一次；辅助函数局部持有原图/裁剪/显示数组，返回后才解码下一源。分组仅存布局和清单引用，未建立跨源像素缓存。原有输出预算保持。每行仍核对 SHA、字节数、形状及位深；逐段和解码前后检查取消，末尾再检查一次，不返回部分成功图。

新增 10 项回归：真实 TIFF 调用计数；同图跨段和非相邻 A/B/A 行；三源逐次释放的弱引用证明；独立已知像素断言；基线完整 RGB 与 manifest SHA 固定比较；逐行四类来源不匹配；解码前、解码后、贴图后及共享源段间取消；坏 TIFF 拒绝。复用源错误用例修改的是后一个共享行，防止仅检查首次引用。

冻结结果由 `git show 82d673a:tools/wb/src/wb_tool/adapters/laboratory_figure.py` 的原渲染器与相同确定性合成 fixture 生成；测试运行不加载基线源码。RGB SHA 为 `a92c46baee4764d323841fa11922a7656a0e13c145b0b7fe265be6ff76db9c27`，完整 manifest SHA 为 `1ff09bfa4d93a4a40f5748023a278b9a6c76144c7999ad2894f9dbe054d3d2a9`。

## 实际检查

| 命令 | 退出码 | 结果 |
|---|---:|---|
| `uv sync --locked --all-groups` | 0 | 创建独立 .venv，安装锁定依赖 |
| `uv run --locked --no-sync python dev.py context --task T-021 --scope tools/wb --scope work --record` | 0 | 输出已读取；回执由主任务统一提交 |
| `uv run --locked --no-sync pytest tools/wb/tests/test_laboratory_decode.py tools/wb/tests/test_laboratory_layout.py tools/wb/tests/test_figure_project.py -q` | 0 | 35 passed，1.36s |
| `uv run --locked --no-sync ruff check tools/wb/src/wb_tool/adapters/laboratory_figure.py tools/wb/tests/test_laboratory_decode.py` | 0 | 通过 |
| `uv run --locked --no-sync ruff format --check tools/wb/src/wb_tool/adapters/laboratory_figure.py tools/wb/tests/test_laboratory_decode.py` | 0 | 2 files already formatted |
| `uv run --locked --no-sync pyright tools/wb/src/wb_tool/adapters/laboratory_figure.py tools/wb/tests/test_laboratory_decode.py` | 0 | 0 errors/warnings |
| `git diff --check` | 0 | 通过，Git 提示 CRLF 将规范为 LF |

初轮新增测试执行退出 1：夹具复用行 ROI 的 lane_id 未同步；修正为新行身份后，测试草稿仍有占位 SHA 和不支持的公开入口取消参数、未排序 import/静态类型问题。修正测试及显式 UTF-8 读写后，上述最终检查通过。未修改既有断言。

未运行完整 `dev.py check --all`、独立 wheel、真实大图内存/时间基准、GUI 或整套旧版本恢复；由主任务集成后完成。弱引用验证证明数组生命周期，不等于操作系统峰值内存验收。作者自验不算独立审查，T-021 整体尚需集成与审查。
