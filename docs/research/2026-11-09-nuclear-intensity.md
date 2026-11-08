# 同一批核内，PH3 信号有多强？

**决定：固定标签的单视野强度测量可以进入受限工程 MVP；面向学生的自动分析产品暂缓准入。** 给定配准的核染色图、目标通道原图及同坐标实例标签，成熟库即可导出可追溯的逐核测量。此次只验证一个公开视野的测量环节，未取得学生独立操作记录、实验室样本映射或背景 SOP。产品试用前应在获准的多视野样本中，由实验负责人确认通道、核边界、曝光可比性和背景口径，再让学生独立完成配对、抽查与导出。现有 8 位核计数工具继续按原契约使用。

## 一张原图怎样成为一行结果

官方 HT29 ExampleHuman 图像由 Jason Moffat 提供，压缩包 README 明确图像为 CC0，列出 Moffat 等人 2006 年论文。CellProfiler 软件许可 BSD-3-Clause。只使用官方包的这一个图像集。管线 NamesAndTypes 指定 d0 为 DAPI（DNA），d1 为磷酸化组蛋白 H3（PH3）抗体，d2 为细胞体。核来自 DNA 对象 Nuclei；核内 PH3 使用每个核的全部像素，不使用管线另行检测的 PH3 亮点 ROI。本视野身份保留完整文件前缀 AS_09125_050116030001_D03f00。生物样本、处理组和独立重复的映射均未知。来源于 2026-11-09 核查。[官方示例与下载](https://cellprofiler.org/examples) · [原研究](https://doi.org/10.1016/j.cell.2006.01.040) · [P014 许可证据](../../work/evidence/P-014/license-sources.json)

使用已核验 SHA 的 Windows CellProfiler 4.2.8。官方 14 个模块及参数原样执行，末尾追加 P014 已有的 ConvertObjectsToImage 和 SaveImages 导出 Nuclei 原坐标实例编号。模块的 uint16 模式实际以 int32 存储编号，NPY 和压缩 TIFF 均保留 int32；0 为核外。两通道原 TIFF 均为 512×512、uint8，无显示变换、背景扣除或重采样。SciPy ndimage 按标签从每张 TIFF 直接求像素数、算术平均和像素值之和。面积单位 px²，均值为原始数字值 DN，积分为各像素 DN 的总和（表中 DN·px）；没有可用的物理面积校准或浓度换算。Image.csv 的 Scaling_DNA 与 Scaling_PH3 都为 255；本例对照 CP 均值与积分时，分别将原始均值与原始积分除以 255。[CP 4.2.8 测量定义](https://cellprofiler-manual.s3.amazonaws.com/CellProfiler-4.2.8/modules/measurement.html#measureobjectintensity)

## 原图复算结果

ImageNumber=1 的 289 个 ObjectNumber 与正标签一一对应，面积精确匹配旧官方 Nuclei.csv，零基质心 (x=列, y=行) 在 1e-10 像素内一致。以原图结果为参考，强度相对容差取 float32 的一个 epsilon（约 1.19e-7，绝对容差零），容纳 CP 将每个像素归一化到浮点时的舍入。所有 578 条均值、578 条积分通过。

| 通道 | 逐核均值的视野中位数（DN） | CP 标度最大绝对差，均值 / 积分 | 达到编码上限的像素 |
|---|---:|---:|---|
| DNA | 54.019608 | 1.13e-8 / 3.14e-6 | 全图 2，均在核 7 |
| PH3 | 10.245283 | 1.02e-8 / 1.20e-6 | 全图 0，最大值 245 |

例如核 1 的质心 (477.10, 7.58)，面积 131 px²。DNA 积分 6373、均值 48.64885 DN；相同标签下 PH3 积分 1298、均值 9.90840 DN。用原图与标签 TIFF 按编号定位，完整精度见[逐核表](../../work/evidence/P-032/per-nucleus.csv)、[实例标签](../../work/evidence/P-032/nuclei-labels.tif)与[机器可读摘要](../../work/evidence/P-032/summary.json)。

## 报告边界

核均值反映平均亮度，积分还随核面积改变。触及 8 位上限仅提示可能截断；未触顶也无法证明采集在线性区。非核区包含细胞体，不宜自动当作空白。信号带原始背景，无法据此划定 PH3 阳性或估计蛋白含量。分割与参考测量共用 CP 对象，没有独立核轮廓、抗体或生物真值。视野中位数对每个核等权；289 个核同属一视野，样本列留作 UNKNOWN。在真实实验中先显式登记视野到样本及重复的归属，再按预定规则在各生物样本内汇总；本例不做组间推断。更高位深、配准误差、照明校正与跨批次归一化均需另行验证。

## 回放（Windows）

在仓库根目录运行下列命令，最后一个路径必须为新目录。使用 P014 留存的 ExampleHuman.zip、解压目录 official-human/ExampleHuman，以及未改官方管线产出的 cp-official-human-01/{Image,Nuclei}.csv；[P014 官方运行命令和来源哈希](../../work/evidence/P-014/official-smoke.json)。若另机重建该参考，先用该命令在新输出目录运行原管线。回放脚本校验官方归档和执行文件 SHA、逐字节核对输入、核对旧表，并导出原图坐标标签及逐核表。

```powershell
uv run --locked --no-sync python work/evidence/P-032/replay.py ../p014-research ../p032-replay-new
```

本机 Python 3.12、NumPy 2.5.4、SciPy 1.18.1、tifffile 2026.9.20。初次 CP 启动缺少处理器环境变量，按 P014 做法在子进程填入实际架构。随后核实导出标签的实际 int32 类型，并修正 Windows 下自算表名与官方 Nuclei.csv 大小写碰撞。每次均使用独立新输出目录。
