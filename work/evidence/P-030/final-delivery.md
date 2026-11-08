# P030 划痕闭合研究交付

[研究、四帧轮廓与复验步骤](../../../docs/research/2026-11-09-scratch-closure.md)建议保留候选、暂缓全自动 MVP。12/24 h 出现方向相反的结果。单孔、单名义视野无法验证物理重叠、独立生物重复、真人节时或采用意愿。重新排期条件见研究末段。

[固定独审](independent/independent-review-5228adf.md)通过。独立核验采集表、ZIP 成员与分类，重放 ImageJ，再以另一种多边形填充核对方向。非阻断 N01：像素计数为整数，CSV 闭合率与差值按三位小数舍入、IoU 按四位舍入；不保证显示尾零。四帧都是研究用已见训练素材，val/test 图与标签未打开。

[PR81](https://github.com/Junweiiii14/bioimage-tools-platform/pull/81) 于北京时间 2026-11-09 05:12 正常 squash 合并。base 0b0c4c532add70dfb1f3a36cd8cc8a53e9f84a77，研究提交 03a02057da3813fc9005333e0a5f96d0212b187c，受审 head 5228adf0ea23de3b78c7f70fedab1b1f7239f4d3，main 3b8de00eaa14901ababf129f5a110e1b0a8e7a8c。两者 git diff --exit-code 为 0。必需 CI 首轮通过：Ubuntu 16m36s、Windows 17m10s、desktop-environment 31s、rules-context 6s；native-case 条件跳过。[质量检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42522433838) · [规则检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42522433840)

P029 本地收尾已随 PR81 进入 main。P030 一次本地收尾及规则重载随后续正常任务携带。历史计划检查在基线及候选均首报 P010，未改旧任务卡。
