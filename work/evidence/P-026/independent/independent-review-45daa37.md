# P026 最终增量复审

**pass，R01 关闭。** 2026-11-09，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`。GitHub PR 查询与远端分支均确认最终 head 为 `45daa37cfc42e11103597acb4ad0a2b7452a6d48`，PR base 为 `e846a681c85e04d53904fe8b6b384376e98f6032`。[PR78](https://github.com/Junweiiii14/bioimage-tools-platform/pull/78)

相对原审 `44a6109da485f6b0085ee81ede5420dd294f2418`，唯一差异是新增 P026 集成清单。清单准确登记上列 base、原审 source_head 和 P025 历史回执来源。直接读取 Git 对象逐字节核对如下。

| 回执 | 来源提交 | 源文件与最终文件共同的 SHA256 |
|---|---|---|
| P025 收尾 | `94f47be998f5e904a797df922d2a1a8844816fa4` | `538476710d9526b1780cea323198b65c8c5468d65bde451f7057e81cd7f489d7` |
| P026 当前 | `44a6109da485f6b0085ee81ede5420dd294f2418` | `f1ed32205017267fb1a4c7f5431caea354a2109985d3af23e31246509f753865` |

针对准确 base/head 执行 `python -B -m tooling.rule_context check` 与 `git diff --check` 均为 exit 0。逐字节核对记录见 `.local/governance/recheck-45daa37.json`。

研究报告与探针均沿用原审内容。IOCBIO 的实测结论限于 gel1 的单张 TIFF、固定参数和 suggest_crops 入口，停在膜定位。Butler S2 提供 11 档上样量、3 张膜的作者测量，缺逐膜逐曝光的原图匹配。Clegg 排除结论限于所查版本、首 IFD 与定量表。科学准确率仍待独立配对材料。[原审回执](independent-review-44a6109.md)
