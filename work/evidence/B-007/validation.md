# B-007 交付验证

范围：研发设计、来源与数据登记、HTML、轻量公开数据样本；未修改产品实现，未执行科学算法或产品验收。

- 主目录：`feat/T-021-laboratory-figure-layout`，HEAD `bb5601addda64fa96fa007612ceda0a0e1ed9b74`，既有dirty保留。实际产品只读基线：`codex/t082-reliability-remediation` / `dfc48ed7c2c944dc8f03c3931bc7985452a31393`，由设计审计及收尾复核确认clean。当前安装/冻结产品未替换。
- Windows、PowerShell；文档构建使用已有bundled Python/Node、marked、Playwright及本机Edge。未安装/升级依赖。
- 用户要求的十类路线逐项调研，登记17条具体数据记录（含受限和失败候选），不把来源数量当科学验证数量。

|检查|命令/证据|结果与边界|
|---|---|---|
|规则上下文|`uv run --locked --no-sync python dev.py context --task B-007 --scope . --record`|建立并读取；最终入口更新后重新记录，见rules-context.json及任务卡|
|代码/视觉事实|01-existing-design-language.md；较新树27项文件/行映射；历史T077图及HEAD差异|沿用字体/四主题/双密度/顶栏步骤/工作区/抽屉；历史截图不冒充当前产品运行|
|工作流审查|workflow-review.md及architecture-review.md|问题定向修正，审阅绑定最终Markdown摘要；作者部分与独审范围分别声明|
|数据清单|`python work/evidence/B-007/combine_datasets.py`|退出0；17唯一记录、15必需字段、十场景覆盖；JSON/CSV同源。许可/访问/下载/解析/准入分开|
|实际文件|sample-download-verification.json；flow与RDML各provenance|五数据文件合计8,103,748字节；图像单文件解码、ZIP目录、FCS头/MD5、RDML结构核验；不是算法准确度验证|
|来源许可补核|probe_record_licenses.py及license-html-probe.json|普通HTTPS原HTML补核三条Zenodo rights/JSON-LD的CC BY4.0；先前文本提取漏项已更正，无绕过权限|
|HTML构建|`node work/evidence/B-007/build_html.cjs`|退出0；13章、49表；嵌入已有Noto Sans SC及OFL许可；单文件约24MB，离线字体不另发网络请求|
|文档完整性|`python work/evidence/B-007/validate_blueprint.py`|退出0；3 JSON示例、6节点说明DAG、标题层级/锚点/本地证据链接/两份HTML相同；未将示例当产品执行|
|图形与交互|`node work/evidence/B-007/verify_html.cjs`|两轮限定检查均退出0；1440×1000及390×844无页面横溢，搜索/空结果/跳转/菜单收放正常；打印样式正文可见；0 JS异常、0外部HTTP请求；最终字体已加载|
|设计机械检查|`impeccable detect --json docs/plans/research-platform-rd.html`|仅运行一次，实际退出1；报告48个table-wrap无wrapper内边距提示。单元格实际padding13px 15px，截图确认文字不贴边，属于wrapper误报；未改规则抑制。最后仅内容增加一表，未再运行detector；最终表格结构/样式同源且由HTML检查核对|
|数据包|`python work/evidence/B-007/package_samples.py`|退出0；12归档项，CRC与逐文件SHA256全部一致；约7.1MB。仅公开小样，无私有数据/大模型/安装包|
|计划入口|`uv run --locked --no-sync python work/programs/scientific-agent-platform/check_plan.py`|退出0；P001–P006保持planned，依赖候选仅P001；不代表实施授权、科学通过或用户签字|
|历史保护|B006旧HTML SHA256；v2源快照|旧HTML仍a70449be…c49，v2源仍dee99565…5e2；B006交付未覆盖|

最终源/HTML/登记表及数据包SHA分别见document-validation.json、dataset-validation.json、package-validation.json；不在多处手抄摘要作为第二真源。

未运行：`dev.py check --all`、产品启动、真实worker端到端、全部实验算法、方法准确率、目标机器安装、云端服务和Agent部署。本轮不修改产品，文档验证不能替代这些阶段验收。

研究中遇到网页502/404、二进制文本工具不支持、API403、个别网络超时，已在对应数据记录标记并寻找正常公开来源；公开记录仍不可取得的保持候选。若文件读取失败后通过其他正常公开入口取得，保留失败历史并以实际文件摘要为准。
