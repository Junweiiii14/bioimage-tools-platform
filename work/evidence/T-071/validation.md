# T071 实施验证

基线main6916b3a，规划来源0a966e8，新受管wb-fig-sequence/codex/fig-sequence-automation；Windows、Python3.12.14/uv0.13.0，uv sync --locked --all-groups实际0，第三方锁不变。旧规划稿/工作树与原图/历史/安装保留。

- 编辑前创建T071并实际加载十二scope回执0；七规则与main相同。T070历史回执将在最终显式integration-context中绑定来源提交，不删除回执以通过门禁。
- 初始定向：pytest -q tools/wb/tests/test_intake_grouping.py tools/wb/tests/test_intake_workflow.py tools/wb/tests/test_intake_group_revision.py，24 passed/12.58s，实际0。
- 首增量：加test_intake_sequence.py后30 passed/13.67s，实际0；顺序投影/缺组/余组/来源身份/旧wire/阶段屏障/异常全批暂停。
- 增加80例Hypothesis身份守恒、幂等与JSON往返后，四文件31 passed/6.06s，实际0。Ruff初次仅新测试导入排序1，ruff --fix后0；5文件格式检查0、四用例文件Pyright0。
- 纯核心 edb5a5e 绑定非作者审查 accepted；40项含独立反例/80个Hypothesis输入实际0，五种旧wire/摘要与基线逐字节一致。范围见 independent-review.md，不覆盖后续产品增量。
- 新顶部配置、单一CAS启动、整批自动导航/原图修正后单一继续、独立FigSequenceTest配置及新诊断已实现。相关Ruff/Pyright实际0；首轮两个纯核心新测试的错误预期/旧参数名已修正（断言改为现有真实错误文案及公开outcome参数，没有削弱产品检查）。
- 新实际Qt网页两Fig测试最终11.25s实际0：顶端填写Fig名/N/蛋白、手选组内来源、一次启动；第一行needs_review时第二行pending且全部非crop attempt0；各自一次修正继续，全部crop提交才compose、全部compose提交才measure；实际进入review/layout/quant/results，两个真实worker PID与运行提交、独立完整输出、重开无自动续跑，原图/旧输出逐字节保持。
- 六文件扩大定向（sequence纯核心、intake网页、实际desktop、发行设置、CLI生命周期）70 passed / 134.65s，进程实际0。包括过期摘要和合成CAS失败下绝不启动裁剪worker；两个旧手工草稿测试显式构造schema1，继续覆盖其原契约，不把新默认schema2伪装成旧格式。
- 新诊断源码实际调用 `python -m bioimage_app --verify-sequence-installation .local/t071-sequence-source-v2.json`，8.0s实际0、13项齐全；worker PID58648/56128，实际页面顺序review/review/layout/quant/results，每个运行阶段都收到真实快照，原值uint16/9槽位/完整输出/重开/关闭通过。此源码调用isolated_imports=false；扩大回归中的真实`-I`子进程另通过，不宣称已安装。
- 诊断v1曾因把JS“点击完成”当成保存回执而120s失败，按真实持久crop.reviewed判定后v2通过；保留失败报告，不伪装成功。
- UI一次detector实际0：仅24条design-system advisory（20字阶/3颜色/1圆角），无primary；继承既有系统漂移，转交finish reviewer，不扩大修复设计系统。1440、1024、390实际Qt源码截图已逐一打开确认；完整视觉独审尚未完成。
- 三目录当前只读清单104文件/85TIFF/76唯一内容；与T069历史114/95不同，历史证据不改。首个脚本沿用旧95等待条件被主动停止，自有窗口正常关闭/删除，实际1；v2扫描及发现19个仪器三联组通过，但本地脚本用Python严格模型接JSON列表失败，实际1，未启动产品处理。进一步核验完整列表47组：19组角色merge/signal/white、28组全部reference。用户现已明确：只给19仪器采集组编号，28参考组保留单列、不占序号。
- 尚未运行最终完整门禁、最终绑定独审、PR/服务器检查、构建安装；不宣告已交付。旧工作树/原图/历史和T069安装保持。

- 澄清后reference_group_ids严格校验全部成员reference证据；原完整组身份/位置不变，蛋白投影跳过参考；空可选字段省略保持已发grouping@2摘要。新仪器池异步识别，旧保存项目仅显式预览分类。
- 增量保护14 passed/13.18s实际0（取消编码迟到回调、过期摘要/CAS失败不启动、真实两Fig链）；类型检查0。参考与界面控制31 passed/19.93s实际0；随后空字段兼容/新池识别后核心+真实两Fig12 passed/10.62s实际0。新增测试首轮观察group_id夹具不满足24位身份规则失败，按真实契约修正夹具后通过，未降低校验。
- 三目录最终开发链.local/t071-real-chain/20261021-003541/report.json：192.59s实际0，扫描85 TIFF/76内容；19仪器三联组、28参考，19个回归Fig/74槽位（为完整顺序覆盖，不主张原生物配对），人工来源/ROI/N沿用已见开发参照。19真实worker原像素输出；一行修订后其余18 Fig保留、再次输出新目录、旧目录保持；保存重开结果稳定，全部104源文件字节不变，自有资源/窗口关闭删除。此链用后端明确选择记录，不冒称用户实际点击证据；实际网页点击由两Fig合成回归另覆盖。历史T069的114/95清单原样保留。
- 独审2a发现关闭途中资产/渲染回调可遗留busy（24通过/2失败实际1）；现补相同key才结束操作，旧key不得结束新任务。UI独审要求手动浏览保留页/选中/焦点、暂停人话说明及明确放弃草稿文案，已修复待最终绑定复审。原失败与本地抓图探针失败保留，不混作通过。

- 最后修复后的网页/宿主/快捷键定向64 passed/91.77s，进程实际0；包含手动浏览页/源/焦点保持、参考独立区域、编码取消和两Fig真实链。Ruff和八文件Pyright实际0。

- 冻结c935产品/7e文档的首个完整check --all：静态/类型/9依赖契约通过，pytest 976通过/1失败、849.93s，整命令实际1，后续wheel未跑；不以976项替代全门禁成功。唯一失败为新增序列安装诊断没有看到每个短暂running状态。PR30首Linux同一失败：976通过/1失败、399.97s，inferior01/debugger1，后续wheel未跑。原日志.local/t071-final-fullcheck.log、t071-ci-ubuntu-first.log保留。
- 诊断根因已确认：bridge.stateChanged节流/合并快照，不保证每次成功持久保存都发布。两平台都已完整输出、两个真实worker和review/layout/quant/results真实页面成立，但短暂阶段样本不全，诊断应失败。修复仅诊断观察：包装实际host.save成功回调，先观察已安装的持久修订再调用原有after，失败/CAS/取消不伪造事件；网页导航仍由真实JS独立检查。阶段要求从数量加强为与最终账本全部(stage,target)集合精确相等，记录revision及committed-save-callback来源，不删断言、不加重试/延迟、不改生产调度/门禁。局部真实-I诊断11.83s实际0；新字典推断类型初次1错误，显式dict[str,object]后Pyright0，无忽略。

- 二次本机完整977/845.63s、原child0/u32=0、全部wheel/真实OCR及整命令0；Linuxcb2完整977/395.52s/debugger0/wheel/check0。cb2仅比本机开始20c多两份Markdown/8行，没有在执行期间改产品、测试或门禁。Windowscb2在第5个既有归档关闭用例原生挂起，job20分钟CANCELLED、pytest退出未知，API日志404，live247行片段已保留；未合并。最窄所属端口顺序修正与23项定向0见windows-close-order.md，需要新冻结全门禁/CI。

- 最终a952完整979/825.65s、原child0/u32=0、全部wheel/OCR/check0；5f诊断请求确认另有真实-I11.68s0与32独立纯控制0，不冒充被a952完整覆盖。最终5f两平台979项（Windows615.77s/Linux332.14s）及全部wheel/OCR/check0、四required SUCCESS，PR30正常精确合main710bb85；非作者核全树相同。原a541两平台各978通过/1失败及Windows手动坐标UNKNOWN保留，未改该旧测试答案或容差。详final-ci.md。
- 冻结main710bb构建/当前用户安装0，安装态顺序13项、旧采集组17项、灰度OCR7项全passed，父OS0、无所属残留或开发模块；PS5.1随包三流程外层0。7751构建载荷SHA与安装一致，新桌面T071交付已生成，旧3文件和10dirty/HEAD/status保持。首PS5.1本地外层中文路径编码失败-196608保留，仅补BOM后新轮0；详offline-installation.md，最终非作者产物核验见独审文件。
