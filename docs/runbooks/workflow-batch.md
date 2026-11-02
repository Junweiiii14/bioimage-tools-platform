# 有限批量工作流：5–10分钟操作

使用同一个工作流执行器顺序处理多样本。以下目录都选新的路径，已有原图、批次和成果不会被覆盖。

1. 运行一组明确标记的合成输入，同时保存可复用流程：

```powershell
uv run --locked --no-sync python -m bioimage_app --workflow-batch --workspace <第一批新目录> --validation triangle_u16 --validation triangle_u8 --template-out <新模板.json>
```

结果应为4000和40，来源为解析合成样例，不是独立科学准确率。最后一条JSON的`batch_id`用于重开，`samples`包含各样本状态、原因及已提交表/曲线/报告文件。进度只反映真实子执行，保存提交后才显示完成。

2. 使用模板绑定另一批原始输入，数值参数和真实图连接保留：

```powershell
uv run --locked --no-sync python -m bioimage_app --workflow-batch --workspace <第二批新目录> --validation triangle_u8 --template <模板.json>
```

模板会更新原图身份、图像元信息和请求源SHA。旧ROI/极性保持；图像尺寸变化不触发猜测或自动改坐标，越界仍报告invalid及空值。

3. 处理自己的文件：准备清单，文件路径相对于清单目录，也可用绝对路径。分析参数是已有AnalysisRequest JSON，不猜测泳道、ROI或样本关系。

```json
{
  "format": "wb_workflow_batch@1",
  "samples": [
    {"sample_id": "sample_A", "source": "A.tif", "parameters": "A-parameters.json"},
    {"sample_id": "sample_B", "source": "B.tif", "parameters": "B-parameters.json"}
  ]
}
```

```powershell
uv run --locked --no-sync python -m bioimage_app --workflow-batch --workspace <新目录> --manifest <清单.json>
```

使用`--template`时清单保留`sample_id`/`source`，移除`parameters`，数值配置来自模板。坏文件会保留失败项，其他样本继续；无效值、待复核与真实零分开，不能把有问题的批次当科学审核通过。

4. 重开与调整：

```powershell
uv run --locked --no-sync python -m bioimage_app --workflow-batch --workspace <已有目录> --resume <batch_id>
uv run --locked --no-sync python -m bioimage_app --workflow-batch --workspace <已有目录> --rerun <batch_id> --layout compact
uv run --locked --no-sync python -m bioimage_app --workflow-batch --workspace <已有目录> --rerun <batch_id> --template <修改参数后的模板.json>
```

重开已完成批次不重复计算；未完成子图按既有真实记录对账。调整创建新批次和子执行，保留旧记录；样式只重做发布，数值参数改变重算分析及后继节点。损坏缓存明确拒绝，其他独立样本继续；再次对该失败批次`--rerun`可复用完好的检查点并生成新分析资产，不覆盖坏的历史资产。输入从未成功冻结的失败项需重新提供输入清单。

退出码0表示全部完成；1表示完成但有问题或整批取消；2表示输入/持久化/成果核验失败。最终JSON的`state`、各样本状态和`reason`共同说明结果。磁盘故障不会作为普通坏样本忽略。

父控制器API支持整批暂停、继续、取消和安全关闭，重开默认等待继续；本CLI的`--resume`明确提交继续请求。可视操作面板和真实节点编辑由P009提供，当前操作单不宣称它已完成。

首版上限16样本、合计64节点/256连接、1MiB冻结计划；预算不是速度承诺。科学留出、用户体验、干净Windows、物理DPI/GPU等未验边界仍保留。
