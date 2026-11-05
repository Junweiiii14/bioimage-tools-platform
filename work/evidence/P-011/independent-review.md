# P011独立审查

用户明确授权只读子代理审查；独立审查者p011_independent_review，未修改源码或证据文件。本记录由主代理依据其返回结果整理，不将作者自验计为独审。

- base：87dba64196f8591405dd222f05a69dca07434291。
- 初审HEAD：7e875d10d86531795c49411142f10e9b8c35bab2。
- 修复复审HEAD：4dcd41eef34be8d9f99a0358dddfa81985d72295。
- 范围：完整产品/测试diff，自动证据与失效、原值/背景范围、身份兼容及导出、取消/草稿保护。

## 发现及关闭

P2：advanced.js的seed用pair.identity覆盖深拷贝，导致保存后编辑身份污染服务器缓存，撤销时重读失败后可能误存被撤销身份。独立Node探针提取真实seed确认cachedServer/discardDraft被改为UNSAVED。4dcd41e改为深拷贝身份；独立重跑Node探针通过。新增真实网页回归先复现旧代码误存，再覆盖保存→编辑组别→撤销重读失败→修改样本名→重新确认保存，组别保持control。复审结论：该P2关闭，无新增可确认问题。

## 独立执行

环境：Windows，仓库锁定uv环境，活动树bioimage-plan-sync。

1. `uv run --locked --no-sync pytest tools/wb/tests/test_bounded_background_context.py tools/wb/tests/test_project_analysis.py tools/wb/tests/test_intake_automatic_crop.py -q`：51 passed/5.89s，exit0。
2. `uv run --locked --no-sync pytest tools/wb/tests/test_prominent_band_geometry.py tools/wb/tests/test_prominent_crop_integration.py tools/wb/tests/test_common_band_geometry.py tools/wb/tests/test_anchored_context.py tools/wb/tests/test_anchored_analysis.py tools/wb/tests/test_normalization.py -q`：59 passed/6.09s，exit0。
3. 临时只读Python探针：seed1104，200个角度[-π/6,π/6]的旋转/平移膜区，150×150 valid随机孔洞及excluded标签各概率.003，origin(-20,-20)，target(x40:60,y50:70)，crop(x20:80,y45:75)。显式sin/cos逆投影、floor(v+.5)最近邻及界外拒绝逐像素求safe(y)，逐行扫描连续安全边界；与产品X/Y范围精确一致，200次通过exit0。非科学准确率实验。
4. 4dcd41e独立GUI复审：`uv run --locked --no-sync pytest tests/test_workbench_advanced.py::test_actual_web_forms_save_reopen_and_export -q`，offscreen、--disable-gpu、PYTHONUTF8=1；1 passed/8.42s，exit0。

未独立运行全量门禁、真实实验、学生试用或干净目标Windows；这些不由代码审查代替。后续产品/测试变动需复审相关结论。
