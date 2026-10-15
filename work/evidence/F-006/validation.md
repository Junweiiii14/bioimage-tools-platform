# F-006 当前版本展示和报告验证

- 日期2026-10-15，Windows/PowerShell；产品代码1e6cd5a，文档基线ffdcdbd。
- context --task F-006 --scope .local --scope work --scope .agent-handoff --record退出0，输出已读。
- .local/prepare_preview.py最终退出0；合成工作区/模板/脚本建立成功。首次遗漏import_asset参数的失败保留于任务记录；未改产品。
- 启动实际开发版Qt窗口，ready.json确认已载入wb-demo-20261015；只读SQLite检查2个run均succeeded；demo-figure.png和demo-layout.wbtemplate存在。verification.json保存在交付目录。
- 通过捆绑Python/python-docx生成报告；默认render_docx失败（本机无LibreOffice）。使用已安装Word COM专属不可见实例打开本次文件并ExportAsFixedFormat，退出0，关闭本次文档/实例；未操作其他用户文档。
- PDF经捆绑Poppler渲染，7页均已view_image逐页检查；无可见标题蓝线、孤页、表格截断或重叠。DOCX标题/各级标题黑色；界面图为合成演示截图。默认模板残留的未使用样式边框不在成品标题显示。
- 报告Word/PDF、两个启动脚本及Read-Me.txt在独立交付目录；产物/工作区/日志均留.local，不提交私有图或生成软件包。
- 使用documents与pdf技能及捆绑依赖；usage_check只读核对按钮和坐标。产品源码/依赖/门禁未变；不重跑无关产品全门禁，不新增真实科学/包态验收结论。
