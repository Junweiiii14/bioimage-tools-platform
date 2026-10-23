# T080 常见条带算法实施与有限验证

日期：2026-10-23。记录者是 `common_band_geometry.py` 的实现作者；这是作者实施与验证记录，**不是独立审查**。最终产品提交仍需非作者审查、仓库必需检查以及主任务的完整流程与安装态验证。

## 状态与绑定范围

- 分支：`codex/t080-crop-evidence-plan`。
- 验证时基线 HEAD：`2d2c9727ec93c7a625e46964696788f06f8f4834`；产品变化位于共享工作树，尚未由本记录者提交。不能把基线提交称为已包含整改的产品提交。
- 环境：Windows 11 `10.0.26200`，Python `3.12.14`；通过仓库锁定环境执行 `uv run --locked --no-sync`。
- 本记录覆盖新增领域模块、其定向测试、公开裁剪 API 的有限重放，以及外侧空白收缩契约。桌面旋转、项目交付目录、完整实验项目流程、安装包与最终独审由主任务另行记录。
- 未修改原始输入、历史结果、锁文件、门禁或既有可靠算法实现；检测使用私有浮点副本，原像素采样继续使用原数组坐标。

最终文件 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `tools/wb/src/wb_tool/domain/common_band_geometry.py` | `28385c8ab8ae0e13bee42c470bf8ee178757a0dda906e3c527d35bb4a611b782` |
| `tools/wb/tests/test_common_band_geometry.py` | `6f4e0d7a815173b49057958d4a53829ddad5aa244e7f446713ba0ad49da68ca8` |

## 最终实现

新增 `source_common_band_geometry@1` / `guided_common_band_geometry@1`；公开 API 接纳后使用 `intake_crop@4`，保留 `reviewed=false`。既有可靠几何被接纳时继续保留旧 `intake_crop@3`；新算法不通过为旧失败候选添加成功标志来放行。

主行依据明显核心的共同方向和空间排列选择。单个大片阴影的得分贡献有上限；同一X附近的碎核或多行不能重复累加无限票数；远处较弱行不单独阻断。两个独立完整行同等级、没有明显优势时保留 `common_rows_equally_prominent`。分数是工程启发式，不是统计置信度或蛋白身份判断。

信号方向由选中核心逐列原信号的加权位置拟合，支持连接成片的核心；不以膜倾角替代信号倾角。明确N始终保留：先处理多余近碎核，连接剖面按谷区加权中心划分；有两端与共同节距证据时保留内部弱/阴性槽，末端相位不足仍需调整。未将弱信号或失败伪装成有效零值。

显示框保持5N:4，并覆盖所选核心和少量背景。原像素轴向采样框Q与旋转展示框分别保存；Q采用共同主行包络，完整保留N及内部共享X分界。`sampling_limits` 完整包含各Q；它们不表示轴向矩形等于旋转多边形。

若仅首槽左侧或末槽右侧的空白延伸触及膜外，允许该外侧边界向内收回；Y范围、内部X边界、N、槽位身份和展示框不变。收回后保留所选核心原坐标整数包围范围外至少3个完整原像素列的背景。保留范围仍逐像素要求 `all(valid)`；没有末端核心依据、核心/最小背景触边、内部槽或保留范围含膜外像素时拒绝，不降低膜外容忍率。该规则已写入 `docs/contracts/wb-common-band-crop-v4.md`。

## 定向验证与检查

所有命令从活动工作树根目录运行。这里只汇总已经执行的命令，不代表执行了全仓库检查。

| 命令（前缀均为 `uv run --locked --no-sync`） | 退出码与结果 |
| --- | --- |
| `pytest tools/wb/tests/test_common_band_geometry.py -q` | 最终0；11 passed，2.09秒 |
| `pytest tools/wb/tests/test_common_band_geometry.py tools/wb/tests/test_intake_automatic_crop.py::test_source_contour_cannot_prove_signal_direction_or_single_target -q` | 外侧空白修复前0；当时10个新用例加旧fixture的2个参数，共12 passed；旧同强双排拒绝断言未改 |
| `pyright tools/wb/src/wb_tool/domain/common_band_geometry.py tools/wb/tests/test_common_band_geometry.py` | 0；0 errors、0 warnings；最终模块代码相同。之后仅调整新合成用例右边界的测试断言，没有再次运行类型检查 |
| `ruff check tools/wb/src/wb_tool/domain/common_band_geometry.py tools/wb/tests/test_common_band_geometry.py` | 最终0 |
| `ruff format --check tools/wb/src/wb_tool/domain/common_band_geometry.py tools/wb/tests/test_common_band_geometry.py` | 最终0；2 files already formatted |
| `python .local/T080/common_integrated_final.py` | 0；首次公开API完整21例，结果如下 |
| `python .local/T080/inspect_g02_sampling.py` | 0；对唯一失败例做一次只读原因定位，不修改产品或绕过门禁 |
| `python .local/T080/common_outer_padding_recheck.py` | 0；修复后仅3例增量，不重跑21例 |
| `python .local/T080/compare_outer_padding.py` | 0；比较保存的报告，不运行检测 |

11个最终定向用例覆盖：三种信号倾角与原坐标、连接条带、内部阴性槽、大片阴影、同强/较弱第二排、大倾角膜外角落、首末空白边界机制、末端相位不足及取消。其中新增的空白边界例检查首槽收缩、N和内部边界不变、真实强带像素均被覆盖、背景余量以及源数组不变；真实末槽分支由下述g02增量复查覆盖。

新合成用例最初错误假定更换膜范围后推断网格完全相同、两侧必定同时收缩，并固定断言物理边缘精确坐标。实际膜拟合和整数边界会改变这些值。因此改为从同一返回显示框验证原网格内部边界不变，并用独立原图像素检查完整覆盖、膜内范围及背景余量；右侧本来有效时允许保持。曾尝试直接测试私有辅助函数，被类型检查拒绝，最终仍从检测函数进入，没有增加类型忽略、skip/xfail或修改旧测试预期。

## 首次21例公开API重放：保留原结果

诊断集合是9个采集组各2种信号来源，加3张PNG无损转TIFF副本，共21个来源变体。各例使用新建未审核单行容器，经 `propose_intake_crop`、`automatic_intake_crop_allowed` 和实际 `accept_automatic_intake_crop` 验证。N沿用运行前的视觉暂定值，**不是实验者正式metadata**。

- 20/21例有候选、允许自动接纳且实际接纳；17例为新 `intake_crop@4`，3例继续使用旧 `intake_crop@3`。
- 所有接纳记录与行保持 `reviewed=false`。
- 9个采集组中8组的两种来源均接纳；PNG转TIFF的3例全部接纳。
- 唯一未接纳例g02-2：旧算法 `lane_spacing_ambiguous` 后，新算法报告 `common_sampling_outside_membrane`，未伪造几何。
- 该次模块SHA为 `9d1bb05823774c8f130d724a45fcca53c9b0dccdf02446ccab10b6a9a828c4dd`，早于外侧空白增量修复。运行期间所记录相关代码SHA未变。
- 首次报告 `.local/T080/common-integrated-final/report.json` 的SHA为 `a59ceea968e391478b531badda4de9ab29a9fd3774e5bcb0b99d0c47141efe1d`。**该报告仍为20/21，未回填或覆盖成21/21。**

只读定位表明，g02-2最后一个Q为 `[791,846)×[742,761)`，其中26/1045像素位于有效膜外，全部集中于右上方X843–845、Y742–750。所选核心X811.41–827.41、Y748.77–753.79，说明触边来自外侧空白延伸，而不是核心越界。原因记录保留于 `.local/T080/common-integrated-final/g02-sampling-cause.json`。

## 最终模块的3例增量

仅复查g02-2和g03的两种倾斜来源；三例均经公开API实际接纳为 `intake_crop@4`，保持未审核。没有重复整批测试或搜索阈值。

- g02-2末Q变为 `[791,843)×[742,761)`，只收回右侧3列；N仍为4，内部X边界791、Y范围不变。所选核心完整，右侧仍有14个完整背景列。
- g03两来源的Q、展示框和 `sampling_limits` 与首次21例报告逐项相同；角度约−16.980°和−16.964°。
- 查看的必要叠图包括倾斜例、碎核末槽例、PNG参考及修复后的g02；显示框与Q分别绘制。叠图只用于观察几何，不作为原像素定量或生物学正确性的替代证据。
- 最终增量报告 `.local/T080/common-outer-padding-recheck/report.json` 的SHA为 `7d3113a84a6d4eee058657e0dae58cbee758a27d62da74ddc0fba273bacc2f9a`；边界逐项比较见同目录 `boundary-comparison.json`。

两次公开API运行均在前后核验输入清单中的原文件SHA及转换TIFF SHA；全部不变。旧baseline报告也保持原SHA。诊断脚本和叠图仅存ignored目录；本提交材料不包含私有输入路径、原图、真实文件名或图像内容。

## 统计与未完成边界

本记录评估的完整实验项目数为0：来源变体相关，单行新容器不是完整实验项目，采集组通过率也不能替代项目通过率。首次20/21加3例针对性复查，不能重写成在最终代码下重新全量证明21/21，更不能称为裁剪正确率或80%项目泛化证据。

用户目标仍是80%的完整项目内所有裁剪100%自动通过，并接受少部分项目错裁。需要分别报告整项目自动完成、全部裁剪无需修正、至少一处错裁项目率；当前开发集不足以估计这些指标。主行明显程度不能证明蛋白身份、抗体特异性、曝光线性或实验结论。完整项目流程、真实界面/导出、最终提交独审和安装交付的结果应追加在各自证据中，不能由本记录推断通过。
