# PR84 / P033 固定增量独审

**本次源码 CLI 与工具 wheel 通过（pass）。** 审查绑定基线 `fb6638eb7145dc9f0af61679a48aaef24a681606`、产品修复 `e77d67a3ec2d9a8789ab6bea105fd6d3ab50b3b7`、冻结 HEAD `4fb45866cda22a3509cdd42d805f375ca6dab3a4`。2026-11-09 在独立 Windows 工作树核验。R01、R02、R03 及普通目录误拒均已关闭。目录候选的新增源码核验缺口见 F01。[PR84](https://github.com/Junweiiii14/bioimage-tools-platform/pull/84)

| 原问题 | 该提交的实测 |
|---|---|
| R03，实验计算归属 | 从冻结源码重新构建并安装核工具 wheel。在没有 bioimage_app、PySide6 或 TensorFlow 的隔离环境，用 Python 隔离模式调用 nuclei_intensity.api.measure_intensity，稀疏 ID、最大 uint32 ID、零值与空集均通过。核 wheel 增加 nuclei_intensity 命名空间，原 nuclei_tool 源成员与基线相同；桌面 wheel 只有 CLI 增量，从公开入口导入计算。既有依赖和算法阈值未变。 |
| R02，既有 worker 兼容 | 使用原 P015 worker、固定 P014 模型和 ExampleHuman d0，正常 nuclei_cli 创建全新项目，exit 0，新 run 为 96cd08b54077405e81d787520b32ee24，真实提交 233 核。新工具与原 worker 的分割实现摘要仍为 004eec08bec7aa4436dc30e9fd2f3041257139fbf6e2d3730db7e4b506262889。 |
| R01，已有结果保护 | A 指向另一有效项目 B/results 的真实路径及 Windows Junction 时均 exit 2，未写入文件或暂存目录。两个项目原有文件及目录前后一致，B 随后正常重开导出。普通目录及祖先含其他应用 workspace.json 的目录均 exit 0，原先的误拒已关闭。 |

从独立安装位置读取 API 路径并实际输入两个非零标签的结果见[隔离 wheel 调用](core/tool-wheel.json)。

构建时区分 ZIP 目录项与实际文件，复核后核工具和桌面 wheel 分别比基线增加 1,209、1,553 字节。旧分割器的 wheel 成员、方法指纹均与基线一致。[逐成员及门禁核验](governance/wheel-boundaries-4fb4586.json)

**直接调用范围。** 工具函数依约接收同坐标、已准入的图像和标签。额外直接传入形状为 (0, 3) 的两个数组时，迭代结果与“非空图、无非零标签”一样为空。正常 CLI 的 TIFF 准入已经拒绝零像素数据，不会写出这类项目结果。后续对接可输入切片或任意数组的调用方时，应在公开函数处明确拒绝零像素网格，以保留输入无效与合法零核的区别。[实际 wheel 的零像素反例](edge/wheel-receipt.json)

**数值与出处。** 对上述新提交的 233 核，通过正常 CLI 配对 D03f00d1 原始 PH3 图，逐像素按原标签做整数累加后求均值。每行原 ID、面积、均值、积分均匹配，逐行目标摘要和 run 以及出处中的源 TIFF、提交标签、目标 TIFF 和 execution/run 均与相应工件相符。核 1 面积 219 px²、积分 2249 DN·px、均值 10.26940639 DN。同一项目重复导出产生不同目录，保留原结果。另用 P032 的 289 个固定标签通过新 API 逐项复算 DNA、PH3 共 578 行，精确吻合。正常 verify.py 返回 0。此前已验证零核返回仅表头和真实零保留 233 行、损坏标签与错误输入拒绝。数值实现文件迁移前后字节一致。[新项目运行](core/build.stdout) · [逐核和出处回执](core/positive.json) · [跨项目与同名文件回执](integrity/receipt.json)

**接口与门禁。** 公开计算函数与文件 I/O、项目存储和 Qt 分离，供其他消费者从核工具分发物调用。此轮交付的是固定方法的源码命令与数值 API，可视节点和用户安装版不属于已验证范围。AST 对同一源目录的两个命名空间逐个核对归属，并有错误包名和来源目录的反例。导入契约、新 wheel 的实际安装、准确提交规则、git diff --check 均通过。独审实际运行 tests/test_nuclei_intensity.py 和 tests/test_boundaries.py，共 16 passed，变更文件 Ruff exit 0。科学适用性仍限于操作者确认同一视野同一像素坐标的 uint8 原图，本轮未做物理配准、生物阈值或跨样本验证。

**F01，含此方法的下一次目录候选验收前处理。** tooling/candidate_acceptance.py 的安装源码映射及私有运行时导入探针尚未登记 nuclei_intensity。用此准确提交构造的安装目录应比较 312 个源码/资源成员，该函数只覆盖 309 个，遗漏 __init__.py、api.py、py.typed。删除或篡改模拟安装目录中的 api.py 后，verify_source 仍通过。真实工具 wheel 的文件内容和执行行为已单独核验。请在下一次包含新方法的目录候选中，验证该命名空间与相应 Git 提交逐项匹配、可由私有运行时导入，并按各旧候选自身提交保留其原有的六命名空间核查。本次没有生成或签署 Windows 目录工件。[安装源码核验反例](edge/namespace-receipt.json) · [当前核验器](https://github.com/Junweiiii14/bioimage-tools-platform/blob/4fb45866cda22a3509cdd42d805f375ca6dab3a4/tooling/candidate_acceptance.py#L25)
