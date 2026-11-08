# P026 研究交付

[研究记录](../../../docs/research/2026-11-09-wb-public-reference.md)及[复现探针](probe.py)。独审另核 IOCBIO 像素与直接解码逐点相同；该配置未定位膜、没有积分，不能授予 S1。Butler S2 可验稀释表，缺按膜、泳道和曝光对应的原始像素；已见膜只作探索。未改变算法、阈值、产品或学校试用状态。

[PR78](https://github.com/Junweiiii14/bioimage-tools-platform/pull/78) 正常 squash 合入 main 8321615773c73ede412e1a60b2688e545f537f8a，与最终受审 45daa37cfc42e11103597acb4ad0a2b7452a6d48 完整树比较 exit 0。最初候选 44a6109 的研究事实通过，但[首审](independent/independent-review-44a6109.md)和首轮 rules-context 均发现 P025 历史回执缺少集成清单；只新增清单后，[固定增量独审](independent/independent-review-45daa37.md)通过。原始检查失败留存，不更改历史回执。

最终候选的四项必需 CI 全绿：[规则](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42508026511)、[Linux/Windows 基础及桌面环境](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42508026513)。开发机未重复完整科学矩阵；旧 P010 全局计划检查缺项继续保留。独审回执归档于 independent，只含报告、哈希、标签与测量摘要，不含原图/作者表格。一次本地收尾随下个正常任务带入。
