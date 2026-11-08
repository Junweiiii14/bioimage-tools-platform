# P026 公开 WB 材料独审

**研究事实通过。本次候选结论为 changes_required，唯一阻断为 R01。** 2026-11-09，独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`。审查绑定 base `e846a681c85e04d53904fe8b6b384376e98f6032` 与 head `44a6109da485f6b0085ee81ede5420dd294f2418`。[PR78](https://github.com/Junweiiii14/bioimage-tools-platform/pull/78)

## R01 · 缺少历史回执的集成清单

PR 同时携入 P025 收尾回执和 P026 本次回执。独立检出上运行 `python -B -m tooling.rule_context check --base e846a681c85e04d53904fe8b6b384376e98f6032 --head 44a6109da485f6b0085ee81ede5420dd294f2418`，exit 1，同一提交的必需 CI 也失败。两份回执本身可核。本次应使用现有集成清单登记 `work/evidence/P-025/rules-context.json`，来源提交 `94f47be998f5e904a797df922d2a1a8844816fa4`。复审只需验证新增清单、原回执字节和新提交的规则检查。P025 完成卡已填正确受审 SHA，既有计划元数据缺项此次新增 0。产品、算法、锁和门禁没有差异。[GitHub 规则检查](https://github.com/Junweiiii14/bioimage-tools-platform/actions/runs/42507510585/job/128813232940)

回传时另核到本地修复 `45daa37cfc42e11103597acb4ad0a2b7452a6d48`。相对原审只新增上述清单，原提交的研究报告与探针 Git blob 相同。使用准确 base 和该本地 SHA 运行同一规则检查，exit 0。GitHub PR 查询与 git ls-remote 在回传前仍指向原审 `44a6109`。

## IOCBIO 原图与定位

固定 ZIP 为 64,922,171 字节，SHA256 `66c84b4a5557ccfd203bec15becbc9e85ca7c681e9e2b2545f24092b60059c46`。归档含三张膜各自的 GAPDH、LTCC、Ponceau 三张图。只取 `gel1_GAPDH_expo1min.tif`，成员 SHA256 `af35f27d9171f1699a8247611dc48683833f03eae1ed30a1e795ad5966ab3a64`。ImageQuant LAS 4000 标签记录 1 分钟曝光、暗帧与仪器校正。公开 load_tiff 的二维数组与直接解码逐像素相同，单页 3072×2048、单通道 uint16、MINISWHITE，范围 941–30497，两端数字码命中各 0。线性响应不能由此确定。

在独立树使用锁定 CPython 3.12.14 环境运行提交内 probe.py，exit 0。配置为 lane_count=13、crop_height=30、polarity=light、left_marker=True、min_snr=4、无膜框提示。在泳道拟合前，suggest_crops 的 membrane_periodic_profile_candidates@1 已返回 membrane_not_found 和 0 个候选。若进入泳道格点步骤，左 Marker 在 13 个样本泳道之外另计。本次没有积分、归一化或科学误差输出。首页仪器批处理另走 source_geometry@2，不在此次探针范围内。

论文图 3 为三名操作者分别使用两款软件，按图、操作者和软件各自的泳道均值归一。作者算法先沿泳道宽度积分，本项目沿宽取均值再做端点基线积分。归档没有把操作者测量值、ROI 和端点逐泳道绑定的表，图中相关性不能用作本软件的准确率。[IOCBIO 论文](https://link.springer.com/article/10.1186/s12915-023-01734-8) · [图 3](https://link.springer.com/article/10.1186/s12915-023-01734-8/figures/3)

## Butler 与 Clegg

从 PMC 官方对象取得 Butler S2 原表，与本地缓存逐字节一致。43,052 字节，SHA256 `fdb4ed8f4139d35d7b6a3fdeb38bc8ca282e18634f3b011300c601231590c57f`。Figure 1 Data 的 B3:E14 为硝酸纤维素膜、化学发光、11 档总蛋白上样量和 3 张膜。膜 1 在 20 µg 时 O.D. 为 1,108,907，在 40 µg 时为 926,268.8，红外块的空单元格保留缺失。研究引用的是作者测量，已核材料尚不能将原灰度帧逐膜、泳道和曝光对应到这些数值。本轮 Europe PMC 聚合端点返回服务错误 XML，改从同一论文的官方 PMC 文件核对。[论文](https://doi.org/10.1155/2019/5214821) · [S2 原表](https://s3.amazonaws.com/pmc-oa-opendata/PMC6360618.1/5214821.f3.xlsx)

Clegg 固定 v2 的图 1 TIFF 仅取前 65,536 字节，HTTP 206。首 IFD 为 13868×2777、RGB8，软件标记 Illustrator 25.1；源图说明记载 ChemiDoc MP 采集及 Illustrator 裁切和标注。固定 v1 定量表首标签为 Fig. 1C.，内部 A1 标记 Figure 1B，给出三个条件各三次重复的 pRab10/Rab10 比值。此材料支持排除这个面板作逐带线性原值参考，结论只及所查版本、文件和首 IFD。[源图 v2](https://zenodo.org/records/21109968) · [定量 v1](https://zenodo.org/records/17596792)

## 复验位置

独立树为 `bioimage-review-p026`。锁定依赖离线同步 exit 0，明确选择上述缓存后运行 `.local/reviewer-venv/Scripts/python.exe -I -B work/evidence/P-026/probe.py <IOCBIO ZIP>`，实际输出在 `.local/exact-probe.txt`。逐像素对照、完整标签和探针设置见 `.local/iocbio-input.json`。原表与 Clegg 定点解析 exit 0，见 `.local/sources/receipt.json` 与 `.local/sources/scope-receipt.json`。规则失败及保护路径检查见 `.local/governance/governance-44a6109.json`。准确 base/head 的 git diff --check exit 0。
