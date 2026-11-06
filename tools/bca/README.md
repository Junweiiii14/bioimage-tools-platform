# 单板BCA研究适配

公开API `bca_tool.api`：`read_plate(csv, record)`严格解析一次；`analyze_plate(validated.wells)`接受已验证的不可变孔记录，返回逐孔和技术样本结果。领域不做I/O，适配层产生候选文件；宿主沿用WorkflowSession/Workspace完成真实worker、取消、事务提交及重开。内部不重复猜测实验事实。

方法仅为[P018契约](../../docs/research/2026-11-06-bca-method-contract.md) `pierce25-point-v0-research`，API/包版本0.1.1、出处schema版本1。旧P017研究结果不迁移、不重算。固定25/200 µL、37℃30分钟、562 nm、零BSA空白、固定9个标准水平；每个水平与样本至少2技术孔。逐孔扣空白→NumPy2.5.4 interp→明确预稀释→技术均值/SD；禁止外推、工作液倍数、离群移除、生物n或自动择模。

## 从CSV运行与重开

仓库根先执行 `uv sync --locked --all-groups`，无需新环境或模型。使用**全新**工作区：

```powershell
uv run --locked --no-sync python -m bioimage_app.bca_cli --workspace .local/my-bca --source tools/bca/examples/synthetic.csv --record tools/bca/examples/record.json
uv run --locked --no-sync python -m bioimage_app.bca_cli --workspace .local/my-bca --reopen <上条输出的execution_id>
```

末行`phase=finished,state=succeeded`表示计算及存储完成，`outputs`提供已提交逐孔CSV、样本CSV和出处JSON的绝对路径；不是科学验收。CSV含方法/API版本、原身份、技术n与status/reason。重开校验已有资产，不重新计算；重复使用已有目录开始新分析会拒绝。Ctrl+C请求取消，等finished后再操作工作区。失败/取消返回非零且不列成果路径。默认60秒期限只约束执行链，不是方法参数。

`examples`是非私有透明合成数据：保留P018全部原始23孔值，给LOW/HIGH/NEGATIVE补第2技术孔并加partial样本，以满足本次入口要求；不改P018冻结参考。S1均值应为5008.680555555556 µg/mL、SD为208.69470972519616；另4个样本partial汇总为空。

真实输入必须按示例CSV列顺序填写，孔号A1–H12唯一、仅一板、身份/技术重复显式；原吸光度不得已扣背景或自动换算。JSON字段均必填，无默认实验确认；同稀释液/同处理、冷却和基质兼容依据由输入者明确声明，软件不验证实验真实性。`source_sha256`绑定CSV实际字节（可用PowerShell `Get-FileHash -Algorithm SHA256`，填小写摘要）。日期使用ISO格式。未知必要记录不能直接套用合成例或将其当成已确认。

样本支持25–2000 µg/mL（稀释前被测溶液），低/高范围逐孔空值；任一技术孔受限，整个样本汇总留空并标partial，保留有效单孔。标准/空白的浓度输出not_applicable，保留标准均值/残差。空值不是0；LoD/LoQ未知，不把厂家范围当LoQ。CSV和JSON均不覆盖原表/历史；结果留在Workspace，其发布由宿主负责。

没有同SOP真实逐孔化学参考、LoQ、学生/真人或安装态验收。这里只提供源码研究CLI，未做GUI、所有板格式、自动拟合、统计/批处理或安装发布。当前一个真实模块节点覆盖本方法计算；逐步骤自由节点编排和可卸载GUI未在本轮承诺。

0.1.1修复P019独审R01/R02：结果返回前通过Workspace核验运行/请求/清单及实际输入输出摘要，损坏/缺失返回失败且不修补历史。标准均值采用P018探针的原读数均值减空白；仅在25和2000端点将原读数与端点均值相差不超过两者最大ULP的2倍视为机器等价，交给同一interp反算。它不是科学容差或全域端点钳制，真正越界仍空值。固定方法ID与LoQ未知不变；包/API及implementation digest标明修正，已有0.1.0成果可核验读取而不会被重新计算覆盖。

P020 后继源码新增桌面最小流程，见 [统一工作台操作](../../docs/runbooks/unified-workbench.md)；上述“未做GUI”描述 P019 当时交付，不表示当前源码仍无入口。方法/API 0.1.1 未变，科学与安装边界保留。
