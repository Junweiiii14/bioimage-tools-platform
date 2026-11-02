# V0 WB模块与对照成果 v1

P002实施中的公开边界；完成状态和实际验收以任务卡为准。此增量不改变原WB方法、AssetRef v1、Workspace格式或旧项目读取。

## 冻结请求和唯一准入

`wb_tool.api.prepare_wb_execution`接受已登记的原图AssetRef、原AnalysisRequest和文档身份，冻结ModuleSpec、参数canonical JSON及SHA256、运行环境版本、request/execution/node/attempt/document/revision身份。模块固定为`wb-legacy-analysis`、版本`1.0`，仅准入`fixed_grid@1`、`legacy_bounds@1`、`profile_integral@1`、`dtype_limits_review@1`。不实现归一化或自动几何校正。

`execute_wb_module`重新验证信封，校验当前实现与环境，调用原`analyze_annotations`；不复制科学公式。原uint8/uint16、显式极性、原图半开ROI、闭区间积分边界、均值剖面信号及质量复核语义不变。实现摘要是固定源码清单按列举顺序的LF规范化SHA256，不是实验真实性签名；更新实现或环境须显式建立新请求。

`tool_contracts.api`新增schema_version=1的ModuleSpec、ExecutionRequest和OutputManifest，protocol_version=1的ExecutionEvent，科学角色由BoundAsset组合既有AssetRef表示。未知字段、布尔版本号、重复JSON键、非有限数、超过1MiB的JSON及超过32层嵌套拒绝。旧`storage_contract_schema()`快照不变。新版契约不能由旧程序自动解释，不伪装成旧AnalysisResult。

## 实际执行和文件

静态入口`python -m bioimage_app --worker wb_v0_compare`（工具独立入口`python -m wb_tool.module_worker`）不加载GUI。宿主通过stdin的一行WBModuleStart传入冻结请求、完整运行身份、受控绝对原图路径和全新输出目录；先收到hello，真实PID持久化后才发送start。worker只写全新目录，不修改输入和旧输出。

worker先后真实执行旧`analyze_annotations`和新`execute_wb_module`，比较完整机器结果。固定`legacy_exact@1`的绝对容差为0：同一输入、同一旧确定性方法的工程等价检验，不是科学准确性阈值。至少需要一个条带，不生成空差异表。

| 端口 | 文件 | 内容 |
| --- | --- | --- |
| measurements | measurements.csv | 样本（lane身份）、指标（band身份）、有效信号、状态、原因、方法、源资产/SHA、运行/请求身份、单位和单独的待复核原积分 |
| differences | differences.csv | 两次真实计算的数值/状态/原因、差值、可数值比较标记和精确一致标记；不可数值比较时差值为空 |
| provenance | run-manifest.json | 冻结请求、模块/方法/实现/环境、真实run关联、比较策略和其他四项文件SHA |
| analysis | analysis.json | 新模块机器结果，沿用原AnalysisResult |
| baseline | baseline.json | 本次旧入口真实计算的机器结果 |

CSV为UTF-8 BOM，文本字段使用可逆`text_prefix@1`（每个字符串加`text:`）避免电子表格公式解释；数值/布尔原样，None为空。`quality_review`、`invalid`、`excluded`和`not_detected`均不进入有效value，真实有效零保持0。单位`mean_pixel_intensity_times_pixel`指原图行宽均值强度沿像素剖面的积分，没有物理长度校准。

全套产物上限16MiB。summary的`exact_match`比较完整序列化结果；`quality=complete`要求结果一致且所有行valid，否则`issues`。成功产生比较报告不等于每个条带可用于下游定量。

## 协议、退出和持久化

事件依次hello(0)、accepted(1)、result/failure/cancelled(2)；accepted及终态携带完整同一尝试身份，result携带publication=candidate的OutputManifest。取消只接受当前身份的一次消息。worker结果事件不证明进程成功退出，也不代表Workspace提交。

宿主复用ProcessRunner和RunSession，收到真实成功退出回执后由现有存储线程校验冻结持久请求、输入注册资产、候选身份、声明文件集合、路径、非链接/非硬链接、大小和SHA。必需输出缺失/篡改、manifest后非零退出、无终态或错误身份不得成功。文件经Workspace不可变导入，再用原commit_result事务保存publication=committed的正式清单；正式引用为Workspace登记AssetRef。原图、请求和旧结果不覆盖。

导入与最终结果CAS不是一个文件系统原子事务。取消或失败可能留下暂存文件和未被结果引用的导入资产，保留诊断，不当作成功结果，不自动删除。取消token继续传入最终commit_result，终态先后沿原提交规则。宿主关停必须等实际worker退出和存储线程排空。薄GUI与`--v0-compare`/`--v0-open`共用ComparisonSession，重开核验输入、冻结请求和全部成果资产；操作见[中文验收说明](../wb-v0-acceptance.md)，实际验证状态见P002任务。

`run-manifest.json`记录计算阶段的来源，不自证宿主已提交；最终RunRecord及其result引用的OutputManifest才是成功发布依据。重开后必须用Workspace校验资产再展示。旧AnalysisResult/项目记录继续走旧读取路径。
