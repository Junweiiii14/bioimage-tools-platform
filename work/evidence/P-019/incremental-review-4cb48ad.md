# P019 R1 指定增量复审：pass

2026-11-06，审查窗口`01a1af0d-808e-7131-ae29-237aded27938`。**准确候选的工程MVP增量复审通过，P019-R01与P019-R02均关闭；未发现新的阻断。** 完整必需CI仍由上游跟踪，不能把本结论改写为已合入、科学准入或用户安装更新。

- PR：https://github.com/Junweiiii14/bioimage-tools-platform/pull/71
- PR base：`3947261244143e3414b9bbf151bbe77c6edb5991`
- Reviewed candidate：`4cb48ad51dc71f5e4b36195e3caa1356507665b0`
- 本次增量：`0a73a4d2753ddee0a94a172110b5102b9b39bfab..candidate`
- 独立检出：`bioimage-review-p019`，detached；tracked干净，开发树、作者结果和旧审查证据未改。

## R01 关闭：真实资产核验及成功宣告顺序

`bca_cli.py:55`的新函数复用Workspace/get_run/read_asset/asset_path和公开validate_workflow_result_selection，验证运行、请求、清单及实际输入输出。WorkflowSession释放原存储后才执行，不新增引擎或修改共享执行链；校验失败只改变本次CLI响应，不修复或重算历史。

主审用专属venv、`python -I`实际重放上一轮保存的原反例，未重新构造更容易通过的替代数据：

| 独立场景 | 退出码与结果 |
|---|---|
| 原0.1.0正常工作区重开 | 0 / succeeded / pid=null，全部既有资产摘要不变 |
| 原R01数值被改为999999的工作区重开 | 2 / failed / result_integrity，outputs为空，pid=null，损坏文件也保持原样 |
| 复制正常旧工作区并移除其中一个成果文件后重开 | 2 / failed，outputs为空，pid=null，没有重新生成缺失文件，其他资产不变 |
| 新0.1.1真实CLI执行→提交 | 0 / succeeded，正确新API/包版本，正常数值及partial语义保留 |
| 新0.1.1成果重开 | 0 / succeeded / pid=null，已提交资产摘要不变 |

逐条捕获全部JSON消息：正常重开依次preparing→verifying→最终succeeded；损坏/缺失依次preparing→verifying→最终failed。所有场景在最终完成之前均无succeeded消息，失败场景从未输出成功路径。旧0.1.0读取没有调用当前计算，历史版本未被重新解释或覆盖。

证据：`.local/r1-review-4f81fd5b/r1-integrity-results.json`及五场景stdout/stderr。源码调用链另经只读子审交叉核对，结论与实测一致。

## R02 关闭：只处理机器舍入等价端点

标准计算采用mean(raw)-blank，与P018探针一致。`plate.py:75`的等价处理只位于25/2000两个端点，范围为原读数与该端点均值最大ULP的2倍；其余值继续交给同一NumPy interp，没有科学容差、全域钳制、模型替换或新依赖。

数值专项子审在本独立树实际重放上一轮两组原CSV：结果为精确25/2000 µg/mL，S1有效孔数恢复2、汇总research_estimate。另14个有界端点检查全部通过：2 ULP外侧按声明视为机器等价；3 ULP、1e-12及0.001外侧仍为范围外/null；内侧1e-12/0.001继续真实插值。真实超范围没有被广泛拉回有效结果。主审定向pytest同时执行了这两项原始反例及越界回归。

证据：`.local/plugin-review-p019/probe_r1_bounds.py`及`r1-boundary-results.json`。旧反例、旧日志及作者输出均未改。

## 验证、范围和版本

- 本审查树`uv sync --locked --all-groups --offline` exit0，仅将本地BCA元数据0.1.0更新为0.1.1；共享环境未动。Python3.12.14/NumPy2.5.4，所有执行来自独立检出。
- `pytest tools/bca/tests tests/test_bca_host.py tests/test_import_contracts.py -q`：**38 passed / 9.77s / exit0**。Qt使用offscreen及--disable-gpu，与首轮一致；未弱化旧预期或跳过用例。
- 新正常执行的S1均值/SD保持5008.680555555556/208.69470972519616 µg/mL（原软件容差1e-10），另4个样本仍partial且汇总为空。新输出包/API/module_version为0.1.1、schema1、method_id及LoQ未知不变。
- 主审实际构建并独立安装0.1.1 BCA wheel，CSV/API数值、worker hello、安装来源及无Qt/runtime/其他工具/SciPy检查exit0；明确检查安装的包和模块版本0.1.1。压缩wheel11756 bytes，不冒充完整依赖或运行内存指标。
- 78个第三方锁对象逐项完全不变；只有本地BCA版本更新。P018冻结方法/探针/参考、原0.1.0执行/结果、worker/protocol/宿主装配、共享存储、边界及CI实现均无变化，可沿用上一轮对应证据。包/API及implementation digest显式标识修正，不迁移旧结果。
- 已提交的原changes_required报告与主审更正版原文在Git换行归一化后完全一致，包含之前diff检查收据更正，没有改署名或把旧发现改成旧版通过。
- 准确PR base/candidate的rule_context check **exit0**。增量git diff --check **exit2**，仅新results-r1两份CSV的受保护CRLF告警，逐行字节核验没有其他尾随空格/tab；原日志`.local/diff-check-r1.txt`。没有通过改门禁/配置或字节摘要消除告警。
- GitHub查询时PR71 base/head与本报告一致，rules-context及desktop-environment成功，双平台quality仍在运行。此处不提前宣告最终CI成功。

## 回传及未验

保持准确候选不变，必需CI全部成功后由上游安排正常合入并核对main与已审内容。若相关文件再变，仅复审受影响增量；不为这份收据重复推送或启动无关整改。

没有重复未变研究、全部本地产品测试、全部既有wheel/GUI、完整卸载矩阵；原作者全量canvas失败记录保持原样。未验同SOP真实化学板、独立真值、LoD/LoQ、真人或安装/目标机。工程MVP通过不替代这些结论。本审查没有代签合并。
