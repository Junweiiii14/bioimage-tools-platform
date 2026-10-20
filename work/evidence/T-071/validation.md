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
- 三目录当前只读清单104文件/85TIFF/76唯一内容；与T069历史114/95不同，历史证据不改。首个脚本沿用旧95等待条件被主动停止，自有窗口正常关闭/删除，实际1；v2扫描及发现19个仪器三联组通过，但本地脚本用Python严格模型接JSON列表失败，实际1，未启动产品处理。进一步核验完整列表47组：19组角色merge/signal/white、28组全部reference。已向用户集中确认参考组是否不占顺序，等待此数据范围答案；不擅自跳过中间参考组。
- 尚未运行最终完整门禁、最终绑定独审、PR/服务器检查、构建安装；新真实目录完整链未通过，不宣告已交付。旧工作树/原图/历史和T069安装保持。
