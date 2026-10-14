# WB 数值核心

公开入口 `wb_tool.api`；包版本 0.2.0，当前实现 `profile_integral@1`、TIFF 输入及泳道剖面，尚无产品 GUI。
数值契约与参考来源见 `../../docs/contracts/wb-reference-v1.md`。

- 输入：未平滑且已声明极性的非负有限剖面、闭区间 `BandBounds`、可选 `Baseline`。
- 输出：不可变 `ProfileMeasurement`，含信号、边界、基线来源、算法和单位。
- 失败：`QuantificationError`；有效平坦区域返回真实零值，未检测状态由后续用例表达。
- 数值领域不读文件、不依赖 UI、不推断蛋白身份、不乘泳道宽度。
- `load_tiff` 支持单页 uint8/uint16 灰度与 RGB/不透明 RGBA，保留原文件与位深；
  RGB 使用整数 BT.601，MINISWHITE 不静默反相；多页/透明/非左上方向明确拒绝。
- `compute_lane_profiles` 需要显式 dark/light 极性与稳定 lane_id，坐标为半开矩形。
  读取数组以 bytes 为后备，不能重新开启写入；均值以 float64 计算，不修改原像素。
- NumPy 和 tifffile 依赖均固定为已有锁版本，不引入新的第三方包。

验证：仓库根 `uv run --locked --no-sync pytest tools/wb/tests -q`；
完整门禁 `uv run --locked --no-sync python dev.py check --all`。
