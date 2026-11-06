# P017 审查与验证

- 初始基线：P016候选16d32b1与main6bd4680树一致；保留ac10a07收尾，合并main产生的8个交接冲突全部核为squash历史冲突，恢复较新收尾后合并00becc8。无产品差异。首次git commit缺pre-commit失败，uv run git commit钩子正常通过，无绕过。
- 预声明8098d0b、来源/环境冻结68bed12先于拟合。上游B020规划e4209e9在共享树独立指定路径提交，已完整保留，当前任务集成清单需包含B020历史回执。
- run1退出1（退化输入返回NaN而非抛错）；run2退出0，数值容差未变。首次ruff格式检查有行长/未用变量问题，随后正常格式修正，不加忽略。
- 原始下载只在.local，未改产品依赖/门禁/已有测试。R全脚本、科学真值、真人试用、目标机均未验。
- 指定独审窗口01a1af0d-808e-7131-ae29-237aded27938对bcf57ce正式pass（仅研究/规划，无阻断）；原文见[independent-review-bcf57ce](independent-review-bcf57ce.md)，[独立数值/来源/环境核验](reviewer-independent-check.json)和[不覆盖反例](reviewer-existing-output-check.json)逐字节复制，署名及对象未改。唯一P3在现行报告补注FPCountR基线可选，历史预声明不改。
- 原候选PR68 rules-context/desktop通过，双平台foundation在收据提交前仍运行，不能作为后续HEAD通过证据。此次仅收据/补注/交接增量，待指定窗口增量确认和新HEAD必需CI，不自合并。

- 格式后run3退出0，4份CSV与run2逐字节一致（0.1206秒、不含导入）。ruff最终通过。dev.py policy与git diff --check通过；handoff容量维护先归档1段，硬限制无问题。check_plan.py退出1：既存P010 done但head_commit=null；main同样如此，不修改历史状态冒充通过。P017依赖P013/P016均done已核。

- 先前子代理只读审查同一bcf57ce无P1/P2，现作为补充，不替代指定窗口独审。作者另测独立研究环境文件逻辑大小291.29MiB（含绘图与对照库，非产品增量/物理占用/峰值内存）。未追加全量本地产品测试。
