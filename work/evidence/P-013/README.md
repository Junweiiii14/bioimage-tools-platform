# P013 探针与验收收据

状态：研究探针完成，PR/必需 CI/最终回传待完成。当前源码基线 cddf5ae；正式候选提交在任务卡收尾记录。Windows 11、Python3.12.14，CPU 单进程；未运行 GPU 或模型。

## 复现

在仓库根创建隔离环境，不改变产品依赖：

```powershell
uv venv .local/p013-venv --python 3.12
uv pip install --python .local/p013-venv/Scripts/python.exe -r work/evidence/P-013/requirements.txt
.local/p013-venv/Scripts/python.exe work/evidence/P-013/probe.py ../p013-research-data ../p013-research-data/reproduction-new
```

从 download-manifest.json 中三个官方 URL 下载归档到仓库外 p013-research-data，逐一核对 SHA256。数据明确 CC0，使用引用见主研究说明。脚本只读取 ZIP 的明确目录，不解压归档，不执行里面的任何代码；输出目录必须新建，否则拒绝覆盖。文件名分组来自官方 metadata/test.txt 和 validation.txt；不从 treatment 名猜生物重复。

`report.json` 是 run-03 实际环境、输入摘要、选图及结果；`metrics.csv` 是完整逐图结果。逐核 intensities.csv 在仓库外 run-02/run-03 保留，复现命令可重建。两个成功运行 metrics.csv 的 SHA256 均为 d9de1291e5fc8788c7f5b73783d4a8fdabee93bfc62c40af723abdb72dec6ac0；intensities.csv 均为 5b142f039ae9f8ffd6ad66272df9efbb18a65dbe22bd45d8593c3f7af6bd5b5b。report 含计时因此不要求逐字节一致。

`failure-example.png` 是 test 最大相对计数误差图（A12_s7），三栏同一原图/人工轮廓/预测轮廓。显示按原图1–99.5百分位映射8位；仅显示使用，所有分割由原uint16转float64开始，强度取原uint16。图像公开CC0，未上传私有资料。观察到小核/簇分离失败；不推断全部错误同因。

## 实际命令与结果

- 归档下载检查首次退出1：误读 macOS 的资源分叉 txt；随后只读明确 metadata 成功，归档摘要已保存。没有把下载失败记为数据通过。
- `probe.py … run-01`：退出1，第一张 validation PNG 为 RGBA，不是原断言 RGB；尚未测试 test。修正允许alpha恒255的RGBA，红通道解码不变。
- `probe.py … run-02`：退出0，完成15图；NumPy 对 where 无 out 警告。评价分母为非空实例的并集，实际均>0；改显式断言 union>0 后直接除法，不填0、不改匹配阈值。
- `probe.py … run-03`：退出0，无上述警告；完整逐图计数/匹配和逐核强度与run-02逐字节一致，参数及选图未变。
- 小型解析评价核对：完全重合TP1、半面积恰IoU0.5不匹配、空预测FN1，全部通过。它验证评价边界，不替代数据作者的独立核标注。
- `uv run --locked --no-sync ruff check work/evidence/P-013/probe.py`：退出0；`ruff format --check`：退出0。
- `uv run --locked --no-sync python dev.py policy`：退出0，扫描213产品文件。无产品实现变化，不把此结果称新产品通过。
- 本机全量产品测试、目标机、真实学生试用、独立IF强度参考：未运行/未取得；纯研究不新增无关产品测试。服务器必需CI仍正常执行，不改门禁。

没有调整准确率预期、测试容差、skip/xfail、类型忽略或产品锁；只修正真实输入通道断言及评价除法警告，原失败与输出仍在仓库外保留。
