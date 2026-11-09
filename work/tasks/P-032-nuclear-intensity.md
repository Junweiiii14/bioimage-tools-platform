# P032 固定核实例的双通道强度复验

<!-- PROGRAM_TASK_META {"id":"P-032","status":"done","head_commit":"791f4e056c1a20ca4aa951e501acc52ff0a41a13","work_package":"W14","depends_on":["P-014"],"execution_root":"C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-plan-sync","owner":"chat-01a1bd2b-0eda-7b30-b5fc-15bad4c72d7f","base_commit":"b7ac508a79f31d95c5fc22a715f04d7c1c81cff5"} -->

继承 P031 收尾 2a7e023。固定 ExampleHuman 全视野、全部 Nuclei 对象，按对象 ID 核对原图 DNA/PH3 的面积、均值、积分；记录样本归属、位深、标度、饱和与背景限制，决定 MVP 范围。像素面积精确相等，归一化强度按原始整数恢复误差与 CP 浮点精度核查。验收以可回放结果、独审与 CI 为据。

[结果与回放](../../docs/research/2026-11-09-nuclear-intensity.md)。Windows 本机两次最终脚本回放 exit 0，逐核表、标签 TIFF、摘要逐字节一致；ruff check、policy、handoff 容量 exit 0。计划检查 exit 1，首报历史 P010 缺 reviewed commit，沿用 P031 已记录的基线。作者机未跑全量。

[固定独审 PASS](../evidence/P-032/independent/independent-review-791f4e0.md) 绑定 791f4e056c1a20ca4aa951e501acc52ff0a41a13，含官方原管线新运行、整数逐像素复算和单 DN 积分负例。研究实现 cf91bc5；初版规则检查因缺历史回执清单失败，d78e57c 补来源，791f4e0 绑定任务卡。北京时间 2026-11-09 07:08:58 [PR83](https://github.com/Junweiiii14/bioimage-tools-platform/pull/83) squash 至 main fb6638eb7145dc9f0af61679a48aaef24a681606，git diff --exit-code 核对已审树 exit 0。最终规则 7s、桌面环境 28s、Ubuntu 17m55s、Windows 重跑 28m45s 均 pass，native-case 条件跳过。

[Windows 首轮](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42528647742/job/128877788389) 在 pause_adjust 等待暂停状态时停住，诊断捕获存储线程读取工作流账本，作业达 30 分钟时限；根因 UNKNOWN。作者机同一提交离屏运行该 pytest 节点 1 passed in 8.16s，[同 SHA 单作业重跑](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42528647742/job/128885898509) 通过。既有检查、时间限制和产品代码均未调整。共享树一次本地收尾交回上游。
