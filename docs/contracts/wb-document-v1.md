# WB 草稿文档 v1

`wb_tool.api.WBDocument` 保存 source AssetRef 与 AnalysisRequest，schema_version=1。
source 是工作区输入快照引用；摘要必须与请求来源一致。不保存绝对源路径、显示数组或结果候选。
request 保留半开 ROI、闭区间条带、基线、极性、稳定身份与 revision；空白泳道可保留无条带。
通过 from_bytes 读取时拒绝重复 JSON 字段、未知字段/版本、布尔修订与非法数据，最多16MiB。
写入始终包含显式版本；旧 worker v1 与工作区 v1 未变化，没有把预览位深变成定量位深。
JSON schema 快照 wb-document-v1.schema.json，漂移测试必须同步审查。

UI 编辑 generation 与持久化 revision 分开。每次保存冻结文档并递增持久化 revision；
计算使用 prepare_run 冻结的文档，运行期间的新编辑可保存为后续草稿，旧结果不替换当前标注。
重开验证输入资产，重新生成显示副本，读相同修订的已提交历史结果。无效/未检出/待复核信号显示缺失。
关闭先保存有效的未保存修改，取消/确认活跃进程退出，再异步关闭存储与预览线程。

预览最大边约2048采样像素；16位显示为原值整除257的8位副本，只用于画布。
ROI 从显示变换回原像素坐标；worker 再从原始快照计算，无显示重采样参与数值。
当前界面是手工闭环，完整首版仍必须完成自动候选、拼图Fig/行名OCR、关联/归一化与自动结果写表等。

T044可选 `anchored_context@1` / `anchored_background@1` 的目标与采样区扩展见
`wb-anchored-context-v1.md`。同步审查三个机器schema；旧策略序列化省略新默认字段，
既有资产不重写。旧读取器拒绝新策略；不能把外层版本保持解释为支持新字段。
