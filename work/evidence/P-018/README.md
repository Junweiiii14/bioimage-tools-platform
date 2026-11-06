# P018 最小API探针与证据

[方法、来源和输入输出契约候选](../../../docs/research/2026-11-06-bca-method-contract.md)。研究脚本不等于产品解析器，合成例不等于化学参考。算法仅调用公开`numpy.interp`；预声明在24373f1，未改变容差或预期使检查通过。

## 重现

在本仓库已锁开发环境运行，不需新增依赖；Python3.12.14、NumPy2.5.4、Windows11。只需Python+NumPy；没有模型/worker环境/新增正式依赖。本轮不量测产品体量、性能或峰值内存。

```powershell
uv run --locked --no-sync python work/evidence/P-018/run_probe.py .local/p018-new-output
```

输出目录必须不存在。脚本生成23孔透明合成CSV（18标准/空白孔、5样本孔），样本逐孔CSV与JSON数值收据；它没有读取任意CSV或验证板级元信息的功能。入口全规则及完整逐孔/样本CSV产品输出留下一任务。本例S1为两技术孔，其余单孔仅验证数值边界，不是可准入的完整样本；契约的每样本≥2孔规则尚未实现。

[原始合成输入](results/synthetic-input.csv)、[样本孔输出](results/sample-wells.csv)、[结果](results/result.json)。标准数组为手写分段点，空白0.049/0.051，非真实测量。中点/端点、空白均值、10倍稀释和跨拐点汇总的期望独立手算；abs/rel容差1e-10只约束双精度软件复现。0、25、2000为插值API端点检验，零值不是本候选支持的未知样本定量。

## 实际检查

2026-11-06，探针首次运行及独立新目录重跑均exit0；JSON/CSV字节相同。非有限读数、平坦/倒序标准明确ValueError。相同输出目录重跑exit1/FileExistsError，原文件摘要未变。没有改变第三方算法、数据、容差、锁或门禁。

开发步骤另有两个非实验失败：首次提交因未将现有.venv/Scripts加入PATH找不到pre-commit，补PATH后正常hooks通过；编辑registry辅助脚本默认GBK解码失败，未写registry，显式UTF-8后成功。不是依赖安装/算法失败，不隐去。

厂家PDF本地下载并使用Poppler渲染第3页，确认微孔板步骤/模型注释与图2试管图注。只保存链接和SHA256，不重新分发PDF。论文补充材料已读取全部9页提取文本，未发现本轮所需逐孔板表；未对其图表做数值提取。未运行湿实验、真实完整BCA数据、学生操作、目标机、产品GUI或产品全量本地测试；无产品变更，远端必需CI仍须完成。

独审/CI/准确提交收据在[验收记录](validation.md)；本文件不提前宣称集成完成。
