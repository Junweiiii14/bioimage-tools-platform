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

## 扩展回归与独审修正

- 95项扩展最终：.local/T077-targeted-final.xml/log，95 passed /97.01s /exit0；覆盖既有平台、导入、WebUI及输出/归档兼容。随后仅两处一次索引优化和显示格式修正，相关11项/8.18s/exit0复验；最终全门禁由PR38当前HEAD CI执行。
- 独审已复现CSV中点与Intl不一致（1.005/2.675/1.125），4ca8f50改Decimal(str)+ROUND_HALF_UP，8边界+2适配器10项/2.28s/0。不改变raw值和定量。XLSX由有可选小数点的格式改成按每值可见位数明确0/1/2位，质量星号各有格式；端到端测试现读取实际numFmt选择解释格式后逐格比对，不再忽略工作簿格式。
- rules-context首轮FAILURE：默认回执base=origin/main，而PR38实际base是T076 6b6afd5；按支持的--base参数重新加载全部适用规则与任务并生成回执，未手改回执、规则或成功状态。最终检查待CI。
- Ruff/格式/Pyright、policy、Start-BioImage.ps1 --verify-launch、smoke-env均exit0。smoke-env仅环境，不外推安装验收。
- 全合成安全素材已独立复制 .local/deliveries/WB-T077-safe-demo，106文件/5,425,611字节逐项SHA一致，原图shape300×700 uint16且像素集合为本测试生成值。尚无视频聊天，须等最终独审与CI。

## 最终收口

- ddc6290：20项/13.87s/0，独立20项/11.78s/0；5张有效截图，新增hover修复原浅底浅字问题，保持深底+outline。一次19过1失败定位为页面快照就绪条件不足，现等真实10个raw值入页面后保留原内容断言。
- 自动结果目录也统一可见measurements.csv/xlsx；旧完整审计单列measurement-audit.csv/xlsx并写index.table_policy=intake_visible_table@1，ZIP内部旧表不动。既有9槽/数值/来源审计断言原样保留，仅改读取的新审计文件名；属于授权导出布局变更，非弱化答案。端到端比较自动与直接主表CSV字节、XLSX主表XML和styles，审计修订与容器时间戳可不同。初次整XLSX字节比较21过1败/11.39s/1，不是稳定容器不变量，已按实际主表/格式边界修正。

## 最终绑定证据

- 产品c32ad11，作者输出/旧恢复相关22 passed /11.67s /exit0；非作者24 passed /12.16s /exit0，独立39成员及严格旧ZIP恢复相等。独审Accepted、有限静态ship，报告已随本次证据提交；之后只有Markdown/交接变化时该产品结论仍以产品文件相同为条件。
- 最终安全演示目录改为.local/deliveries/WB-T077-safe-demo-c32ad11（旧副本保留），108文件/5,432,183字节逐项SHA相同，包含新自动可见表与独立审计。启动指针检查仍exit0。
- PR38：当前产品HEAD规则回执/桌面环境SUCCESS，Windows/Linux完整CI运行中；最终证据HEAD必须实时核验，不在此写未发生的成功。最终JSON存.local/T077-final-ci.json；缺codex/codex-automation两个标签，未伪造存在或另造标签。
- 本地未再运行dev.py check --all，完整全量/隔离wheel由最终必需CI执行；未运行audit（无依赖变化）、干净机/物理Explorer/OLE/外部表格软件验收，均不写通过。
