# T-009 OCR/自动表后端子阶段

Windows/Python3.12.14/uv0.13.0，base34831e4，feat/T-009-fig-ocr-table，2026-10-14。

- 只读核对原OCR源码/模型，source SHA见reference-source.json；旧目录没有修改。
- 临时隔离环境实际RapidOCR3.9.2/ONNX1.31/OpenCV5与现有NumPy2.5.4兼容；六标签/两Fig正确。
- 三个PP-OCRv6模型SHA与旧软件相同，模型随固定PyPI wheel分发，没有模型/私有图进入Git。
- `uv lock`/`uv sync --locked --all-groups`：0。增加11项OCR依赖，无现有第三方版本升级；WB模块0.6.0。
- `dev.py check --all`：0，199tests、Ruff/format/Pyright strict、9合约、4wheel5安装场景。
- core WB普通API不加载rapidocr/onnxruntime/cv2；通用宿主不加载WB/NumPy；带OCR的安装场景真实识别Fig1A/AKT通过。
- socket.connect禁止时实际OCR仍通过；缺模型/错误SHA在engine初始化和源读取前拒绝，无自动下载。
- 实际OCR→Fig/行建议→四泳道八绑定→矩形解析积分→确认后自动单元格3045/1995；未确认/未关联/缺失/排除/真实零不同。
- ZIP/XML检查、字面`=1+2`不成公式、已有XLSX拒绝且字节保持；独立bundled openpyxl3.1.5验证两Sheet/Unicode标题/数值。
- WB0.6.0元数据更新后重新隔离构建安装全部四wheel/五场景，结果见命令完成记录。

未运行：独审/远程CI/最终包态；未完成：OCR专用worker/Qt复核实时写表、文档保存重开/旧兼容、跨图拼图关联。
导出目前需支持硬链接的文件系统，FAT交付方案待补。六标签不是通用OCR准确率或用户标注验收。
算法积分/worker/工作区v1未变化；新OCR预处理与空间建议有各自版本ID。没有新增skip、xfail、类型忽略或更改旧数值容差。

## 完整桌面阶段（2026-10-14，后于上述后端记录）

本轮从184d018继续，wb-tool0.7.0/bioimage-app0.2.0。`dev.py check --all`退出0，205测试（59.00s），Ruff/format/Pyright strict、9导入合约、4wheel5场景通过。增加隔离安装产物真实`--worker wb_ocr`进程检查。

Qt用例实际经过本地OCR worker，验证同图和独立拼图、先OCR后ROI、显式跨图单元格绑定、数值自动写入、名称修正/空名拒绝确认、XLSX、v2保存重开、ROI修改清值。新增严格OCR协议/source/revision/attempt/重复JSON/取消及模型版本守卫；v1文档继续读取，v2/schema快照通过。

对新真实资料只读探针：短编号/并排标签布局@2返回长图16组；另图高置信Fig1C误读Fig1G。未冻结真值，不计算准确率。私人OCR/提取/预览仅.local。Windows新文件发布使用无覆盖rename，物理FAT未测。

完整检查后修正表格重绘选中位置变量被覆盖，补相应桌面断言；定向桌面8项/Ruff/Pyright再检查。没有放宽数值容差或新增skip/xfail；文档测试由v1专用读取改版本分派，仍测试v1历史兼容。uv.lock仅两个本地包版本变化，无第三方升级。独审/远程CI/最终产品打包仍未运行。
