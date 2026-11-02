# P003初次准确提交独审：Request changes

非作者p002_independent_review审查准确f2dc5ad44fba2e4f951b8987f0babb6b41c1d1a2..debeb3e034e7bfd9ba4cc9a3ca1bede6786c7153。产品结论Request changes；此前B011治理Accepted范围保留，不代替本产品审查。

1. P1，runtime evaluation.py原41–55：只闭包source_groups，未闭包共同父记录身份。root为unassigned/无groups，dev与hold有不同groups但同parent=root，分区检查返回空且实际评估engineering_passed/requested_use_allowed为true。相同采集派生物可跨分区被放行。
2. P2，wb_method_validation.py原102–129：忽略冻结design polarity/band_bounds/quant_policy。分别改dark、[1,3]、invented@9仍真实运行并五例报告通过，因实际用了fixture.request原参数。执行与声称冻结参考不一致。

独立实际命令：`uv run --locked --no-sync python -m pytest tests/test_method_validation.py -q --basetemp=.local/p003-independent-20261102-a`，exit0，13 passed/2.51秒。独立stdin反例脚本exit0成功复现两项；产物.local/p003-independent-extra-20261102。未修改产品/任务/证据。作者未跟踪冻结输出不在初次准确审查范围内。

修复：闭包增加带独立命名空间的record身份；严格核对原设计全部实际方法/参数/坐标字段，拒绝bool伪装整数。增加共同父/不同子标签/任意输入顺序的性质与实际评估拒绝反例，以及三字段修改/布尔坐标反例。先前debeb3e全门禁在pytest阶段由作者核实自身进程树后主动终止（exit1；不是产品自发失败），原因是已发现缺陷、须冻结新候选再验证；未将部分运行写成通过。旧冻结输出和execution.json均保留为该初次候选证据，最终接受须另新提交复审与全门禁。
