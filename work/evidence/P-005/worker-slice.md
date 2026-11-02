# P005真实节点与请求确认切片（不是完整执行器）

本轮基线89ba603b38c77bd45689c48c2918f43f423f7a4f，锁定Windows/Python3.12.14环境，未增依赖/更改旧公式或schema。新增固定wb_workflow入口及verify/analyze/publish三模块；RunSession可选require_dispatch_ack，真实PID入库后必须获匹配确认才发请求，原始ExecutionEvent保留。契约见docs/contracts/wb-original-workflow-v1.md。

实际命令均uv run --locked --no-sync：

- pytest tests/test_module_run_session.py tests/test_run_session.py tests/test_process_runner.py：28passed28.08s/exit0。旧七场景分别跑默认/确认模式，原成功/非零/缺失/篡改/取消/缺绑定/硬链接断言保留。确认前只能收到hello、无产物；错run授权拒绝，正确PID授权后才继续。
- 新tests/test_wb_workflow_nodes.py首五组实际三节点：5passed22.88s/exit0；每组都是独立真实OS子进程、RunSession、正式Workspace事务提交及关闭重开，总15次节点执行。独立预期40/4000/真实0/invalid=null/quality_review=null通过，完整原始剖面核对，不以新结果复制旧值。
- 七个受影响测试文件曾一次114passed57.89s/exit0，覆盖上述模块/RunSession/process、账本、P007契约与Workspace；随后因完整曲线坐标/宿主依赖身份及取消反例增量，针对受影响范围复验（不冒称114对应最终源码）。
- 增量tests/test_run_session.py tests/test_wb_workflow_nodes.py：12passed28.82s/exit0，新增等待确认时取消不发请求、真实退出后持久cancelled重开；三节点仍保留精确值与完整剖面。
- 最终tests/test_wb_workflow_nodes.py：6passed22.93s/exit0；五组真实三节点全通过，并新增外来数值策略AnalysisResult不得伪装本报告方法、候选目录不创建的反例。剖面带原Y起点/步长、dtype上限、位深与转换。
- 随后把实际public worker入口api.py纳入固定实现源摘要，最终六项再次6passed22.86s/exit0。全仓Pyright strict0errors、14个受影响Python文件format检查0、计划登记检查0；旧schema/数值门禁未修改。
- 最终Ruff check/format及受影响Pyright strict exit0；policy及九项import-linter约束exit0。初版Pyright质量标注str/Literal错误和测试B023闭包错误均修正，无ignore/skip/预期放松。

报告实际源为自有合成uint8三角形正式提交成果，复制到.local/p005-report-preview.png目视检查：1200×168灰度，值40.0/status=valid、单位、来源SHA及曲线文件说明完整可读。首次预览脚本把pytest目录名少写一个字符，StopIteration/exit1；按实际目录名修正后exit0并查看，不是产品失败。未输出/提交用户原图。

新模块指纹固定生产源码（含LineReader与协议依赖），自身环境核对Python/OS/CPU、依赖、codec及TIFF资源配置。宿主摘要函数实际读取已安装contracts/runtime/desktop源码并记录Qt/宿主包版本，但生产GraphSession还未调用它做当前准入；不能把节点收到host_runtime_source字段当作真实宿主认证。

**未完成：** 测试父进程目前显式串接三节点，尚不是生产通用自动调度。GraphSession/可信模块装配与后台准备、账本started确认、当前环境准入、cache/recovery/暂停取消完整接线及故障矩阵仍需实施。本轮新源未跑完整门禁/新wheels/CI，准确提交独审待做；前轮418的wheel/独审只属于前轮源码。P005继续in_progress，M1/M2未完成，不授S1/现场验收。

首轮823d独审Request changes见worker-review-r1.md：发布绕过旧完整结果校验，可输出非有限/负数为valid。后继分析/发布共用旧ResultFrame验证，13项最终节点测试23.04秒通过，错误输入无候选目录；新准确源码仍须复审。
