# P021 作者自验与审查入口

阶段：固定研究方法进入既有图编排的工程 MVP。基线 `aa3302ad2980dfeec1ac6f7776fec6176f18fcda`，分支 `codex/p021-research-workflow`，继承 P020 一次本地收尾 `a5d9ca8`。本页不是独审通过声明；准确候选由 Git 提交及后续审查请求绑定。

## 实际覆盖

- `nuclei_tool.api` → NucleiHost.definition/modules → research_authoring → 现有 WorkflowAuthoringSession/WorkflowBatchSession/WorkflowSession。固定一个方法节点覆盖 StarDist 完整研究处理；无内部函数拆节点。
- `bca_tool.api` → BcaHost.definition/registry_definition → 同一编辑/执行/事务链。原始 CSV 与明确板记录两根输入，固定方法无自由参数；不复制数值公式。
- 用户导航和复现步骤见 [研究编排](../../../docs/runbooks/research-workflow.md)。三工具首页入口保留，WB三节点未重建。目录按当前实验提供受支持方法，未实现跨实验图、安装卸载和 Agent。
- 只改自研宿主装配/输入复用/编辑器/展示及测试文档。`tools/nuclei`、`tools/bca`、第三方源码、权重、依赖锁、冻结参考与门禁无改动。CLI与图使用同一输入适配和公开API。
- 编辑文档 schema2 明确 tool/record；旧schema1只读不写，显式保存新修订才升级。模板封装/科学图/Workspace/算法版本不变，详[兼容契约](../../../docs/contracts/workflow-authoring-v1.md)。

## 实测与原始证据

Windows 11 / Python 3.12.14 / 已锁定 PySide6 QtWebEngine。普通测试离屏；截图用真实 Windows 平台、`--disable-gpu`，不是物理 GPU/DPI 或真人输入验收。已有 GLES/mailbox 警告未声称修复。

| 命令/证据 | 结果与界限 |
|---|---|
| `pytest tests/test_workflow_authoring_store.py tests/test_workflow_authoring_bridge.py tests/test_workflow_authoring_session.py -q` | exit0，10 passed / 41.24s；既有编辑CAS、真实执行/关闭路径 |
| `pytest tests/test_research_authoring.py tests/test_research_authoring_web.py -q` 最终定向 | exit0，5 passed / 10.65s；模板新输入、BCA明确记录、无效连线/重新绑定、真实worker、旧模板保护、冷读、损坏输入拒绝、schema1显式保存 |
| 定向附加 WB `test_web_editor_saves_and_runs_actual_fixture` | exit0，5 passed / 24.27s（含当时3项研究单测+研究GUI）；WB三节点真实出表、再绑定40.0通过 |
| `.local/p021_desktop_test.py` 第一轮 | exit1，120.92s；第一张46核已提交，误选非uint8第二图被正确拒绝，探针等待超时；未修改准入预期 |
| 同探针第二轮 | exit1，27.77s；两图已提交46/18核、模板复用/新进程冷读完成；BCA已提交但探针误要求completed，实际completed_with_issues符合4个partial契约。保留原失败，不将整探针写pass |
| `.local/p021_bca_capture_test.py` | exit0，1 passed / 11.77s；重开上述BCA实际工作区、重新核验并展示成果，四主题/1440与960截图 |
| [desktop-runs.json](desktop-runs.json) | 第二轮关闭后从三个真实工作区重新读取并核验的完整投影；均有run/输入/输出摘要，无base64。临时测试目录后被pytest正常保留策略清理，记录不伪装为永久可打开项目 |
| [numerical-parity.json](numerical-parity.json) | 两张核标签文件SHA与P015固定已见研究结果相同；BCA相同CSV摘要、同输入CLI重新执行的wells/samples逐字节相同。属于工程一致性，不是独立科学准确性 |
| `ruff check` / `ruff format --check` / 定向 `pyright` / `npm run check:web` | 最终自验exit0，Pyright 0 errors；日志p021-lint-final.log.gz包含环境烟测通过。未加忽略、skip、改容差或门禁 |
| `dev.py policy` | exit0，248个产品文件边界扫描；不等于动态沙箱或全科学证明 |
| `dev.py check --all` | 本机运行中；已有GPU日志和至少一个失败尚待最终定位，不宣称通过。最终候选必需CI另记 |

原始日志/探针为无损 gzip，摘要及截图见 [artifact-index.json](artifact-index.json)。完整运行语义和结果依赖真实投影，不以截图替代执行。图像来自既有公开研究数据与合成板，无私有原图。两轮UI有界检查后仅将核数文本移至显示图之前（不改计算/样式），通过DOM及源码检查，未追加第三轮视觉精修。机械detect返回全页面既有CSS对比度/动画/glow警告；本轮无CSS/token改动，不将此扫描写成全页面无问题。

## 仍未验证与协调

科学/化学准确性、LoQ、训练重叠/患者独立性、真人、物理DPI/OS IME/干净目标机与用户安装更新全部保留。模型环境/磁盘成本沿P014/P015，未新增重依赖或环境；本轮未测新峰值内存，未重做P009全性能矩阵。新图结果读取复用原图/标签显示，数值资产保持原始精度。

既有取消/失败/旧草稿保护由上述10项和P009/P015/P019证据约束；本轮新增缺运行配置、无效来源、错误连线和资产损坏反例，不重复全部历史异常矩阵。作者自验不替代独审。共享树仍由开发窗持有，冻结后回上游，由指定独审窗按准确base/head审查；不自行合并。

## 创建顺序回归修复

旧候选0027432在本机全量第329号用例 `test_changed_source_rejected_before_workspace_creation` 失败：输入导入提取使原图SHA变化的拒绝发生在Workspace.create之后。恢复先公开read/校验再创建；导入接收已验证NucleiInput/PlateInput，保持入口验证一次及快照摘要核验。BCA同类CLI顺序一并恢复，数值/worker/方法未改。

`pytest tests/test_nuclei_ui.py::test_changed_source_rejected_before_workspace_creation tests/test_research_authoring.py tests/test_research_authoring_web.py tests/test_nuclei_host.py tests/test_bca_host.py -q` exit0，12 passed / 17.92s，原断言未修改。相关Ruff与Pyright exit0。全量原进程继续诊断；执行期间有工作区变更，最终日志不得作为任一冻结head的全量通过。修复后准确提交的必需CI承担完整验证。
