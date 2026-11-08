# P024 学生练习资料独审

**pass。三条练习路线均满足本机候选首次使用与输入准备的验收条件。**

审查对象为 [PR76](https://github.com/Junweiiii14/bioimage-tools-platform/pull/76)，base `d3733a7e1edae6e195d129c751a707e62b7fedea`，candidate `9d684ebb7089150273ef8da1760d6a6153a29d1d`。独审窗口 `01a1af0d-808e-7131-ae29-237aded27938`，2026-11-09，Windows x64，独立工作树 `bioimage-review-p024`。以下路径相对该树。

## 学生实际收到的 ZIP

作者树 `.local/p024-first-use.zip` 为 594,408 字节，SHA256 `73ccd34c0ed1dbb971241edf200c90ccbe58539f1188189a31f387e423944d2c`。审查者从该提交按作者公布的路径重新运行 git archive，得到完全相同的 ZIP 字节。解压实交付的 ZIP 至独立目录，校验全部 17 个文件。以 `examples/first-use/README.md` 为起点，9 处本地链接均能打开，三组可选择材料齐全。页面给出输入、必要信息、结果、导出、重开和本地反馈栏。本机 P023 启动程序、外置核 worker 和模型的文档路径均存在。

| 路线 | 在解压目录上的独立核验 |
|---|---|
| WB | `wb/inputs` 中的 A/B 均为 700×300 uint16 TIFF。将附带的既有生成器运行到另一个新目录，两份输出与交付文件分别逐字节相同。练习指定五泳道及 Target/A、Reference/B 配对，并标明合成来源。 |
| 核分割 | 交付文件是原图 IM197。EBI 官方下载、提交、历史缓存和 ZIP 的 TIFF 字节相同，SHA256 `77f7b965733145a6edae173090ba1b9081266c708a3f141a12f8b281af640074`。P023 公开输入接口读取到 1360×1024 的单页 uint8 灰度图。EBI 数据记录和作者原始 README 明确指定 CC0，随附作者说明仅换行有差异。历史人工标注 38 核，固定方法计数 46，练习页将后者明确标为工程复现值。 |
| BCA | 在 P023 私有运行时对解压的 CSV 和 record.json 调用公开 read_plate，读取 28 孔。CSV 的 SHA256 为 `297f027954d555e646c711d4e114277c860087a6382d97e417ac1b5afac276e3`，与板记录相同。S1 对应 C1、C2 两个技术孔，预稀释倍数 10。固定计算返回 5008.680555555556 µg/mL，其他四个样本组的 partial 汇总均为空。 |

核图来源见 [EBI 数据记录](https://uk1s3.embassy.ebi.ac.uk/bia-integrator-data/pages/S-BIAD634.html) 和[作者原始说明](https://ftp.ebi.ac.uk/biostudies/fire/S-BIAD/634/S-BIAD634/Files/dataset/readme.txt)。主审命令为 P023 私有 `runtime/python.exe -I -B .local/check_practice_zip.py`，exit 0。证据为 `.local/practice-zip-review.json` 和 `.local/nuclei-review/receipt.json`。

## 两份 P023 清单与门禁

以 Git 对象逐字节比对。原 PR75 清单在受审提交、合并提交以及本候选原路径的 SHA256 均为 `2cfeea1332cf8764613c14a7aa3b5377d3e59147e5f7cd4df02c046d94ed86df`。收尾提交 `72651ea0` 的另一份清单对应本候选归档路径 `work/evidence/P-023/closeout-integration-context.json`，SHA256 均为 `fab431077d1ff3a5313a68086244809e873ed2fe5a271bd23ba95ad6b0e3e8d9`。原清单指向的 P022 回执与 P024 登记的 P023 收尾回执均匹配各自来源。P023 的 17 个收尾文件和 20 项独审成员也与各自历史来源相符。

在各自基线上运行 `python -m tooling.rule_context check`，PR75 与 P023 收尾为 exit 0，修复前 `3e66248` 因两份活动清单 exit 1，送审提交 exit 0。Git 差异显示产品代码、上游算法、依赖、规则和门禁均无改动。准确 base/head 的 `git diff --check` 为 exit 0。完整对象、摘要、命令和输出见 `.local/receipt-review/p023-manifest-provenance.json`。

## 结果、导出与冷重开

作者用 P023 私有运行时和独立 settings.ini 操作已安装的桌面窗口。独审读取已提交的 walkthrough，并核对对应磁盘文件。WB 的 94 项、核分割的 29 项、BCA 的 33 项共 156 项，实际摘要与冷重开前后两份清单逐项一致。12 个导出文件和 12 份原始界面记录均吻合。用只读 immutable SQLite 核对了四个有 PID 的成功 worker 记录及正式结果摘要。

- WB 两个原图摘要分别对应 Target、Reference。两行正式结果和导出表均为 268125、375375、268125、375375、268125，冷重开记录对应原 Fig。本次学生最短路线走到原始积分。
- 核分割的来源摘要对应 ZIP 内 TIFF，原尺寸 uint32 标签包含 46 个不同的非零实例 ID。导出与新进程重开均对应运行 `3b914b640dde43fdaee28276dccbe484`。
- BCA 正式结果的 28 孔与原 CSV 的孔号、A562 以及配套板记录一致。导出与重开显示同一次运行 `63647dd725694a7ba63805cd3623febe`，S1 在界面按显示精度为 5008.681，导出保留全精度，四组 partial 的均值保留空值。

11 月 6 日 BCA 原生目录框在选定项目前被 Esc 中断。11 月 9 日作者使用新进程、离屏 Qt 控件和软件渲染完成同一项目的读取，脚本、捕获的运行 ID、页面数值和磁盘结果吻合。作者报告首次补验探针访问错误窗口属性后退出 -1073740791，修正后 exit 0 并出现 GLES3 回退提示。留存目录下的 reopen-exit.txt 和 stderr-reopen.log 属于 11 月 6 日，因此 11 月 9 日的退出码及渲染日志按作者报告记载。物理 Windows 目录框的最后确认仍待验证。

独审的首次证据脚本也曾错误要求折叠状态下的首次核结果界面显示来源摘要及运行 ID，exit 1。改为按实际显示的计数及展开来源的导出、冷重开记录核对，保留所有身份和数值检查，最终 `python -I -B -X utf8 .local/evidence-review/verify.py` exit 0。见 `.local/evidence-review/receipt.json`。

## 上游处置

回传前再次查询 [PR76](https://github.com/Junweiiii14/bioimage-tools-platform/pull/76)，base 和 head 与本回执一致。rules-context 和 desktop-environment 已通过，两个平台的 foundation 仍在运行。由规划窗口核对该提交的必需 CI 后按既定流程集成。作者继续持有共享树。审查工作树 tracked clean。

本轮独立执行的是解压、样例再生成、输入读取、BCA 固定样例计算及证据复核。三条桌面流程为作者实测。真人学生体验、算法科学适用性及干净 Windows 安装待各自验收，本轮未重跑模型或安装矩阵。
