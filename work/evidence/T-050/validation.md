# T-050 只读审计与验证

日期2026-10-19；Windows/PowerShell；规划PR基线221a2dff610554092a881fc396010f032b31ae33，代码只读基线a23435471742b69adbc800bad0b1b8fe58872bd3。审计两名子代理只读分工，没有产品修改或长测试。下列是现状和候选优化依据，不是新流程通过证明。

## 需求依据

用户明确要求清单先行，并确认N含空位/不含Marker、原名与缩略图分配确认、拼图后触发但读取原像素定量。新版规划为docs/wb-development-plan-v2.md；S1–S3是待审建议。

## 产品事实（路径均相对于审计基线，未随本PR引入main）

| 证据位置 | 已观察事实/规划影响 |
|---|---|
| apps/desktop/src/bioimage_app/automatic_workflow.py:170 | 当前定位后先analyze_project再publish/compose，需重排为用户确认的新流程 |
| tools/wb/src/wb_tool/application/figure_project.py:31 | FigureRow已有稳定ID、Fig/蛋白/N/原图SHA/ROI及缺图占位，可扩展复用 |
| tools/wb/src/wb_tool/domain/source_geometry.py:280 | 当前只补内部槽，不外推无信号首尾；显式N冲突失败，不能声称空条带已解决 |
| tools/wb/src/wb_tool/adapters/automatic.py:19；ui/background.py:118 | 初次无ROI路径的lane_count默认None，后台调用未传N；新流程必须验证N真实进入首轮定位 |
| tools/wb/src/wb_tool/application/import_labels.py | 旧Fig路径/文件名/编号变体筛选不能作为未知仪器导出身份真值 |
| tools/wb/src/wb_tool/application/project_analysis.py | 已有全部N槽及有效/缺失/失败等状态；empty_lanes是人工排除，不能把未检出自动映射进去 |
| tools/wb/src/wb_tool/application/laboratory_layout.py | 原泳道范围和显示位置关联可复用，显示不参与定量 |
| tools/wb/src/wb_tool/adapters/automatic_export.py；figure_image_export.py:86；figure_export.py:266 | PNG/TIFF/ZIP分别渲染，宿主再请求预览，至少4次；可共享冻结渲染，不删除写后核验 |
| tools/wb/src/wb_tool/adapters/laboratory_figure.py:117 | 已按源单次解码并释放；应保留有界内存，不缓存整个批次 |
| tools/wb/pyproject.toml；apps/desktop/pyproject.toml；tooling/build_runtime_candidate.py | OCR在工具中optional，桌面wb extra却强制带OCR，打包导出生产依赖闭包；可选发行需独立修改审查 |
| apps/desktop/src/bioimage_app/web_window.py；tools/wb/src/wb_tool/domain/scipy_geometry.py及wbquant143 | QtWebEngine为当前UI运行依赖，SciPy为核心几何/积分依赖，不能直接删除 |

## 体积观察

本机T048 app目录，排除所有__pycache__及.pyc后7,721文件，1,095,924,700字节（1,045.16 MiB）；对应安装器361,325,507字节。按文件长度求和，不是磁盘压缩占用或重打包节省量。主要包目录约PySide6 625.42 MiB、cv2 112.40、scipy及scipy.libs 114.04、onnxruntime 41.67、rapidocr 31.07；各目录估计包含少量运行缓存，不能直接相加推算可节省量。四产品包非缓存源码合计约1.34 MiB。

原始PDF通过bundled pypdf只读抽取34页中的相关文字（第12、14–16、21–22页）；第一次控制台GBK编码失败exit1，设置UTF-8后exit0。未编辑PDF，也未进行版面设计/图表解读。原文支持原始资产、稳定身份/坐标、显示与计算分离、按任务恢复及小步独立审查。

## 执行记录

- git fetch origin main、GitHub仓库/PR只读查询：exit0；main仍221a2df，规划采用独立文档PR，避免夹带未集成产品。
- context T-050：exit0，范围为README、新规划、任务/证据及handoff；使用已安装Python环境，不升级依赖。
- 后续文档检查、PDF摘要、回执与审查结果在下方记录。
- 本轮产品单测/GUI/安装/性能运行/科学准确率评分未运行；仅代码阅读与目录长度统计；不复用历史测试当本轮通过。

- 文档链接检查：exit0；PDF Git blob仍3ae2a2ac0dd235059d2fafaa9cba3f25f01f101d，与main一致。
- dev.py policy：exit0；本规划树扫描0产品文件，只说明治理基线，不是产品通过。
- handoff容量检查：exit0，changed0/warnings0/unresolved0。
- git diff --check：exit0。
- 初次快照归档因目标目录不存在失败，已从main原始blob完整恢复到归档目录；不遗失旧记录。

- 独立文档审查绑定fa61c29，无阻塞；已明确每Fig拼图就绪与冻结快照。后继仅记录交付状态与审查证据。
- GitHub草稿PR #16已创建并附本聊天；远端检查以最终PR head为准，本轮不合并。
