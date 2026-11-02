# 旧方法对照：5–10分钟验收

这是研发第一阶段V0的工程对照入口。它让同一成熟WB方法从旧入口和独立模块各运行一次，验证数值、失败语义及保存后的读取。合成样例的预期在执行前固定；一致性不代替真实实验的独立科学验证。

## 桌面操作

1. 在当前开发环境运行 `uv run --locked --no-sync python -m bioimage_app`。点击顶栏 **旧方法对照**。已有实验项目和草稿保留；当前WB处理尚未结束时，先完成或取消该任务。
2. 保持 **16位三角峰 · 预期4000**，点击 **运行对照**，在原生选择器中选择保存父目录。程序自动建立新的 `WB对照-日期-身份` 工程，不覆盖旧目录。
3. 等待“成果已保存并核验”。**差异**应显示旧入口4000、独立模块4000、差值0、状态有效；**数值**可查看有效信号和单独的原始积分。展开 **保存与来源依据** 可见实际工程、运行身份与进程号。
4. 点击 **关闭并重开核验**。程序重新打开工作区并校验已登记资产；数值和运行身份应保持。关闭整个软件后，也可从 **旧方法对照 → 打开对照工程** 选择同一目录。
5. 再选 **平坦剖面** 运行到新的工程：有效信号是0。再选 **越界ROI**：两次结果均无效、数值及差值为“—”，并保留超界原因。**位深端点**样例为待复核，不能当作有效零。
6. **打开工程文件夹** 可找到 `v0-compare/measurements.csv`、`differences.csv`、`run-manifest.json` 及两份机器结果。表格字符串使用 `text:` 字面前缀；空单元格是缺失/无效值，不是0。正式界面从已登记的工作区资产读取并校验；请勿改写工程内部资产。
7. 关闭对照窗口，原WB实验项目应仍在。普通实验项目继续从原 **打开项目** 入口进入；对照工程使用专用入口。运行中点击取消、关闭对照窗口或退出软件，会等待计算退出及存储排空，不提前宣布成功。

无需重新安装或替换在用版本。此处的启动命令依赖已同步的开发环境，不是新安装器发布说明。

## 无GUI调用

从仓库根目录运行；目标目录必须不存在或为空。以下两个命令不会创建GUI窗口：

```powershell
uv run --locked --no-sync python -m bioimage_app --v0-compare .local/v0-example-001 --case triangle_u16
uv run --locked --no-sync python -m bioimage_app --v0-open .local/v0-example-001
```

可选样例：`triangle_u8`（40）、`triangle_u16`（4000）、`flat_zero`（有效0）、`invalid_roi`（无效空值）、`dtype_limits`（待复核空值）。输出UTF-8 JSON，包含真实RunRecord、已核验文件路径及表格预览；成功保存报告退出0，失败/取消退出2。`quality=issues`表示报告内含异常测量，不能把报告成功理解成所有行有效。

显式原图与原AnalysisRequest JSON可用同一入口：

```powershell
uv run --locked --no-sync python -m bioimage_app --v0-compare .local/v0-explicit-001 --source C:/data/original.tif --parameters C:/data/analysis-request.json
```

参数必须明确原图SHA256、修订、dark/light极性、泳道ROI及条带边界。只接受本次准入的`fixed_grid@1`和`legacy_bounds@1`，不猜测ROI、极性或归一化配对。`wb_tool.api.prepare_wb_execution`与`execute_wb_module`还提供不依赖Qt的Python用例入口；完整CLI宿主使用QtCore事件循环复用真实进程、异步存储和取消机制。

## 如何判断失败没有冒充成功

不支持的dtype、输入改变、缺失/篡改输出、错误身份、manifest后非零退出或取消，都不能得到成功结果引用。已有失败运行重开后仍有原因。被外部改写的正式资产会导致核验失败，界面清空相应表格，不展示缓存值充当有效结果。

`v0-compare`内文件是本次计算导出的报告；Workspace中的最终RunRecord及其成果清单记录正式发布。清单、参数/输入/实现/环境摘要和物理资产引用的边界见[模块契约](contracts/wb-module-v0.md)。

## 验收范围

工程检查、独立代码审查、GUI视觉审查、用户实际体验及科学验证分别记录于[P002任务](../work/tasks/P-002-wb-headless-module.md)。未取得的用户体验确认不代签；独立留出实验材料、干净Windows/员工设备、物理DPI/GPU等既有未验项继续保留。不扩展V1几何校正、IF或科研Agent。
