# Decision Log

| Date | Decision | Reason | Evidence |
| --- | --- | --- | --- |
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
