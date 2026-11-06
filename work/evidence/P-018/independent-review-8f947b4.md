# P018 指定独立审查

审查者：审查窗口 `01a1af0d-808e-7131-ae29-237aded27938`，2026-11-06。结论：**pass（研究内容范围）；集成尚未就绪**。没有产品或科学准入结论。

- 基线：`f8f69b51e01446ffed6301dec99d2cf28fcdb85c`。
- 候选：`8f947b4e67fbf53bcd926b37a1a2f56b8e5343ea`。
- P018独有增量：`0d134926ecb8b2ecd0f1692847d067f8dc123fbe..candidate`；P017收尾另已审查。
- 独立检出：`bioimage-review-p018`，未切换或修改开发树，tracked状态干净。
- 范围：固定BCA研究方法、最小输入输出候选、147行合成API探针及结果、来源解释、登记与交接。没有承诺本轮实现任意CSV解析器或产品工具。

## 发现与结论

研究内容没有阻断发现。数值候选和化学方法证据界限清楚；25–2000 µg/mL为收窄的研究支持范围，未伪称已验证LoQ。逐技术孔反算再乘明确预稀释倍数，未乘工作液体积比例；技术重复不称生物重复。区间外与低范围留空并保留原因，不以零冒充结果。直接调用已锁NumPy公开API，没有新增求解器、依赖或过度包装，也没有改动第三方本体。

**待完成的集成项**：准确基线/候选执行 `python -m tooling.rule_context check --base f8f69b51e01446ffed6301dec99d2cf28fcdb85c --head 8f947b4e67fbf53bcd926b37a1a2f56b8e5343ea`，exit 1：`Integration must list every extra historical receipt exactly`。这是P017历史回执祖先与P018当前回执的集成清单问题，不是数值失败。已报告上游；PR69合入后须按实际main/diff重载并正确记录历史来源，准确检查成功且必需CI完成后才具备正常集成条件。不得删除回执或改变门禁来消除失败。后续仅规则/文档变化可做增量核对，不重复整个数值研究。

## 主审独立执行

环境：Windows，Python3.12.14，已有锁定开发环境NumPy2.5.4；`UV_PROJECT_ENVIRONMENT`指向现有开发venv，`--locked --no-sync`，没有安装依赖。

1. `uv run --locked --no-sync python work/evidence/P-018/run_probe.py .local/reviewer-reproduce` exit 0，实际生成三份结果。
2. 独立以Decimal 50位精度从已提交原始合成CSV读取23孔、9标准水平和空白均值0.050；不用NumPy作为验算器。逐段手算逆值、稀释、均值及ddof=1标准差。S1均值为5008.6805555555555067 µg/mL，SD为208.6947097251962489 µg/mL；单孔原浓度最大差约1.12e-13 µg/mL，低于原先声明1e-10容差。原CSV的浮点表示也纳入高精度复算，没有先改写输入以匹配期望。
3. 两份CSV按单元格、JSON按解析值与候选结果一致；LOW/HIGH/NEGATIVE浓度单元格确实为空，状态符合方法。
4. 对同输出目录再次执行，exit 1/FileExistsError，已有三文件SHA256前后不变。
5. `git diff --check 0d134926..8f947b4` exit 0。规则清单检查失败如上完整保留；未将作者自验替代独审，也没有因检查失败修改预期。

独立数值收据：`reviewer-independent-check.json`；重复目录的原错误日志保存在审查树`.local/reviewer-existing-output.stderr.txt`。

## 来源与代码专项交叉核对

由主审委派的只读子审对准确候选交叉核对；主审另直接核NumPy官方接口。重新下载[厂家指南](https://assets.thermofisher.com/TFS-Assets/LSG/manuals/MAN0011430_Pierce_BCA_Protein_Asy_UG.pdf)并查看p2/p3渲染，SHA256为`349774e9e05c3c972ab79369c061c0faff57c215aa2352dd9da5ac4748a51acf`，与候选相同。25/200 µL、50:1、混匀30秒、37℃30分钟、冷却室温562nm、零标准空白与九个标准水平吻合。含糊的“四参数（quadratic）”没有被擅自解释；软件逐点分段被明确标为项目研究选择。

核对[论文出版商正文](https://link.springer.com/article/10.1007/s00216-022-03910-1)及[全部9页补充材料](https://static-content.springer.com/esm/art%3A10.1007%2Fs00216-022-03910-1/MediaObjects/216_2022_3910_MOESM1_ESM.pdf)的渲染：条件吻合，未发现完整BCA逐孔校准表/板布局，未从图估值。附件SHA256为`c8745f5157044e2c7ecb70854f7d2b89e5ca27c05674483bc8ae15793321fa47`；本机缺pdftotext时以逐页渲染核验，不冒称文本命令成功。[Mendeley条目](https://data.mendeley.com/datasets/7t5ck67w65/1)元信息与候选说明一致，原表没有下载/验算，也没有被当作匹配参考。

[NumPy 2.5 interp](https://numpy.org/doc/2.5/reference/generated/numpy.interp.html)确认默认端点钳制及不自动强制递增，候选显式左右NaN和真实入口单调检查合理。README已明确边界单孔不是合格完整样本、没有CSV解析/元信息验证，未将探针冒称正式适配。registry仅新增P018任务及W07引用；产品、锁、门禁及P017研究算法/结果无变化。

## 未验与复审触发

未运行湿实验、同SOP真实完整板、独立化学真值、LoD/LoQ、真人需求、CSV解析器、产品GUI、安装/目标机或全量产品本地检查；P018必需CI尚未完成。厂家/论文条件吻合与合成数值正确不能转授科学有效性。资料缺项只限制相应结论，不阻塞无关统一UI。

本结论只绑定上述候选。后续方法、脚本、输入、预期/容差或科学声明变化需复审受影响部分；仅合main/记录来源的变化做准确增量核对。正式集成由上游安排，本审查没有直接合并P018。
