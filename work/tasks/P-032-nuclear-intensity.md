# P032 固定核实例的双通道强度复验

<!-- PROGRAM_TASK_META {"id":"P-032","status":"in_review","head_commit":"cf91bc59b6708316664af78bae61fa8b0e1f347d","work_package":"W14","depends_on":["P-014"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1bd2b-0eda-7b30-b5fc-15bad4c72d7f","base_commit":"b7ac508a79f31d95c5fc22a715f04d7c1c81cff5"} -->

继承 P031 收尾 2a7e023。固定 ExampleHuman 全视野、全部 Nuclei 对象，按对象 ID 核对原图 DNA/PH3 的面积、均值、积分；记录样本归属、位深、标度、饱和与背景限制，决定 MVP 范围。像素面积精确相等，归一化强度按原始整数恢复误差与 CP 浮点精度核查。验收以可回放结果、独审与 CI 为据。

[结果与回放](../../docs/research/2026-11-09-nuclear-intensity.md)。Windows 本机两次最终脚本回放 exit 0，逐核表、标签 TIFF、摘要逐字节一致；ruff check、policy、handoff 容量 exit 0。计划检查 exit 1，首报历史 P010 缺 reviewed commit，沿用 P031 已记录的基线。全量测试交既有 CI；独审与集成待回传。
