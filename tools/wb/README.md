# WB 数值核心

公开入口 `wb_tool.api`；当前实现 `profile_integral@1`，尚无产品 GUI。
数值契约与参考来源见 `../../docs/contracts/wb-reference-v1.md`。

- 输入：未平滑且已声明极性的非负有限剖面、闭区间 `BandBounds`、可选 `Baseline`。
- 输出：不可变 `ProfileMeasurement`，含信号、边界、基线来源、算法和单位。
- 失败：`QuantificationError`；有效平坦区域返回真实零值，未检测状态由后续用例表达。
- 不读取图像、不依赖 UI、不推断蛋白身份、不乘泳道宽度。

验证：仓库根 `uv run --locked --no-sync pytest tools/wb/tests -q`；
完整门禁 `uv run --locked --no-sync python dev.py check --all`。
