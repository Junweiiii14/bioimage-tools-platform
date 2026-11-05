# P012 首次使用走查

2026-11-05，Windows 本机，Python 3.12.14 / 锁定 uv 环境。基线 ec7588ded1a7e8ac5febec5d2faed51e7ef0e0fc，活动树 bioimage-plan-sync。通过 computer-use 的原生鼠标/键盘/文件对话框操作实际 WebWorkbenchWindow；未把测试快照注入本次走查窗口。另设 QSettings 和项目目录，未改变在用安装。开发者走查不等于学生独立试用。

## 输入与实际结果

仓库外 `../p012-first-use` 保留原始素材、项目及导出，不提交二进制。项目 `projects/inputs-20261105-205756-8b33fa1b`。两张 300×700 uint16 合成矩形 TIFF，几何同既有五泳道回归，A/B 仅膜外像素不同；可用 [生成器](../../../examples/wb-first-use/generate.py) 重建。

1. 从空首页导入 inputs 文件夹。Fig 1、N=5、Target/Reference，A→Target、B→Reference，自动裁图、成图、定量、保存完整输出完成。两行原始积分均为 268125、375375、268125、375375、268125。
2. 建立 housekeeping / ratio_only，S1–S5、逐泳道 1:1 对应。S1 填写 Synthetic-P012 / Practice-control / DemoBio1 / DemoTech1；其余四条身份未知留空。确认、保存、刷新后五个比值为 1，相对值为空；身份分别为已填写/未填全。
3. 切换 single_control 后原确认撤回，未确认保存时明确提示尚未确认对应，数值不伪装为有效零。重新确认但未选对照时，比值为 1、相对值为空，提示请选择恰好一个对照。选择 S1、重新确认保存刷新，五个比值及相对值均 1。
4. 身份/归一化变更后旧完整输出保留为历史；继续自动处理生成新输出快照，未重做上游积分。旧输出后缀 `_02d7128e4b7d`，新输出后缀 `_b0eba4e5cb89`。
5. 通过原生另存为导出 `normalized-ratio.xlsx`、`normalized-relative.xlsx`、`raw-integrals.xlsx`、`practice-figure.png`。独立读取 XLSX ZIP/XML：五条样本、对应积分、比值/相对值、单对照标记及身份准确；raw 表两行五值一致。PNG 实际查看为两行五条带、Target/Reference 标签，800×300。未使用外部 Excel/WPS 验收。
6. 文件菜单关闭项目并返回首页，最近项目继续工作；积分、配对、S1 身份、S1 对照及确认状态保留，刷新归一化仍为五个 1。发现页面错误返回配置页，但数据未丢失，详见下方修复。

## 确认的障碍与最小修复

- 配置 N 后第一次单击蛋白框、输入蛋白后第一次单击来源可能失效。独审定位到 input 已更新局部绑定，blur/change 又整体替换 DOM，销毁下一次点击的目标。顺序编辑器对已由 input 完整处理的搜索/标签/N/多行蛋白字段跳过重复重绘，其他选择控件及旧网格路径保留。
- 最近项目记住结果页，但后端及前端加载路径均无条件改为 intake。后端保留匹配项目且有效的已存 mode；前端再按当前允许页面过滤，编辑/未就绪项目仍回准备页。未改变科学数据或 schema。
- 英文 valid 状态记录为待真实试用观察项；本轮不凭开发者偏好扩大文案改造。
- 自动化工具的原生弹窗缓存索引过期、菜单覆盖窗口识别和状态刷新滞后单独处理，不计产品故障。

## 验证记录

- `uv run --locked --no-sync pytest tests/test_intake_web_ui.py::test_sequence_field_blur_preserves_next_real_click tests/test_wb_student_results.py -q`：4 passed / 30.44s，exit 0。实际 Qt 鼠标验证单击焦点/来源，自动处理三组用例保留既有正反例断言并增加完整关闭/打开路由检查；未弱化预期或容差。
- 生成器新目录执行 exit 0；独立像素检查与走查 TIFF 完全相同、uint16。对同目录再执行得到预期 FileExistsError 非零，前后文件 SHA 不变；外层验证 exit 0。
- 独立 ZIP/XML/PNG 检查 exit 0，详细临时数据在 `.local/p012-artifact-check.json`；本页记录必要结果，不提交长日志。
- 完整门禁、准确候选独审与 PR 集成结果后续记录；此处不预报通过。

## 试用边界

[学生练习及观察项](../../../examples/wb-first-use/README.md) 交给准备人员生成素材，再由学生独立尝试。真实实验配对、组别、重复和原软件扣背景口径仍 UNKNOWN；本次不猜测。科学适用性、真人学生独立使用、干净 Windows/GPU/DPI 与外部表格软件均未验，不由合成走查或工程测试代替。
