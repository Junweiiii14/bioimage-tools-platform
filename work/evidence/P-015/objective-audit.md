# P015 目标逐项核对

| 目标 | 实际完成与证据 |
| --- | --- |
| 固定成熟实现，独立包/环境 | nuclei-tool及可选宿主入口；P014参数、58项研究环境依赖与模型成员摘要验证；缺模型失败而不下载；README/requirements-research/domain方法定义 |
| 原值准入 | 单页unsigned uint8 TIFF，检查位深、SampleFormat、Photometric、Orientation和通道/页数；signed负值反例拒绝，不转换16bit/RGB |
| 原坐标标签及状态 | uint32 NPY、原图YX/像素中心约定、不同非零ID核数；有效零核与失败/取消分开；请求和出处含摘要 |
| 复用执行和提交 | 显式WorkflowHostModule/CLI复用既有WorkflowSession、RunSession、ProcessRunner、AsyncStorage、Workspace；无新引擎或平台特判 |
| 真实调用/坐标对照 | 14场景，9张每像素每ID匹配冻结直接结果；不以shape/计数代替坐标核验；real-regression.json及独审只读复核 |
| 取消/失败/保护 | 缺模型、坏摘要、真实取消、长异常终态、输入拒绝、原图SHA及已存工作区不覆盖；实际后代退出和host-owned暂存；21新用例及真实场景 |
| 包装/边界 | workspace、AST、11条Import Linter契约、4个新增传递负例、严格类型、独立wheel默认无TF/GUI/存储；双平台完整门禁通过 |
| 独立审查 | 产品a490d2e、门禁测试95ecb02通过，后续只文档；independent-review.md保留原发现与修复 |
| 正常集成 | PR66，最终候选8f00757，必需CI全过后合main a761284；文件树一致 |
| 真实边界 | 无新科学准入；实验室/学生/16bit/训练重叠/Linux模型/目标机及旧GPU缺项保留；无私有上传、发布、花费、WB语义变更 |

本页的“完成”仅指P015已授权工程范围。下一任务须由上游派发，不能借本页启动未经授权的研究用途或发布。
