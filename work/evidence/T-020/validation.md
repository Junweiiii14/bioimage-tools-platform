# T-020直接TIFF/PNG成图验证

日期2026-10-14；分支feat/T-020-direct-figure-image，起点3a38af660e8bbb30f319efa36cbd60489c73ebac。作者自验，独立审查尚未执行；整体WB软件未完成，Goal active。

## 实现

wb-tool0.18.0/app0.13.0；platform-runtime保持0.2.0，第三方依赖不变。直接TIFF/PNG使用同一完整RGB8渲染/来源记录，TIFF单页未压缩contig、ImageDescription JSON、Software标记及INCH/DPI。沿用原显示映射，不改变原图/裁剪/积分/归一化或项目schema。原图/字体增加声明字节数核验。

公开export_figure_image延迟导入；后台自有暂存写入/关闭/fsync、完整像素与标签重读后无覆盖发布。PNG64MiB/TIFF128MiB/来源16MiB、完整3200万像素/32768边长。已知显示TIFF拒绝定量，专用OCR入口允许；不能判断被去掉来源标记或未知第三方图的实验身份。

桌面独立成图按钮先保存精确修订，再启动后台任务。保存期间的取消/关闭也要检查，不能由新任务清除取消事件后继续输出。渲染期间修改/取消/关闭不发布，已发布文件保留；错误可见，未审核或已有目标不覆盖。

## 检查记录

| 命令/检查 | 结果 |
|---|---|
| dev.py context --task T-020，WB/app/tests/tooling/docs/work/handoff/lock范围 | 实施前记录；module-map改动后再次加载/读取，回执rules-context.json |
| TIFF内存最小实验：2×3×3 uint8、300dpi、ASCII JSON与Software | 402字节，tifffile与Pillow像素相同，RGB/INCH/(300,1)/来源正确 |
| pytest tools/wb/tests/test_figure_image_export.py tools/wb/tests/test_figure_project.py -q | 28通过，1.21秒（18新增+10原有） |
| pytest tests/test_figure_image_ui.py -q | 9通过，17.48秒；真实WB/OCR进程与Qt保存/重开/关闭 |
| Ruff相关文件、Pyright | 通过；初始新增测试类型告警已用显式类型、FreeTypeFont检查、QTest和typed helper修正，无新增ignore |
| uv lock --offline；uv sync --locked --offline --all-groups | 退出0，锁文件只改2个本地包版本，无第三方升级 |
| dev.py check --all | 退出0；425测试143.71秒，Ruff251文件、Pyright0、9合约、4个wheel/4个隔离安装环境通过，含新增直接TIFF/PNG验证 |

完整日志.local/requirements-review/T020-check-all.txt；专项T020-core.txt/T020-ui.txt/T020-types.txt。PYTHONUNBUFFERED=1及PYTEST_ADDOPTS='-o faulthandler_timeout=20'仅用于诊断，没有改变通过标准、旧科学期望、skip/xfail或门禁。新增PNG DPI检查0.013容差源于整数像素/米半步舍入0.0127 dpi；科学像素与原数值仍精确比较。

新增27用例覆盖完整16位显示映射/原文件字节、字体与源声明大小、元数据/DPI/错误编码像素、来源标记两种识别、未知第三方TIFF保持原解码、未审核/坏SHA/缺路径/已有文件、校验后取消及发布目标竞争。Qt路径使用宽度超过2048的完整成图，导出的TIFF真实OCR后明确关联/确认得到原积分4000，排除仍空、有效0保持，归一化0.5及重开一致；生成图不进入量化源列表。保存回调和渲染阶段取消/关闭/编辑、发布后关闭均有用例。

## 真实资料与视觉检查

只读用户00060322.tif（SHA23936d91…eddcb9d、1347×902），以全幅几何包装检查导出。N=1仅测试容器，reviewed仅表示已知全幅几何，不是生物泳道或科学审批。TIFF/PNG为1577×988、300dpi、完整像素与来源相同，原画面显示灰度逐像素相等，原SHA保持。真实离线OCR17 token含包装文字，0确认/0绑定，无定量运行，4.07秒不是性能基准。

私有探针脚本/JSON/图片留在.local/requirements-review，未提交用户原图。已查看T020-user-display-c64a3852/display.png与QWidget.grab的T020-direct-image.png：完整拼图、直接导出按钮、OCR关联/值4000/缺失/0可见。未调用原生CUA或执行用户提供的旧工具程序；没有真实OCR准确率结论。

未完成：绑定最终提交的独审、远程CI/PR/main集成、实验室版式/横向分段/模板库（T-021）、缩放句柄、旧工具实际衔接、真实实验标注/效率评价、大项目性能、Windows最终包/干净机/DPI/物理FAT/签名许可证。旧Qt原生中止与T-017停滞根因仍UNKNOWN，本轮通过不能宣称已解决。

产品提交：1258d64ad3d26d2c05fa0c1a5f590e7e637ed5f1；本地提交，未推送/独审/发布。提交钩子Ruff检查、格式与Repository policy均通过。
