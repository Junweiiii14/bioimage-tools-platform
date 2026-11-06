# P022 作者自验与候选说明

阶段：已交付三工具的可选装配最小里程碑（B021 A1–A3）。基线 main `2a3c7a32936c6e4daf63dac23fb953cc4512e840`，起始 `e5b3d52cee737f3cd7f7fad46ecd30aeb1cc47ad` 含 P021 一次收尾；分支 `codex/p022-optional-tools`。作者窗 `01a1b0c7-c5ea-71a2-9e7e-b25ee7daaa74`，上游/指定独审按 B021。本页仅作者自验，不是独审或发布声明。

## 已证实的问题与最小修复

原始 wheel 在隔离环境经普通 `python -I -m bioimage_app` 启动，退出码1，`web_window.py`顶层导入WB失败，见 `baseline-startup.log`。基础app默认核分割/BCA还带入NumPy/Pillow。原wheel检查只验证宿主部分能力，不能推出首页可用。

- `tool_assembly.py`只识别三个固定包，启动时冻结缺失/启用/停用状态；普通首页设置写入QSettings、下次启动生效。没有插件SDK、动态工作区代码、下载商店或热切任务。
- `web_window.py`仅创建本次启用的工具桥接；原WB宿主类原样移到`wb_web_host.py`，既有调用入口用明确的已装配对象访问。普通平台页面与WB项目桥接分开；无工具也能使用首页/设置/退出。
- `research_authoring`、编辑存储和执行注册的工具导入移到实际使用分支，编辑存储在变更前拒绝缺失/停用工具项目。没有修改通用runtime、存储schema、实验公式或工具API。
- app依赖改成`wb`/`nuclei`/`bca` extras；根开发环境仍装三工具。`uv lock --offline`只重排本地依赖边，所有第三方版本和摘要未变。
- 已有wheel门禁补上真正的“无工具、无NumPy/Pillow”的普通`__main__`首页及正常关闭；全工具wheel测试继续保留。新反例覆盖停用提示、当前实例不热变更、新实例读取设置、拒绝WB入口及正常退出。没有删测试、改容差、skip或放宽检查。

## 有界隔离矩阵

Windows11 / CPython3.12.14 / PySide6 6.12.0，Qt offscreen，既有`--disable-gpu --disable-software-rasterizer`。全部实际安装wheel，`-I`从独立环境运行，探针不导入测试包/源码树。`desktop_probe.py`只包裹普通入口的创建函数以安排UI操作，其余执行真正的`bioimage_app.__main__.main`、WebChannel、WorkflowSession和Workspace；文件选择由探针提供非私有路径。非真人或物理显示验收。

完整投影、运行ID、输入输出摘要、依赖清单与配置在 `matrix.json.gz`，分场景原始日志同名gzip；退出码成功均0。可复现驱动为 `run_matrix.py`，当日两次探针修正与后续场景如下记录。

| 装配 | 实际结果 |
|---|---|
| 仅平台 | 首页呈现三个未安装状态；无wb/nuclei/bca/numpy/PIL/tensorflow；正常关闭 |
| 仅WB | 既有16bit三角峰流程，真实3节点worker、20个资产摘要，completed；新进程重开且资产不变；无其他实验包 |
| 仅核分割 | 固定已有StarDist隔离worker、既有Ganglioneuroblastoma_10公开图，46核、8个资产摘要，completed；冷重开不变；无WB/BCA/scipy/重模型库进入宿主 |
| 仅BCA | 原synthetic.csv/record.json，真实worker、12个资产摘要，completed_with_issues（原4个partial）；冷重开不变；无WB/核分割/PIL/scipy |
| 全工具 | 三条同样流程均完成；另一个新进程逐项重开，逐资产摘要与保存时一致 |
| WB停用后重启 | 使用全工具进程实际保存的同一QSettings，不重写开关；WB=disabled、核分割/BCA=enabled。BCA再次真实完成；WB历史明确“已停用/不可执行”，20个历史资产不变 |
| 隔离卸载WB后重启 | 只在本任务all-env用uv pip uninstall wb-tool，WB=missing；BCA再次真实完成、核分割历史核验重开；WB历史明确“未安装/不可执行”，原字节不变。未碰在用安装 |
| 核分割缺环境 | 核分割包启用但worker/model为空，首页明确“首次使用需准备环境”；不同于未安装/停用。其他工具可用由全工具剩余链证明 |

矩阵范围为当前三种已知工具和本机环境；不是任意第三方插件、每种依赖损坏组合或所有科学组合证明。历史拒绝策略保留数据，暂不提供缺工具时的专属结果渲染。CLI/显式旧诊断入口不由桌面启用开关充当安全隔离。

## 体量和时间（不设新门禁）

磁盘为环境全部普通文件的逻辑字节求和，含运行生成pyc，uv缓存硬链接未扣重，**不是新增物理占用**。仅平台679.59MiB、+WB1054.66MiB、+核分割736.90MiB、+BCA721.77MiB；全工具移除WB包后1052.01MiB（保留其已安装依赖，不能当作清洁最小环境）。核分割原隔离worker1934.91MiB、固定模型5.51MiB；二者不进入桌面最小环境。完整依赖名/版本见矩阵。

单次暖缓存入口至首页/WebChannel可用：平台1.391s、WB5.989s、核分割2.133s、BCA1.981s、全工具3.092s。单工具上述样例含创建/真实执行/提交分别12.165s/10.991s/2.690s；仅描述当次机器与调度，不比较优劣。OS冷缓存、峰值/常驻内存、用户设备和启动分位数未测。基础仍约680MiB，主要为Qt桌面依赖，不能称超轻应用。

## 其他自验与未完成检查

- 定向既有研究/桥接/对照/BCA/核分割GUI回归：15 passed，27.50s，exit0；新停用用例1 passed，1.32s，exit0。
- 静态policy：250产品文件，exit0；import-linter：12 kept/0 broken，exit0。它们不是动态沙箱证明。
- JS固定格式/lint/types/4项工具测试exit0；Python格式/lint通过。首次新增测试使用私有成员被严格类型检查拒绝，已改为公开信号/会话入口；后续全量执行已通过该阶段，保留重模型源码解析3 warnings。
- 现有`dev.py check --all`正在本机执行，冻结候选时不提前写通过；完成结果回传上游，不为纯收据另推HEAD。准确候选必需CI仍须通过才能正常集成。

首次矩阵WB完成计算后，探针未处理关闭确认，强制期限后进程3221226505；不能称该次完整通过，原生退出原因不进一步猜测。第二次全工具探针在页面按钮仍禁用时点击下一工具，误读旧投影；改为等待真实按钮可用、正确项目身份及批次终态后，仅重跑受影响全工具及后续场景。两次失败原日志保留，未改产品数值或放宽成功状态。早期页面缺少WB高级信号连接导致JS错误已修正；最终仅平台/停用UI和既有回归通过。GLES/mailbox旧警告保留，不宣称GPU问题解决。

本轮仅自研宿主、UI、依赖声明与验证改变。第三方算法源码、权重、冻结参考、工具领域/API和版本都未改；不用作者自验替代指定独审。科学/化学真值/LoQ/患者独立性、真人、物理DPI/OS IME、干净目标机、用户安装更新、正式发布均未验证或未执行。下一候选应尽快进入可启动交付准备，不扩大框架。


## 首审 R01 修复与增量自验

指定独审对47c8d08首审结论changes_required，唯一阻断P022-R01/P2：停用WB后真实目录drop先写入opening，再因缺工具抛错，轮询异常导致BCA被不存在的任务阻塞。修复仅在`start_from_images`任何状态写入之前调用`tools.require("wb")`；原外层处理明确错误，不建立补偿状态机制。

- `pytest tests/test_optional_tools.py tests/test_folder_drop.py tests/test_bca_web.py -q`：exit0，15 passed/11 warnings/14.89s；覆盖missing/disabled真实QDragEnterEvent/QDropEvent后两次会话轮询无异常、状态idle、BCA选文件仍可进入，以及既有有效WB多文件夹/缩放路径与BCA真实提交。缺包单测为受控find_spec反例，下面另有真实缺包wheel。
- 重新构建app wheel，在新的独立BCA-only和WB+BCA（WB停用）环境，普通main入口接收真实Qt drop，均明确拒绝且stage=idle，BCA原生文件选择继续；随后BCA真实worker/正式提交成功。两个进程exit0。完整投影/状态见`r01-native-drop.json.gz`，原始日志`r01-missing.log.gz`和`r01-disabled.log.gz`。
- Pyright exit0，0 errors/3条既有重模型源码warnings；格式/lint与提交钩子继续执行。无科学/数值/版本/容差改变，不重跑未受影响的整套模型矩阵。
- N01非阻断建议同次修正：`run_matrix.py`停用场景引用前一全工具进程的实际settings_name并设置preserve_settings，不再重写开关。先前已提交matrix中的真实跨进程保留证据仍有效。

47c8d08的本机全量检查尚在后台执行；本轮中途有上述实质修复，后续结果只作诊断，不能冒充新head准确全量通过。最终集成依赖新head的指定增量复审与必需CI；首审报告在最终一次收尾归档，不为纯收据另推HEAD。
