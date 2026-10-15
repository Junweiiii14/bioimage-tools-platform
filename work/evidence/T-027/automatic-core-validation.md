# T-024 自动建议策略 automatic_wb_proposals@1

状态：本地实现与作者验证完成，待协调分支集成、独立审查与实际 UI 验收。

输入必须为 load_tiff 的原始 uint8/uint16 二维灰度；暗条带是默认明确记录的策略，API 可显式选 light。文件名后缀不参与源选择或实验身份判断。分析仍为 profile_integral@1，建议版本与积分版本分离。

检测在私有 float64 副本上复用膜边界检测，膜不明确时在全图提出建议并记录回退。列方向短条带能量为垂直背景差的第95百分位，使用0.35/0.5/0.65/0.8/0.9相对阈值尝试分离相邻带，要求等间距候选的间距变异系数小于0.15及带宽至少间距0.4。仅左侧30%内的孤立信号不当样本。Marker 的几何建议与蛋白身份无关。固定网格保留内部推定槽位；显式 N 覆盖可保留已知空位。该工程启发式不证明实验泳道计数准确率。

行候选使用40%以上泳道的信噪支持，并以有界权重质心选择中心；默认60原像素高，小图自动缩短。请求边界通过平滑副本和端点背景差的主峰扩展至2%振幅或差分噪声阈值。原始均值剖面与端点基线进入既有积分，检测平滑绝不进入数值测量。弱/平坦槽 bounds=None，真实原值上下限仍 quality_review，不填有效0或绕过质量检查。

项目 schema8 继承 schema7，新增 AutomaticRowEvidence；source SHA、修订、原坐标、N、排除位、请求、策略参数和警告保留。human_reviewed 固定 false；row.reviewed 不伪造。row_is_ready 接受人工审核或当前自动证据，自动证据匹配源/几何/极性/边界/基线/包含位；运行修订重定基与 run 链接不会使证据无故失效。旧schema1–7读取不变。旧读取器不支持schema8，不能把它降级后伪装保留证据。

API：suggest_automatic_wb、suggest_analysis_for_crop、install_automatic_result、install_automatic_request、automatic_project_row、with_automatic_rows、row_is_ready。automatic_project_row 是后台调用入口；已有ROI时保持图上调整，重新建议积分边界；已有空位与估计N冲突会明确拒绝，不能悄悄删除用户空位。

验证：2026-10-15 Windows / Python3.12.14，40 targeted tests passed in1.31s（自动11 + 既有裁剪/项目29）；Pyright WB源及新测试0；Ruff同范围通过。矩形解析期望297500证明原像素积分未被平滑替代。首次新测试调用不存在to_bytes导致1失败，改为已存在model_dump_json编码；Pyright测试bit_depth类型收窄为已知合成16位，未改生产契约、旧预期、容差或门禁。

私有真实10TIFF本机只读探针：5个有清晰样本条带的图自动给出3/3/5/5/5泳道并生成边界；3个仅左Marker及2个未形成可靠列信号的图明确无样本候选。来源全部由实际像素处理，没有根据_0/_1选择。真实值尚未有人工真值；部分图含位深上下限，结果保留quality_review。私有图/接触表/脚本在.local，未提交。全仓检查由协调分支集成后执行；本分支不宣称完整产品通过。
