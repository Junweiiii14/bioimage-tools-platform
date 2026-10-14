# 项目结果 CSV 与统一归档 v2

wb-tool 0.16.0 / bioimage-app 0.11.0。项目 schema v1–v5、积分和归一化公式不变；旧 PNG provenance / manifest.json schema v1 保持。新 ZIP 的 archive.json 标识 `format=wb_project_archive/schema_version=2`。这是可检查的导出格式，尚未提供 ZIP 导入，也不把历史 RunRecord 当成本工作区的进程退出或成功提交收据。

## 结果格式

三个公开导出函数按 `.xlsx` / `.csv` 后缀选择；新增可选 cancelled 回调。项目原图行、OCR 标签、归一化原图/OCR 标签视图共用原有填表函数和表格行构建器。只有经结果验证、当前来源/标注/审核匹配的值才输出；4000 与真实 0 保留数值，缺图、未运行、未确认、过期、排除、失败、不可用均为空并带状态/原因。名称重复不合并，行/lane/band/run/SHA/请求修订仍独立。

XLSX 保留宽表及来源表、字面文本与数值单元格。CSV 使用 UTF-8 BOM、逗号、CRLF、标准双引号转义，一条记录对应一个泳道：

- source：项目 ID/修订、算法/单位，加原 XLSX 来源表的行 ID、Fig、蛋白、泳道序号、原图 SHA、lane/band、请求修订、运行 ID、积分、状态/原因。
- ocr：项目 ID/修订、OCR 源/运行/引擎、算法/单位，加 OCR 行 ID、Fig、蛋白、目标行、泳道、原图 SHA、lane/band、定量修订/运行、积分、状态/原因。
- normalization：项目 ID/修订、算法、标签来源、OCR 源/运行，加原 XLSX 结果全部列，再加前缀为 `来源_` 的来源表全部列。包括目标/参照积分、比值、对照均值、相对值、各状态及目标/参照 row/ROI/SHA/run/lane/band、确认与备注。

CSV 文字编码为 `wb_csv_text_prefix@1`：所有数据字符串（包括空字符串）前置恰好一个 `text:`；去掉一个该前缀即可恢复原文字。受控表头不加前缀；数字不加前缀、无引号，None 为空字段。故文本 `00123`、等号、引号、逗号、换行与已有 `text:` 均可区分、还原，不能误认成数值或公式。CSV 自身无类型系统；导入程序须按此契约解码，通用查看器可能显示前缀。需要原标签直接展示时使用 XLSX。见[技术依据](../research/2026-10-14-wb-csv-archive.md)。不依靠 CSV 的引号充当公式转义。

## ZIP 内容及校验

| 路径 | 内容 |
|---|---|
| project.json | 精确保存修订的完整项目：行、模板、候选、标注、运行引用、OCR 原文副本/人工关联、归一化配置 |
| figure.png / manifest.json | 原有显示拼图、行来源/ROI/输出框/映射记录；PNG 不能代替原图定量 |
| crops/0001.tif 等 | 原通道/位深/数值裁剪；缺图行无裁剪 |
| assets/SHA256 | 原图、自定义字体、可选 OCR 源；原始文件字节 |
| tables/source.csv、source.xlsx | 必有，未配置/无结果也带明确状态 |
| tables/ocr.* | 存在 OCR 状态时提供；证据不可用则不填有效值 |
| tables/normalization.*、normalization_ocr.* | schema v5 提供原图表；有 OCR 时另提供 OCR 标签表，未配置则仅表头 |
| runs/0001/run.json | 项目声明的历史运行记录，和验证状态分开 |
| runs/0001/request.json、result.json | 原始已核验请求/结果资产字节；未核验的不写入 |
| README.txt | 格式、恢复文字、数值与信任边界说明 |
| archive.json | 每成员 path/SHA256/size_bytes/role、run 的验证状态/原因及对应文件、格式和修订 |

成员摘要针对实际写入字节计算。原图/字体/OCR 源同时比对声明 SHA 和字节数。index 不列自身（不能自包含自己的 SHA）；其余成员全部登记。压缩内容不含模型二进制；已验证 OCR result 保存引擎/预处理/模型 SHA/token/位置/置信度。摘要只能检测损坏，不提供签名或真实性保证。

桌面在精确保存后，逐个通过存储线程核对 Workspace RunRecord 完整内容并解析资产路径；WB 后台重新读取请求和结果，检查 SHA/大小、严格 JSON、项目修订/定量请求/OCR 来源与保存副本。不能只用显示缓存。坏 run 独立记录 `unavailable` 和原因，其行不填值；其他有效行继续。已核验失败/取消/中断记 `terminal_without_result`，保持实际终态；成功结果记 `verified_result`。后者仅表示资产与声明一致，不代表当前 ROI/人工关联仍有效，表格继续显示 stale/unconfirmed 等状态。缺失请求时即使结果缓存存在也不输出有效数值。

公开低层 API 的 ArchiveRunEvidence 是宿主提供的已匹配运行与路径，API 不连接数据库；未提供证据的 run 记录不可用。不复制整个历史数据库或全部编辑历史，处理证据限当前修订引用的运行请求/结果。重开工作区仍走原存储验证；ZIP 的跨工作区恢复需另行设计外来历史证据信任，不伪造本机 PID/退出/提交。

## 生命周期与预算

文件读取、压缩、表生成在后台；GUI 忙时冻结编辑。取消、关闭或 generation 改变通过 Event 取消，保存阶段的后到修订不启动导出。检查覆盖成员/1MiB写块/最终发布前；若发布先于取消完成，保留已完成文件。新文件同目录临时写入，fsync 后 Windows 无覆盖 rename / POSIX link，失败清理本次临时文件；不覆盖任何已有输出、源图或历史结果。

每表200000单元格，表文件64MiB，CSV文本32MiB字符预算/每字段32767字符；XLSX原有UTF-16限制保留。冻结请求16MiB，单定量结果8MiB/OCR4MiB，累计加载结果64MiB；超出则明确不可用，不用旧缓存替代。ZIP最多4096成员、单成员512MiB、解压后总计2GiB；PNG与渲染仍沿用64MiB/3200万像素。预算是应用准入，不是OS内存硬限制；大型项目性能与物理FAT仍待实测。
