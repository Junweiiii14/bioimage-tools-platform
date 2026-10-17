# F-006 当前版本展示和使用报告

- 状态：done
- 产品基线：1e6cd5ab02968dc7493b2cecc5b3625564f23b8d；文档HEAD ffdcdbd。
- 用户请求：把目前成果交给用户查看，并提供说明现状与使用方法的报告。
- 范围：本地合成演示工作区、启动脚本、中文报告及交接；不修改产品功能、不覆盖原资料，不发布软件。
- 输出：.local/deliveries下独立目录，Word报告及可用预览，真实Qt开发版窗口和可双击启动脚本。合成数据明确标注，不计真实科学验收。
- 验证：实际启动/加载/计算/保存/成图，报告渲染逐页检查；不重复无关全产品测试。

## 交付与验证

- 目录：C:/Users/70236/.codex/worktrees/t021-coordination/bioimage-tools-platform/.local/deliveries/WB-preview-20261015-2。
- Start-WB-Demo.cmd打开合成演示；Start-WB-Empty.cmd打开最新开发版空窗口，依赖当前本机worktree和venv，不是最终免Python安装包。
- 演示通过公开API生成两张合成16位图、三泳道及缺图占位、schema7明确分段与定量计划；真实后台运行后，SQLite只读核验2条succeeded，另有成图PNG及示例模板。未使用私有实验图，未覆盖旧资料。
- 已启动可交互Qt窗口；view_current.py只在本地合成工作区加载/计算/保存/成图。窗口截图来自当前程序，源码未变。保存/预览后结果可能需点击“刷新项目表”，报告明确操作。
- 中文Word报告与PDF共7页，包含现状、试用、导入裁剪、三类坐标、原图定量、归一化、版式分段、模板、OCR、导出及当前限制。documents技能authoring标记已运行，原生Word导出PDF，Poppler渲染全部7页逐页查看；无截断/孤页，标题默认蓝线已移除。
- 默认render_docx因缺LibreOffice退出1，未把失败写成通过；改用本机Word原生导出退出0。首次排版8页末页孤段，修订后7页。演示准备首次调用import_asset遗漏expected_sha256，退出1；只修订本地生成脚本后新建独立目录成功，产品源码未修改。
- usage_check子代理只读核对实际按钮/坐标/模板边界，未参与产品实现。此轮未重跑490项产品测试、独审或远程CI；历史产品证据仍绑定1e6cd5a。
