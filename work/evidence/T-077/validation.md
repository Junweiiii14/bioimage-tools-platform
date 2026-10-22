# T077 验证记录

环境：Windows 11，本机 CPython3.12.14、PySide6/Qt6.12、锁定工作区 uv0.13.0；活动树 wb-ui-system，基线6b6afd5。原 ResearchVault dirty树不改。无依赖/锁文件/算法/项目schema/门禁变更。

- 最新相关12项：`uv run --locked --no-sync pytest tests/test_folder_drop.py tests/test_visible_export_desktop.py tools/wb/tests/test_intake_visible_export.py -q --tb=short --show-capture=no --junitxml=.local/T077-regression2.xml`，12 passed /13.25s /exit0；QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu，QPA为本机Windows。10条QDragEnterEvent旧构造API警告保留，未屏蔽。
- 真实Qt焦点子控件接收URL drag enter/drop，CopyAction；中文双目录、1.0/1.5页面zoom、文件/失效目录/空目录/远端链接、忙态及真实界面草稿保护。真实图像扫描/存储建项目，不是仅mock回调。
- 两张独立合成原图（uint16，倾角±3°、5槽、故意dtype最小值质量警告），经当前页面配置→真实裁剪/成图/worker/提交→未人工审核结果；10个原始积分均出现在XLSX/CSV且逐格匹配可见表，含6个质量星号。XLSX保留原始double；CSV去一个text:前缀后与显示文字完全相符。导出后结果继续显示。缺项/真零、坏证据、无覆盖/取消另有适配器回归；原图字节与历史ZIP不变。
- 1440×940与960×640共4张静态Qt截图均已逐张打开，内容/字体/表格/目录提示可见。软件渲染不证明物理鼠标、Explorer OLE全过程、硬件GPU或目标机DPI。
- Ruff检查/格式、Pyright最终结果及扩展回归/远端必需CI待最终补充。独立审查未执行；不把作者自验当独审。

## 保留的失败与调整

1. 初始fixture错误调用不存在的desktopSession.current，停止该轮并修正就绪条件；随后目录9项通过。
2. 适配器夹具是已审核的解析样本，不能假称未审核；真实未审核验收改用原生桌面实际运行，加入dtype最小值使旧有效值为空的条件真实成立。预期400/800/缺项来自原有解析夹具，未改容差或门禁。
3. 首轮扩展95项：94pass/1fail/102.82s/exit1（.local/T077-targeted.log/xml）；假造draft被页面心跳覆盖，改为页面按钮真实建草稿。首次单端到端因未等待busy回执而点禁用按钮，修为等待真实可操作条件。
4. 截图初轮抓到未绘制/过期帧，未作为通过证据。一次可选QWebSocket截图探针出现0xc0000139日志并结束于后置结果为空超时；该测试截图实现已移除，没有修改产品依赖或屏蔽异常。改为等待静态已绘制帧后Qt抓图。GPU/mailbox警告保留，不宣称根因已修复。
5. 后置截图断言确认真实产品缺陷：保存的WBIntakeProject分支清空结果后不重建。最终结果项目改走既有refresh_project_table后续链；最初漏导入类型造成4fail/8pass/1error，已补正确公共API导入，随后12项通过。原有断言未删除或放宽。

## 范围限制

现有971d860安装目录未重建；运行修正版用本活动树Start-BioImage.ps1及锁定环境。未合并main/发布。干净Win10、物理Explorer鼠标/DPI、科学留出和历史native UNKNOWN保留。CSV沿用文字前缀协议，不虚称支持工作簿样式。
