# P032 固定独审

**通过（pass）。** 2026-11-09 在 Windows 以独立 detached 工作目录复核。基线 `b7ac508a79f31d95c5fc22a715f04d7c1c81cff5`，实际数值与可执行研究 `cf91bc59b6708316664af78bae61fa8b0e1f347d`，最终受审候选 `791f4e056c1a20ca4aa951e501acc52ff0a41a13`。PR 和远端分支均指向该最终 SHA。结论支持把已配对的原图和给定实例标签转换为逐核测量表，作为受限工程 MVP 的候选范围。[PR83](https://github.com/Junweiiii14/bioimage-tools-platform/pull/83)

**原件、标度与对象。** 从 CellProfiler 官网重新下载 ExampleHuman.zip，SHA256 为 `7b35c66b775b5a25d0e39f917e0c52982ff2605017ded9c0cd0dc39a206b0138`。归档 README 明确示例图像由 Jason Moffat 提供且为 CC0，CellProfiler 4.2.8 源码许可为 BSD-3-Clause。官方管线把 D03f00d0 识别为 DNA（DAPI），D03f00d1 为 PH3（磷酸化组蛋白 H3 抗体）。测量范围是 DNA 定义的 Nuclei 对象内所有像素。两原图均为 512×512、uint8、1 通道，与给定的 int32 标签 TIFF 同形。Image.csv 的两项 Scaling 均为 255。实例标签 0 为核外，正整数 1 至 289 为核 ID。TIFF 的像素密度字段未给出经验证的样品面尺度。[官方示例](https://cellprofiler.org/examples) · [来源回执](source/receipt.json)

**真正执行与独立参考。** 以核过摘要的 Windows CellProfiler 4.2.8，在新目录重放提交入口，官方原有 14 模块后只追加两个标签导出模块；CP 完成标记为 Complete，回放进程 exit 0。输出标签 TIFF 和逐核 CSV 与冻结证据逐字节一致，摘要 JSON 的值一致，Windows 文件的 CRLF 与 Git 存储的 LF 有别。另从新下载包取出原始 14 模块管线和三张 TIFF，独立新运行 exit 0/Complete，产出的 Nuclei.csv 与历史 289 行参考表逐字节一致（SHA256 `25f1c18542ca8a4fcc39afd3586fb9d0f552a61d403e30865d10c2eddc11cee7`）。审查侧首次额外试跑把原图放进 .local，官方 Images 模块按其现有隐藏目录过滤规则找不到文件，CP 虽 exit 0，完成标记是 Failure。将同一输入置于普通临时目录后才得到上述参考结果。保留两次回执。[原管线成功运行](quant/official-run-2/receipt.json) · [首次过滤记录](quant/official-run/receipt.json)

**逐核独立复算。** 使用 Pillow 直接读取官网下载包中的原始 TIFF 和冻结标签 TIFF，用 Python 整数逐像素累加面积、x/y 坐标和、强度和与触顶数；核均值及质心最后才作除法。按 (ObjectNumber, channel) 匹配冻结 CSV 和独立生成的原管线输出，未用作者 SciPy 聚合代码。289 个核共 36,963 px²，面积逐核精确相等，零基质心误差在 1e−10 px 内。两通道共 578 条均值、578 条积分，原始 DN 和积分逐项吻合；除以各自的 255 后，均在报告所定一个 float32 相对 epsilon（绝对容差零）内。[独立逐像素回执](quant/pixel-receipt.json) · [冻结的逐核表](https://github.com/Junweiiii14/bioimage-tools-platform/blob/cf91bc59b6708316664af78bae61fa8b0e1f347d/work/evidence/P-032/per-nucleus.csv)

| 通道 | 每核均值的视野中位数（DN） | 全图最大 DN | 编码触顶像素 | CP 标度均值 / 积分最大绝对差 |
|---|---:|---:|---|---:|
| DNA | 54.019608 | 255 | 2 个，均在核 7 | 1.1276e−8 / 3.1381e−6 |
| PH3 | 10.245283 | 245 | 0 个 | 1.0142e−8 / 1.1950e−6 |

例如核 1 面积 131 px²，DNA 原始积分为 6,373，PH3 为 1,298，分别除以 131 得到核内均值 48.648855、9.908397 DN。标签 TIFF 的 SHA256 为 `471fd7ff09b05aae6f72538b2f5c1f1ec8482f0bb95aebcbb274888c88e01a6b`。

**反例。** 在独立副本中仅将第 289 号核的 PH3 参考积分加 1/255，相当于一个原始 DN 的积分差。用未修改的提交脚本重放，CP 正常完成，随后比对指出 289 项中恰有 1 项超差，退出码 1，没有写出最终逐核表或摘要。[负例回执](replay/negative-r2/receipt.json) · [独立精确分数核验](replay/independent.json)

**适用范围。** 这次交叉验证了公式和软件计算。CP 参考与独立复算使用相同对象，核边界的独立真值仍缺。289 个核来自 1 个 HT29 视野，生物样本归属未知。背景校正、阳性阈值、通道实测配准、跨批次曝光可比性和学生现场使用均需各自的证据。固定场景下原管线的 Nuclei.csv 已提供 CP 标度的均值与积分。独立测量路线另提供原始 DN、按既有标签重算和触顶核查。是否进入开发与此后的产品准入仍由规划窗口按实际需求决定。[CellProfiler 测量定义](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.2.8/modules/measurement.html#measureobjectintensity)

**治理整改已关闭。** 初始 cf91bc5 同时带入两份规则回执而缺历史来源清单，准确规则检查 exit 1，任务卡仍是 in_progress、未绑定研究内容。d78e57c 只补集成清单，规则检查 exit 0。最终 791f4e0 相对上一版只将任务卡改为 in_review 并指向 cf91bc5，准确规则检查 exit 0。P031 收尾和当前规则回执内容与原提交相符，研究程序与数值工件均未改变。全局计划检查在基线和最终候选均先报 P010，缺受审 SHA 的集合均为 P010/P021/P022/P023，无本轮新增。产品与上游算法源码未改，未重跑无关产品测试。必需 CI 与合并由规划窗口核对。[三阶段核验](governance/p032-governance-791f4e0.json)
