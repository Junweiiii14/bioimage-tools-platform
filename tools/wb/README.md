# WB 数值核心

公开入口 `wb_tool.api`；包版本 0.5.0，实现参考积分、TIFF、泳道、手工分析、后台协议与可选Qt复核页面。
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
- 协议使用已有锁版本 Pydantic 2.14.1；`python -m wb_tool.worker` 是单任务后台入口，
  stdout 仅为 UTF-8 NDJSON，容量/身份/顺序/取消规则见 `../../docs/contracts/wb-worker-v1.md`。
  worker 返回结果候选，不提交数据库或宣告宿主成功。
- `analyze_annotations` 接受来源摘要、revision、泳道/条带不可变标注，返回明确定量状态；
  取消或来源不符不返回成功结果，部分泳道失败保留原因；位深上下限像素触发复核，
  待复核原始积分不能进入有效信号列。契约见 `../../docs/contracts/wb-manual-analysis-v1.md`。

验证：仓库根 `uv run --locked --no-sync pytest tools/wb/tests -q`；
完整门禁 `uv run --locked --no-sync python dev.py check --all`。

`[desktop]` 可选依赖使用已有锁定Qt；普通API/worker导入不加载Qt。
create_wb_view/create_wb_background 是延迟装配入口；PreviewRaster 是显示专用字节，
不会传给定量用例。WBDocument v1 保存原输入资产/标注，契约见 wb-document-v1.md。
桌面入口由apps显式装配：`uv run --locked --no-sync python -m bioimage_app`。
当前手工界面可拖ROI/编辑闭区间与基线/查看原始曲线和结果状态；OCR/自动写表尚未完成。
