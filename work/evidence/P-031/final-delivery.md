# P031 研究交付

[研究与排期判断](../../../docs/research/2026-11-09-clonogenic-count.md) · [三瓶复验](README.md) · [固定独审](independent/independent-review-9d9c31d.md)。三瓶均少计；C2 两个显微中心被计为一个。暂缓按此默认方法进入自动计数 MVP。0412 是共同文件名前缀，生物批次关系未知。三瓶缺少可配对的实验记录，未计算 PE、SF 或组间差异。

[PR82](https://github.com/Junweiiii14/bioimage-tools-platform/pull/82) 于北京时间 2026-11-09 05:56:27 正常 squash 合并。基线 3b8de00eaa14901ababf129f5a110e1b0a8e7a8c，研究提交 bef2475d959067535457c793ab8e3ae438bfc8e3，最终受审提交 9d9c31dd4457f0e175c627c6a9c230e3effe4c62，主线 b7ac508a79f31d95c5fc22a715f04d7c1c81cff5；合并后 git diff --exit-code 核对同树，exit 0。

初版 e50e740 遗漏两份回执并存时的显式集成清单，规则 CI 失败，旧质量运行由后继提交取消。按既有集成命令保留 P030 收尾的原始回执并增加来源绑定后，固定独审 R01 关闭。最终提交的 rules-context 5s、desktop-environment 35s、Ubuntu 18m26s、Windows 27m59s 全部通过，native-case 条件跳过。未在作者机重复全量产品测试。基线与最终候选的历史计划检查均 exit 1 首报 P010，缺有效受审 SHA 的集合 P010、P021、P022、P023 相同。[质量检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42525299937) · [规则检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42525300010)

P030 一次收尾已随本 PR 入主线。P031 独审报告及其引用的四份回执、最终任务卡与恢复指针在一次本地收尾中随下一项携带。后续若再验证计数，先落实本地 SOP、疑难整皿标点、配对实验记录及学生实操。
