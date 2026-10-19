# T-060：E7 集成、包态与交付验收

- 状态：implementing；base5e3459a，E6产品ea7ed55。前置E0–E6各阶段相关/完整门禁、绑定独审及证据已收尾；E6 862/624.64s、原child0、全部wheel/真实OCR/check0。
- 授权：按docs/wb-execution-plan.md连续推进，无阶段重复批准、无定时任务。有效t051/codex/wb-e0-e7；root sole writer，非作者只读独审。原ResearchVault dirty树、旧候选/安装/原图/历史结果/用户窗口保持。
- 范围：apps/desktop、tools/wb、tooling、tests、docs、README.md、AGENT_HANDOFF.md、.agent-handoff、work/tasks、work/evidence、.github（仅实际CI诊断必要时单独说明/独审，不改规则以绕过失败）。scope .加载全部当前与BASE规则。
- 首项：补充当前存活高风险链独审已绑定ea7ed55/base536f04e，发现历史OCR迟到取消P2。ProjectOCRSession异步解码后不查取消，宿主完成/安装只查generation；先改草稿再保存使失败/取消可能替换关联。修session完成与host完成/安装/CAS前后保护；真实已提交RunRecord不撤销，保存失败/取消保留当前旧关联。覆盖decode/install/关闭/encode前/CAS在途/保存失败/后续显式重试及过期generation。
- 科学/接口：不改算法/默认值/项目schema1–14，不升级依赖/锁，不取消独立灰度或OCR。新诊断、构建清单/通道接口明确版本和旧行为兼容。
- 集成：核实main/历史PR7→3→8…15及本地后继真实依赖；逐批更新匹配实际base的规则回执/显式历史manifest，保留历史来源/审查缺口。绑定最终head非作者审查，四项服务器必需检查完整通过后PR集成main；禁止强推main、删除回执、改成功状态/规则绕过失败。远端状态和实际merge SHA逐批记录。
- 包态：干净提交构建新隔离测试候选，独立AppId/目录/设置/入口，不覆盖T047/T048或原安装。沿用已验证private CPython3.12.14/锁定四wheel/WebEngine/完整OCR模型与许可源码；不用未通过的AOT路线。单独说明资源裁剪，既有qml/include排除之外不扩大裁剪。
- 安装验收：本机非管理员Win11新候选安装、卸载/重装、中文路径、独立入口/设置、原资产与旧安装保护；私有实际runtime运行新清单批量主链（保存/真实worker/稳定槽表/新目录输出/重开/重复不覆盖）与独立灰度/OCR两条流程、所属进程关闭、离线模型，精确进程退出和文件摘要。不调用用户Esc停止的原生Computer Use；离屏工程不外推物理输入/DPI。
- 待验边界：独立真实仪器真值/样本对应、干净目标Win10与125/150/200%DPI缺失时保留未验；继续不依赖的候选/集成工作，不标正式发布完成。历史纯虚调用UNKNOWN保留，不据本轮成功销账。
- 验证：针对性真实Qt/故障测试、全量check和隔离wheel、非作者当前提交风险复审；Qt测试/探针/安装态串行。记录每次命令/退出码/环境/提交与失败，未跑明确未跑；必要实验先冻结预期，不弱化断言/容差/时限。
- 下一步：context/规则阅读→OCR取消/CAS回归及修复→高风险复审→依赖集成/远端CI与独立候选构建/包态验收→需求矩阵和交接。

## 当前进展

OCR取消/CAS修复13边界+42兼容、非作者P2关闭；新E7候选/14检查源自检、4设置隔离、2启动故障及独审通过。32d全量单一standalone页面失败后监视器GBK/UTF8异常截断细节，原OS退出未知/outer1/wheel未跑；独立重放1/10.57s0不销未明失败。监视器Unicode2项先失败后8项全部0，只修日志/真实退出传递，不弱化断言。已merge治理main773并重载规则；PR7已合，PR3新base/head远端检查中，后继阶段继续按依赖。下一步绑定监视器复审和完整UTF8全量复验，再独立候选构建/包态。

