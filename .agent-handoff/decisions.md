# Decision Log

## 2026-10-31 B008 第一阶段派发

用户要求新版方案进入GitHub，并由GPT-6 Astra新聊天使用目标模式持续推进第一阶段。将阶段明确为方案3.0的V0真实WB完整切片；P001先接入正确产品树，P002完成独立运行到成果及薄GUI验证。文档发布与T082产品28提交分开追踪，保留历史限制；后续十场景与Agent仍是后续路线，不自动扩展本阶段。任务状态以接入后唯一P卡为准，GitHub issue44作导航和验收入口。

| Date | Decision | Reason | Evidence |
| --- | --- | --- | --- |
| 2026-10-21 | intake_crop@2机器采纳与人工分离；source_signal_geometry@1及instrument_guided_geometry@1共享信号方向/目标核验 | 膜角度和最强单候选不能证明真实条带方向/唯一目标；证据不足暂停，原坐标定量不变 | T072独审、自动裁图v2、最小实验 |
| 2026-10-21 | 方向框只影响所属Fig尺度；外层进程观察不再自动终止 | 保护native其他Fig历史与摘要；防PID复用误清无关进程 | T072 mixed回归与observer首失败/独审 |
| 2026-10-21 | 每Fig一次N/有序蛋白跨Fig连续分配，仅19仪器组占编号，28参考组保留单列；整批分阶段自动切页 | 用户逐项明确确认，普通实现自主；版本化新草稿/策略，旧结果不静默重排 | T070计划、T071任务与独审 |
| 2026-10-13 | 先建治理和环境，产品 P0 仍待启动 | 用户最新范围；不把方案变成执行授权 | docs/adr/0001-foundation-before-product.md |
| 2026-10-13 | 原始 PDF 保持原样、单仓库分包 | 保留长期方案来源和可回滚历史 | 初始提交与 policy 摘要 |
| 2026-10-13 | Skills 项目安装、完整 SHA 锁定 | 可复现、可审查、降低全局上下文负担 | tooling/skills-lock.json |
| 2026-10-13 | 原先保持私有，后被用户明确公开要求取代 | 用户最新指示优先 | F-002、GitHub visibility PUBLIC |
| 2026-10-13 | 规则加载回执与必需 CI，不绕过 hook 信任 | 无需逐次人工提醒、可复验；不冒充理解证明 | docs/runbooks/rule-enforcement.md |

| 2026-10-13 | 用户授权 T-002/P0，本机先验收，干净机后续 | 最新指示取代“P0 待启动”；不扩展 T-001/WB | work/tasks/T-002-p0-validation.md |
| 2026-10-13 | 可丢弃技术探针与正式产品包分开 | 先证明 Qt/worker/standalone，不预建平台 SDK | tooling/p0/README.md |

| 2026-10-14 | 用户授权持续开发 WB；先冻结参考后产品核心 | 最新指令替代仅限 P0；无第二消费者不预建公共包 | work/tasks/T-003-wb-product.md |

| 2026-10-14 | TIFF 以元数据识别颜色轴，MINISWHITE 原值保留且要求显式极性 | 避免显示或静默反相改变定量意义 | docs/contracts/wb-reference-v1.md |

| 2026-10-14 | dtype_limits_review@1 将上下限像素标为待复核而非证明饱和 | 原始积分可检查但不直接进入有效列；不将异常伪装为零 | docs/contracts/wb-manual-analysis-v1.md |

| 2026-10-14 | JSON 原字节 strict 解析 + 标签/重复键预检；worker 仅产出候选 | 保持 stdlib dataclass 唯一字段，避免 bool 标签与 JSON tuple 模式问题；终态由宿主提交 | docs/contracts/wb-worker-v1.md |

| 2026-10-14 | 新平台包仅管理 opaque 文档/资产/修订/运行，结果先文件发布后 DB CAS | 实际输入/草稿/请求/结果复用；保留未知目录而不假成功或删除 | docs/contracts/workspace-v1.md |

| 2026-10-14 | 多图行计划使用独立wb_figure_project v1，旧单图v1/v2与数值协议不变；显示拼图和原值裁剪同时归档 | 防止一个source定量协议被静默改成多源/8位合成；明确人工审核和来源、不同Fig宽度允许但同Fig不拉伸 | docs/contracts/wb-figure-project-v1.md；T-012的230全量/真实10图导入重开 |

| 2026-10-14 | 自动候选@1只提出几何，项目schema v2保存源/参数/结果快照，应用候选撤销审核；检测平滑不进入定量 | 原导出身份/Marker与真实条带尚需复核，N空位不压缩；更改N/高度禁止套用旧建议；源白背景和边缘反例明确呈现 | docs/contracts/wb-crop-suggestions-v1.md；T-013的244全量与10图探针 |

| 2026-10-14 | CLX明确排除，TIFF/TIF保留显式来源链 | 用户说明CLX来自特殊设备且不用处理，TIFF原图、裁剪TIF；扩展不是来源证明 | T-014用户补充、wb-project-analysis-v1.md |
| 2026-10-14 | 项目v3保存小型标注与已提交run/result引用，重开逐行核验 | 避免大曲线嵌入16 MiB草稿、重复名称误配及一份坏结果阻断整批 | 79a675a、docs/research/2026-10-14-project-measurements.md |

| 2026-10-14 | 项目v4保留已提交OCR证据，人工校正后按原图row_id/SHA/ROI/N显式绑定；取消重识别保留旧关联 | 重复蛋白名称不能证明来源，文档副本不能替代资产校验；OCR显示不进入原图定量 | 05e5d56、wb-project-ocr-v1.md、T-014/ocr-validation.md |

| 2026-10-14 | 项目v5保存显式参照/逐槽样本与对照配置，可无OCR；lane_reference_ratio@1从核验run重建q=T/R、f=q/所选对照均值 | 未知实验偏好不能变成默认配对；全部所选对照必须有效，无epsilon/坏对照静默丢弃；原始积分保持 | 0cd390b、wb-project-normalization-v1.md、2026-10-14-project-normalization.md |

| 2026-10-14 | PNG走独立OCR显示解码/白底透明/已知预处理ID；完整生成图先保存来源修订，再导入不可变资产进入OCR | 保持旧TIFF与原图定量语义，不以缩略图或未确认标签推断实验关联；通用存储线程import_bytes无实验字段 | 1d5ae2a、wb-png-ocr-v1.md、T-016/validation.md |

| 2026-10-14 | 批量元信息使用有界字面XLSX/CSV、严格完整键与可改预览，用户显式选行/字段后原子应用；项目schema不变 | 用户项目表含公式/订单编号和嵌图，不能推断科学映射；不解码嵌图、不用公式缓存；名称保留测量，N/空位依原契约失效 | wb-project-metadata-v1.md、2026-10-14-project-metadata.md、T-017/validation.md |

| 2026-10-14 | 结果CSV使用可逆text:文字编码，数字/None独立；统一ZIP v2保存当前引用的原请求/结果和逐成员摘要，导出重读核验 | CSV无单元格类型，不依赖表格软件特殊转义；显示缓存不能绕过损坏；历史证据不等于本机PID/成功收据，ZIP恢复单列T-019 | c5f5787、wb-project-archive-v2.md、2026-10-14-wb-csv-archive.md、T-018/validation.md |

| 2026-10-14 | schema6归档历史证据与本机run分开，原ZIP及复制请求结果持久化；新空工作区可显式导入单个原修订快照 | 不能伪造外来PID/退出/成功，不能丢历史后称恢复完成；普通CAS仍+1，后续真实计算沿原RunSession | wb-project-restore-v1.md、workspace-v1.md、2026-10-14-wb-archive-restore.md、T-019/validation.md |

| 2026-10-14 | 直接TIFF/PNG复用完整RGB8显示和来源；已知显示TIFF量化拒绝、OCR专用读取；精确保存后后台校验/无覆盖发布 | 混合位深/文字合成不能伪称原值；原16位定量和完整ZIP恢复保持，未知第三方来源不猜测 | wb-direct-figure-image-v1.md、2026-10-14-wb-direct-image.md、T-020/validation.md |

## 2026-10-15 维护顺序

先执行maintenance-plan维护验收与独审收拢，再扩新工具；设计技能不改变Qt技术栈；REA源码学习优先、按缺口试点。

## 2026-10-15 F-003采用决定

Taste v2用于公开网页；科研Qt应用优先Impeccable Operate，不迁移框架。两技能固定来源，Impeccable引擎另锁SHA；cmd固定LF维持跨平台来源hash。REA保留按问题调用的隔离工具，静态Electron已验证，暂不增加全局MCP或产品依赖；真实社区学习收益按后续同题对照决定。

| 2026-10-18 | T045独立完整泳道复用冻结WBQuant，UB全高/端点封底，Fig项目schema9保存原OCR与源坐标 | 用户明确授权自动计算后手动修正；不另建显示像素量化或旧前端表存储 | docs/contracts/wb-fig-quant-v1.md、work/tasks/T-045-wbquant-manual-and-fig.md |
## 2026-10-19 T-050 已确认需求

新WB主流程由一次Fig/蛋白/N清单驱动，N含无信号槽位但不含Marker；原名/缩略图批量分配确认；先拼图再触发原像素测量，不从拼图OCR重建身份。基于用户本次明确要求，替代旧OCR主路径规划。历史PDF与已保存结果不改写；成本/结构建议见新规划，S1–S3仍待审核。

- 用户后续明确同Fig仅共享N，不保证各蛋白样本顺序。方案更新为行ID+行内槽位ID，未给样本映射不自动跨蛋白关联/归一化；不增加强制样本录入以阻断逐行流程。

## 2026-10-19 T050 用户审核回复

S1异常局部暂停、S2独立结果目录获批；S3回复明确“单独使用灰度定量还需要OCR”。新批量流程不调用OCR，独立拼图灰度定量继续支持OCR识别/校正。不能将其解释为批准可选拆包或删除OCR交付，发行方式仍待评估。仅更新规划，产品和依赖保持。


