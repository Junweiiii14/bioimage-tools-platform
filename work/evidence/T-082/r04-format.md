# R04 纯格式阶段

准确提交266c068266179201ec08b9cc1d45eb9a037de248，基线159a51e。仅19个`web_ui/*.js`；无Python、依赖、公式、协议或默认值更改。Prettier3.9.10临时开发工具，使用既有.editorconfig四空格，singleQuote=true、quoteProps=preserve、embeddedLanguageFormatting=off、printWidth=100；保留长模板字面量，不为了行宽修改文本。正式固定工具/最小门禁是后续单独提交。

Espree11.2.0逐文件对比语法树，只忽略位置和Literal.raw拼写，保留实际值、模板raw/cooked、正则模式/flags；19/19相同。摘要/前后行数见r04-format-equivalence.json。app.js由338行整理到2246行，advanced.js155→980；文件长不作为拆分理由。

真实QtWebEngine：`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu uv run --locked --no-sync pytest tests/test_workbench_advanced.py tests/test_workbench_appearance.py tests/test_workbench_lifecycle.py tests/test_standalone_workbench.py tests/test_manual_lanes_workbench.py tests/test_crop_edit_identity.py -q --tb=short`（Windows进程环境设置，无全局改动），**19 passed / 74.29s / exit0**。软件渲染与现有quality.yml一致；GPU历史失败仍保留。没有因格式修改旧行为测试或增加格式专用产品测试。

非作者绑定266c068→159a51e独审：**Accepted**。独立直接从两提交读取19文件，以Espree重新比较AST及注释正文，19/19一致/exit0；代表性diff和空白检查通过，未重复UI或改文件。此结论不覆盖后续质量门禁。

工具初选已核官方Prettier、ESLint配置和TypeScript checkJs文档。临时固定Prettier3.9.10/ESLint10.13.0/TypeScript5.9.3，Node26.7.0/npm11.19.0；npm audit当时79依赖0已知漏洞，仅开发工具。正式package-lock/CI/负例验收待下一工作单元，不把临时安装当已建门禁。
