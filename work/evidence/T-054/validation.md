# E1/T-054 验证

- 基线631b059，Windows11/Python3.12.14/Qt6.12.0，锁文件未改。
- 新增纯派生计划API与不可变类型；schema10、旧读取器、科学算法均不改。保存重开后重新生成计划；不添加第二权威。
- 相关23项（新计划7项含2个Hypothesis性质、原清单16项）4.08s退出0；覆盖特殊名称/路径、独立身份、N变更、重新分配、跨Fig迁移、待算空值、确认/摘要、保存重开。
- 初轮22项通过；Ruff报告新代码导入/长行与机械不可变测试setattr问题，格式化后修正；Pyright指出同类型isinstance冗余，公开输入改为父WBFigureProject并测试旧项目明确拒绝。没有增加类型忽略或削弱原测试；移除纯镜像dataclass实现的setattr测试，保留输入不变的行为断言。
- 最终相关Ruff/format、定向Pyright退出0。完整门禁/隔离wheel/独审待执行，不能以前23项代替。
- 工具链门禁不变，installed_wheels只追加实际公开API的安装环境用例；无依赖升级/锁/schema/数值默认值变化。

## 最终完整门禁

- f975809代码无后续变更：完整dev.py check --all实际外层退出0；808 passed/554.07s，随后9契约及全部隔离wheel运行完成。
- 已安装WB新计划API、四包隔离环境、直接TIFF/PNG、schema7模板、项目v4/v5、真实桌面异步关闭、离线OCR与静态worker、PNG OCR通过。原始完整日志.local/t054-fullcheck.txt。
- 日志中有WebEngine GPU context lost及隔离字体目录提示，测试继续到完整成功；不将它们解释成历史原生异常根因已关闭。
- 一次额外原生栈采样工具退出1/ValueError（独立工具进程不在既有测试监视器祖先关系，按自有进程约束拒绝），未改工具或绕过约束，没得到原生栈；没有终止测试，后续正常完成。
- 非作者独审无阻断，另见independent-review.md；没有远程CI/发布或重建安装包。本阶段可进入E2。
