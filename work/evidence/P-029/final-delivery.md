# P029 研究交付

[研究与复现](../../../docs/research/2026-11-09-qpcr-relative.md)建议保留候选、暂缓开发。没有实地需求、购买意愿或独立生物学真值。用户协调一批获准使用的真实导出、板图和现用结果后再评估。

[指定独审](independent/independent-review-506c968.md)通过，另以 Decimal 从 OOXML 复算 12 个样本。非阻断 N01：未来由实验负责人签认的 SOP 须明确效率汇总层级；相同表头与六对照校准下，Treatment 3 按每基因 36 个效率均值得 1.56268，改为每样本三个技术孔均值得 0.94166。不能由模板推断用户采用哪种定义。

[PR80](https://github.com/Junweiiii14/bioimage-tools-platform/pull/80) 已正常 squash 合并。base 3103063d1abf116ef1d98694b9cc57f4dc70ae22，研究提交 69376e4e078928842988a889577021c5bc28969c，受审 head 506c96881c2e748ab9c2c1bb513a01914387f952；main 0b0c4c532add70dfb1f3a36cd8cc8a53e9f84a77 与受审 head 的 git diff --exit-code 为 0。四项必需 CI 首轮通过，Ubuntu 18m25s、Windows 27m39s、desktop-environment 31s、rules-context 6s，native-case 条件跳过。[质量检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42519025804) · [规则检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42519025803)

P027/P028 历史记录随 PR80 进入 main。本地计划检查的旧卡 head 缺项保留，基线与最终候选均 exit 1；详细集合见独审。本地一次收尾后释放共享树，收尾回执随后续正常任务携带。
