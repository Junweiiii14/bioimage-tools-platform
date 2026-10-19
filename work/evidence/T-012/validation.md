# T-012 自验记录

- 基线 cfe0c56，分支 feat/T-012-figure-project；Windows/Python3.12.14、Qt6.12.0、Pillow12.3.0、NumPy2.5.4。源码版本wb-tool0.9.0/app0.4.0。实施提交见该分支包含本记录的commit；未推送/PR/合并。
- `uv run --locked --no-sync python dev.py check --all`：退出0，230 tests passed（63.06s）、Ruff170文件、Pyright0、9导入合约、4wheel/5安装场景。安装产物验证两个真实窗口异步关闭、实际拼图ZIP导出，既有定量/OCR worker和真实离线OCR仍通过。全日志留ignored `.local/requirements-review/t012-full-check.log`。
- 新增12用例（10项目/导出、2Qt）：不同Fig/N/宽度、重复蛋白名、缺图/空位、16位解析像素、PNG元数据/原值TIFF/原图SHA、review门禁、严格JSON、宽高/N不一致、缺路径/源损坏/取消前和归档中途取消、无覆盖、真实表格拖框、旧来源删除后工作区重开、模板复用。现有旧v1/v2文档及单图GUI全量保留。
- `uv run --locked --no-sync python .local/requirements-review/probe_figure_import.py`：退出0。实际用户项目10张原始TIFF通过批量导入、草稿保存、关闭重开，10个不同SHA全部保留，外部原文件SHA前后相等。未自动选择哪种仪器导出做定量，也未擅自确认真实蛋白身份或ROI。
- 实际QWidget截图已查看：表格、审核勾选、中文流程和两行拼图没有裁切；私人/生成截图仅留.local。Qt截图不代替像素或科学验收。
- 初次静态检查修正了星号表达式括号、Qt render同名覆盖、闭包可空来源和测试第三方类型边界；无数值预期/容差/skip/xfail放宽。安装检查只增验证，未削弱旧门禁。锁文件只改本地版本和对已锁Pillow的extras声明。
- 限制：自动候选、项目OCR/定量/归一化、ZIP导入/直接TIFF拼图、横向分段、独立审查/远程CI/最终Windows产品包未完成。原有Qt原生Aborted没有在本轮出现，但根因仍未知。
