# WB 命名项目交付 v1

T080：`intake_delivery@1`；仪器清单内部 schema5，外层项目 schema10–14 不变。
原 schema1–4 未配置交付时的序列化字节不变；新清单保存
`delivery.legacy_schema_version`，计算与确认摘要按该历史版本重建，剔除交付位置。
选择输出位置不会使原始定量、已确认来源或历史运行失效。旧程序不应写入新清单。

## 公开入口和阶段

- `prepare_intake_delivery(project, output_parent=..., workspace_path=..., delivery_id=...)`
  是纯准备，保留项目运行时类型。允许未确认草稿保存输出位置；活动阶段不能换代。
  宿主先保存当前配置并完成 CAS，再调用文件整理；不能依靠未保存的页面文本写目录。
- `plan_intake_delivery(project)` 给出稳定 Fig/蛋白身份、完整组内来源、未分配来源及
  命名计划摘要。目录保留中文标签、序号和稳定 ID 的短摘要；非法字符与 Windows
  保留名安全转换。完整原名、来源相对路径和摘要保存在文件名对应表。
- `materialize_intake_delivery(project, sources, workspace_path=..., row_id="", cancelled=...)`
  在 worker 创建属于本代的命名目录、复制全部组内原图及未分配来源。
  `row_id` 指定已成功 CAS 的裁剪行时立即归位其原值 TIFF 与显示 PNG/TIFF。
  空 `row_id` 还补齐当前已完成行，支持中断后继续。不能把待审核、失败或无资产行
  宣布为已完成裁图。`IntakeDeliveryReceipt` 绑定项目、代 ID、计划摘要及行 ID。
- `finalize_intake_delivery(project, sources, workspace_path=..., runs=(), ticket=None,
  cancelled=...)` 在同代目录封存。复用现有 `intake_output@1` 的资产/运行证据冻结、
  ZIP 生成与完整性判断；分 Fig 表读取这次冻结的运行副本。返回原有
  `IntakeOutputPreparation`。索引真实导入资产并 CAS 登记后才完成 export 阶段。
- `inspect_intake_delivery(path, cancelled=...)` 验证成员集合、每个 SHA/字节数、路径及
  恢复 ZIP 存在后，返回 `项目恢复.zip`。宿主随后仍执行标准 ZIP 验证与新工作区恢复，
  不把目录索引视作科学结果可信证明。哈希按 1 MiB 块响应取消。

## 目录和命名

```text
项目名_稳定ID_本代ID/
  .wb-delivery.json
  项目说明.txt
  Fig组/
    01_Fig名_稳定ID/
      01_蛋白名_稳定ID/
        原始图片/                 # 该采集组全部来源，保持原字节
        原值裁剪/                 # 已完成选中来源，以及证据明确的同坐标信号来源
        展示图片/                 # 独立显示用 PNG、TIFF；不进入定量
        裁剪与来源记录.json
      Fig名_稳定ID_拼图.png / .tiff
      Fig名_稳定ID_灰度.csv / .xlsx
  未分配来源/                     # 未进入蛋白行的原始来源，不猜测归组
  完整拼图.png / .tiff
  灰度汇总.csv / .xlsx
  项目恢复.zip
  记录/                           # 完整名称映射、标准项目/清单/状态、审计表、run证据
  index.json                      # 最后封存；complete 和 errors 来自真实验证
```

未完成项目可能没有相应拼图或恢复 ZIP。缺失仍显示缺失，表格空值不变为零。
逐 Fig 表按稳定 Fig ID 过滤当前可见表，保持蛋白/槽位顺序；同名身份不合并。
CSV 使用现有可逆文本规则；XLSX 保留现有可表达格式、数值与审计，未审核不阻止导出。

对应辅助裁图仅允许：与选中来源完全相同 SHA 的重复原图；或
`instrument_guided_geometry@2` / `guided_common_band_geometry@1` 的
`registered_signal_pair@1` 证据同时绑定全部三图 SHA、单一导图 SHA 和同尺寸。
导图本身不因同尺寸获准裁剪；白光与坐标未确认来源仅保留原图并明确原因。
选择来源本身的成功裁剪不依赖辅助来源能否裁剪。

展示 TIFF 的 ImageDescription 用 ASCII 转义 JSON，解析后完整保留中文来源警告，
符合 TIFF ASCII 标签要求；PNG 继续使用原 UTF-8 JSON，同一图两种格式的解析内容一致。
这不改变显示像素、原值裁剪或文件名；也保持先前 TIFF 失败前已发布 PNG 的字节，
允许同代校验后继续补齐 TIFF。

## 不覆盖、恢复与异步边界

输出位置和原工作区锚点随项目保存。恢复/移动到另一工作区后，旧绝对路径仅作为历史
说明；默认改用当前工作区的 `outputs`，必须保存新交付代才能继续写出。
仅默认 `outputs` 可由 worker 建立；用户选择的父目录必须存在。
拒绝链接/junction、越界成员、已有非本代目录及不同内容文件；不覆盖任何原始或历史
产物。生成文件采用独占暂存和无覆盖发布；同代重试仅接受相同字节。
输出被封存、名称/分组改变、已归位裁剪或显示配方改变后均创建新代；用户主动输出
当前快照始终新代。取消保留已成功发布文件，未封存目录不宣告完整。

新目录初始化、复制、裁剪显示、冻结、哈希和封存均在 WB worker。
宿主按 session key、generation、revision 与交付身份拒绝旧回复；配置 CAS 失败不启动
目录整理，裁剪资产 CAS 失败不启动其归位，归位失败停止推进并显示实际错误。
标准 `export_intake_outputs` 及其历史 ZIP 布局继续可用；此契约为新增阶段交付布局。

本契约不表示已通过科学准确率、干净 Windows 安装或最终发布验收；以 T080 任务和
绑定提交的验证、独立审查记录为准。
