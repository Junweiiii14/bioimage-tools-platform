# E3/T056 验证

base733ea17，Win11/Python3.12.14/Qt6.12.0，锁不变。

核心第一批：新增6项（含N=1…96的20例性质检验），连同既有E1/E2共21 passed/3.30s退出0。
覆盖全空不丢槽、不假坐标；已知Marker与五个样本中心；N冲突不臆造末端；
取消建议不安装、来源改变拒绝、嵌套slotID伪造拒绝、schema12保存重开、
明确人工矩形后从坐标编码原像素逐值核验TIFF、不覆盖与原图字节不变。

首轮新增断言错误：重复整个slot同时破坏position顺序，先被完整N检查拒绝；
改为保留position只伪造重复slotID以检验目标不变量，未放宽断言。
初期Pyright发现tifffile.imread未知重载类型，使用TiffFile/TiffPage原生读取核验，
无类型忽略/skip/容差/依赖/门禁修改。定向Pyright0；全仓静态、宿主、完整门禁/
隔离wheel和最终非作者独审未完成，E3不标done。真实科学留出缺口保留。

## 宿主与复核候选 bf6c8d4

- 真实桌面：`uv run --locked --no-sync pytest tests/test_instrument_intake_desktop.py -q`，14 passed/14.74s，进程0。两行全空N=8保留完整槽位；手动复核后原值1000/uint16/40×120资产与重开schema12；延迟检测取消不安装、不启动下一行；running意图CAS写失败不启动工具任务。
- 前端最终：`uv run --locked --no-sync pytest tests/test_intake_web_ui.py -q`，7 passed/7.19s，进程0（有WebEngine GPU context lost诊断，测试与进程均0）。覆盖固定N/草稿跨快照、正确身份摘要、忙/失败焦点、匹配保存回复才清草稿。
- `uv run --locked --no-sync pyright`：全仓0 errors/0 warnings；相关Ruff check0，提交钩子Ruff check/format及policy0，无依赖、容差、skip/xfail或门禁更改。
- 返回产物为IntakeCropFile(path/SHA/size)，宿主限制为所属尝试的精确临时文件，Storage import核验SHA并校对返回AssetRef的SHA/字节数；清理验证绝对根及temp父目录，只处理所属目录。
- 界面截图：`.impeccable/review/t056-browser-intake.png`文档顶部、`t056-browser-stages.png`阶段区、`t056-browser-crop.png`原图复核。真实浏览器1280×720/合成5槽700×300膜，无私图；全部已打开核验有效。不是Qt显示、目标DPI或科学准确率证据。键盘从打开复核后的viewport按Tab进入crop-overlay。
- 本轮detector只运行一次，`.local/t056-design-detector.json`：12项advisory、无primary；既有文档token漂移不借本任务修复。独立finish review对bf6c8d4给`ship`，限定已观察桌面E3，无material finding；未知960px/移动/DPI/真实实验不外推。
- 最终全量`dev.py check --all`正在执行（只读native stack/windows fault/Qt inventory观测），当前不能标通过。最终非作者代码审查和文档核验未回收。

## 最终修复候选32da9f4

bf6c8d4全门禁因独审已知P2主动Ctrl+C，outer1；对应pytest34436已退出；这是主动中断，不是原生崩溃或通过证据，日志`.local/t056-fullcheck.txt`保留。
修复真实WebChannel stateChanged强退清单：同项目/会话的cropEnabled review保留，身份变化回到清单。
原复核测试改为Python真实stateChanged.emit经已注册bootstrap回调，覆盖选中/缩略图、busy、保存失败、成功ack、epoch变化；强化重开等待实际host切换/epoch/idle/projectId。
两文件联合回归21 passed/18.93s，进程0；仍有WebEngine GPU诊断但不把日志抹掉。
非作者冻结bootstrap Node探针复审32da9f4，P2关闭、无新增阻断；受影响界面同3图重新截图/打开后，finish verdict对修复逐项resolved/ship，documenter No changes仍有效。
最终32da9f4完整门禁`.local/t056-fullcheck-final.txt`运行中，未标通过。

最终32da9f4：完整pytest **832 passed/553.10s**，原始child exit0/u32=0x00000000，9导入契约0 broken。只读Qt inventory仍344/truncated，与E2观测一致，不能当作344个已证明泄漏；旧所属fixture收尾仍转E6，首次purecall来源UNKNOWN保留。隔离wheel/真实离线OCR及完整check外层退出仍待回收。

最终完整check外层退出0；全部隔离wheel安装/原值TIFF与PNG/模板与保存重开、真实离线PP-OCRv6及OCR worker/PNG文字坐标通过。`.local/t056-fullcheck-final.txt`完整保留。结合32da9f4绑定非作者代码及界面复核，E3本机源码工程阶段完成；科学独立留出、目标Win10/DPI及E4–E7不外推。
