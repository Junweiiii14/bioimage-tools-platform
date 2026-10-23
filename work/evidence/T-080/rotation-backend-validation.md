# T080 旋转定量几何保护验证

2026-10-23，作者自验（inspect_crop_rotation）；不是独立审查。工作树为 `wb-lab-installer/bioimage-tools-platform`，分支 `codex/t080-crop-evidence-plan`，基线 HEAD `2d2c9727ec93c7a625e46964696788f06f8f4834`。本子任务没有提交。Windows 11 10.0.26200 / Python 3.12.14 / 仓库锁定环境；所有本轮图像均为合成数据或已提交的合成历史夹具，未访问私有原图。本轮未启动 Qt。

## 问题与改动

原实现对已自动裁图的同一轴向 ROI 仅改角，也重新执行 `fixed_lane_grid`，丢失逐槽目标位置和背景限域。例如合成五泳道样本的首槽由 `(230,136,279,155)` 变为 `(229,124,277,176)`；整行 ROI 相同不足以证明定量输入不变。

- `application/intake_crop.py`：已可信几何、同一 ROI 且明确传入角度时，使用版本化 `intake_crop_display_review@1`，记录人工复核，保留原 slots、fixed_grid、geometry_policy、检测/候选来源和 raw_crop。连续改角的 pending 草稿可再次复核；不允许越过运行中阶段。新 ROI 仍重建人工固定 N 槽位，并清除旧裁图引用。
- 新复核策略继续检查 guided @1/@2/common 辅助来源身份；人工复核状态不能省略。原自动策略读写不变。源边界舍入容差与显示契约统一为 1e-7 像素；真实越界继续拒绝。
- 按主任务新账本版本，自动采纳入口接受 workflow @3/@4，几何采纳门禁不变。
- `test_intake_automatic_crop.py`：覆盖旧 @3 与新 @4 自动小显示框分别改角 0/-17.5，连续改角、保存/重开、原框尺寸、原 slots/grid/raw_crop、重新裁图字节和实际 Fig 准备得到的定量计划/摘要一致；显示输入摘要必须变化。新 ROI 仍重建；guided @1/@2 篡改来源仍拒绝；源边界亚像素舍入保持一致。
- `docs/contracts/wb-common-band-crop-v4.md`：仅补旋转段，说明新策略、定量不变量、原资产与阶段完成的区别及旧版兼容。

定量摘要使用公共 Fig 准备流程返回的 `ProjectRowAnalysis.model_dump_json()` 的 SHA256；在同一 API 项目修订上全量比较。宿主持久化时 CAS 修订号可以变化，此处不宣称修订元数据永久相同。角度编辑仍按既有流程重建派生显示，未将旧资产引用伪装成新阶段已完成。

## 最终检查

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `uv run --locked --no-sync pytest tools/wb/tests/test_intake_automatic_crop.py tools/wb/tests/test_intake_crop_v2_compatibility.py -q --tb=short` | 0 | 29 passed，3.69s |
| `uv run --locked --no-sync pytest tools/wb/tests/test_intake_crop.py tools/wb/tests/test_intake_figure.py -q --tb=short` | 0 | 11 passed，2.67s |
| `uv run --locked --no-sync pytest tools/wb/tests/test_intake_automatic_crop.py -k rotating_guided -q --tb=short` | 0 | 2 passed / 22 deselected，1.51s；去除测试对私有 helper 的导入后重验受影响两项 |
| `uv run --locked --no-sync pyright tools/wb/src/wb_tool/application/intake_crop.py tools/wb/tests/test_intake_automatic_crop.py` | 0 | 0 errors / warnings / informations |
| `uv run --locked --no-sync ruff check tools/wb/src/wb_tool/application/intake_crop.py tools/wb/tests/test_intake_automatic_crop.py` | 0 | All checks passed |
| `uv run --locked --no-sync ruff format --check tools/wb/src/wb_tool/application/intake_crop.py tools/wb/tests/test_intake_automatic_crop.py` | 0 | 2 files already formatted |
| `git diff --check -- tools/wb/src/wb_tool/application/intake_crop.py tools/wb/tests/test_intake_automatic_crop.py docs/contracts/wb-common-band-crop-v4.md` | 0 | 无空白错误 |

恢复工作时核对上一轮所有命令均已退出，未发现本子任务残留 pytest/pyright/ruff 进程；没有重复完整测试。

## 失败及修正记录

- 新测试第一次检查未审核 display_review 时被更早的 raw_crop 审核门禁正确拒绝，4 项失败是预期异常文案不匹配。随后在该非法状态测试中移除 raw_crop，单独验证新策略的人工确认要求；未改变任何产品门禁。
- `ruff format --check` 初次退出 1：一处表达式需格式化；格式化后通过。
- 误调用未安装的 `mypy`，退出 1（program not found），没有安装依赖；改用仓库实际配置的 pyright。
- pyright 初次退出 1：测试跨模块调用私有 `_grouped` helper。改为已有公开 `grouped_arrays` 加明确合成数组，相关两项重验与严格类型检查通过；未添加 ignore/skip/xfail。

## 文件身份与未完成项

完成时 SHA256：

- `tools/wb/src/wb_tool/application/intake_crop.py`：`4dd835a2f0527cfe8cf0ead00d214f5957887185373b6027bff225f94a4d09e4`
- `tools/wb/tests/test_intake_automatic_crop.py`：`d515a647a1272d34b396b4254ccda56a4e0526e20884e3ec53785392e8b8d639`

主任务负责后续集成、准确提交绑定的独立审查、必需 CI、PR 和安装包验收。作者不能把这份自验视为独审。此前 UI 证据位于 ignored 的 `.local/T080/rotation-ui/evidence.md`；UI 文件已移交主任务，后续改动不在本轮非 Qt 检查覆盖内。
