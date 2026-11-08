# P024 三工具首次练习交付

2026-11-09，[PR76](https://github.com/Junweiiii14/bioimage-tools-platform/pull/76) 已正常 squash 合并。base 为 d3733a7e1edae6e195d129c751a707e62b7fedea，受审提交为 9d684ebb7089150273ef8da1760d6a6153a29d1d，main 为 4d3c3fa7cb8df1a1ae00f7a7c2c34b392817626f。拉取远端 main 后与受审提交执行完整树 git diff，exit 0。

[本机练习 ZIP](../../../.local/p024-first-use.zip) 共 594408 字节，SHA256 为 73ccd34c0ed1dbb971241edf200c90ccbe58539f1188189a31f387e423944d2c。解压后打开 examples/first-use/README.md。仓库也可直接打开[练习说明](../../../examples/first-use/README.md)。在任意后续检出中复现 ZIP 时，把[归档命令](README.md)的 HEAD 替换为上述受审提交。可运行程序与外置核环境沿用[P023交付](../P-023/final-delivery.md)。

作者用实际候选运行时的独立实例完成三种练习的输入、计算、导出和冷重开。[作者证据](README.md)记录了 BCA 最后一步的离屏 Qt 选择框、前次用户中止和探针失败。三个项目重开前后156个已记录文件的摘要相同。指定[独审报告](independent/independent-review-9d684eb.md)判定 pass，报告中所引独审树 .local 下四份 JSON 已按原层次复制至 independent 目录。独审独立解压并核验17个文件、9处本地链接、样例再生成/来源和正式结果。

同一受审提交的四项必需检查均首轮通过。Linux foundation 17分28秒，Windows foundation 23分9秒，desktop-environment 25秒，rules-context 7秒。native-case 按既有条件跳过。[质量检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42502114722) · [规则检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42502114768)

工程走查完成。下一项需求可由用户协调一名学生，从解压的练习说明独立完成一次任务，用现有反馈栏记录第一处停顿、预期与实际，再据此决定是否有产品改动。真人试用和科学、干净 Windows 验收仍待相应材料。既有 N01 和 Linux 历史关闭 UNKNOWN 继续保留。

本地 codex/p024-closeout 仅收纳任务、证据和交接收尾，随下一正常任务带入。共享树释放后由上游另窗派发。
