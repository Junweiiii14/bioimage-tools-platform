# P033 已提交核标签的目标通道强度导出

<!-- PROGRAM_TASK_META {"id":"P-033","status":"in_progress","work_package":"W14","depends_on":["P-016","P-032"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1bd6d-3ea8-7303-8448-27d9d1848f1b","base_commit":"fb6638eb7145dc9f0af61679a48aaef24a681606"} -->

继承 P032 收尾 d6de0df。通过正式 CLI 选择已提交核分割项目与同坐标目标通道原图，按原标签导出逐核原始强度。验收覆盖真实结果、官方固定标签参考、稀疏编号和零核。

Windows 本机以 P015 固定 worker 和模型对 ExampleHuman 的 AS_09125_050116030001_D03f00d0.tif 执行 nuclei_cli，再通过 nuclei_intensity_cli 配对 d1.tif。已提交 run 58a49b09055a41088bfee997c38bd08c 输出 233 行。运行 `uv run --locked --no-sync python work/evidence/P-033/verify.py <workspace> <d1.tif> <per-nucleus.csv>`，逐个掩膜核对 CSV，并用 P032 固定标签比较 289 组 PH3 编号、面积、均值和积分，全部精确相等，exit 0。两套标签来自不同分割方法。P015 历史 regression-03/valid-empty 运行同一导出入口得到仅有表头的 CSV 和核数 0 的出处。Windows 本机 tools/nuclei/tests 21 passed，ruff、定向 pyright 和 policy exit 0；未在作者机运行全量套件。
