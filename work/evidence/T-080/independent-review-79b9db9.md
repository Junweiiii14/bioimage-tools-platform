# T080 CI 修复提交独立审查

Verdict: **Accepted（源码增量审查）**

- Exact HEAD: `79b9db9b7ae055bc3354a3582777082729ca8110`
- 增量基线：`f363f37ab86012afa19e7e83eb4a158137bf9e00`；此前产品审查见 independent-review-be0d0fa.md。
- 独立审查者：`/root/t080_final_review`，没有参与产品或测试实现。2026-10-23，Windows / locked uv；开始时 HEAD 已核对且工作树干净。

完整 CI 先前失败是有效反证，旧 Accepted 不能代替修复验收。本次独立检查冻结增量及科学预期分类，未发现仍需阻断此提交的确定缺陷。

算法修复限制按膜宽误合并明显核心、拒绝为达到 N 而合并深谷分隔的明显峰，保留强第三带/tall/doublet/guide mark 的否定断言。较宽成员容差与 marker 至少三脊是工程策略，不是生物学身份证明。作者真实来源有界回放21/21属于开发素材影响检查，不证明80%独立项目泛化。

公共API测试从“任何N外结构皆阻断”迁移至批准的明显主行策略：新增 assert_prominent_row 校验每个明显主带的完整原图坐标、固定N、未审核、新policy和输入像素保持；不是只翻转布尔断言。显式N=3测试仍要求三槽并在自动采纳时覆盖末槽。旧domain拒绝语义未修改；明显额外强样本仍拒绝。另一行干扰允许时必须覆盖真正主行，不能用斜混排通过。

伙伴偏移与重复行不再阻断独立有效的所选来源，但仍禁止生成注册标志；组SHA篡改拒绝与序列化重开断言保留。新增真实 materialize 反例核实3个原图SHA全部保留、仅1个所选原值裁图、两个伙伴记录“未生成”，补上本代理要求的最小集成证据。

文件名兼容修复保留CSV/XLSX内容和样式、旧ZIP不覆盖断言；公开schema补sampling_policy与已批准契约一致，旧ROI错误消息恢复未降低边界。Linux UI等待是有界等待真实动画结束，原精确几何断言保留；注释明确原失败具体原因尚未证明，没有伪称根因已修。

本代理在冻结提交运行：

`uv run --locked --no-sync pytest tools/wb/tests/test_intake_delivery.py -k unregistered_common tools/wb/tests/test_reliable_geometry_exclusions.py -q --tb=short`

实际exit0，**1 passed, 13 deselected in 1.73s**。`-k`同时过滤所有列入文件，因此不把该次运行称为exclusions全文件通过。其余71项为作者记录，本代理没有重复Qt或全仓测试。

此结论覆盖源码及测试语义增量，允许继续新准确HEAD的GitHub必需检查。CI、PR合入、新包构建和安装验收仍须独立真实证据；本报告不宣布这些步骤通过。后续产品变化需重新审查。
