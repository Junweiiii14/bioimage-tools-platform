# T-003：WB 产品开发与验收

- 状态：implementing
- base commit：d83e4a0
- 授权：2026-10-14 用户要求检查进度、持续规划开发直到完成 WB 自动化软件；取代仅限 P0 的旧范围限制。
- 依赖任务：T-002 本机 P0 已有部分证据；干净机仍待后续。

## 目标与范围
先冻结原方案与既有 WB 参考代码、解析样例和坐标/积分定义，再按里程碑实现 WB 软件。不得把技术探针视为产品。原图、历史结果和 PDF 保持不变；不恢复归档项目。

## 修改范围与必读
根规则、docs、work、.agent-handoff、tooling、tests、tools/wb、dev.py、.importlinter、.github/workflows/quality.yml、pyproject.toml、uv.lock。第一产品包已实现已冻结的纯数值积分；当前进入 TIFF 输入、半开泳道 ROI 与原始均值剖面阶段，不提前创建公共平台包。必读架构、代码规范、研究协议和原方案，以及 tools/wb/README.md 与 docs/contracts/wb-reference-v1.md。

## 里程碑
1. T-001 参考冻结：来源版本、公式、解析预期、差异和限制。
2. WB 领域与图像适配：位深、ROI、积分、归一化、失败状态，独立 wheel/边界门禁。
3. 工作区/worker/UI：导入、ROI 编辑、分析、取消、保存恢复与导出。
4. 自动检测与批次：人工复核、参数快照、旧结果隔离。
5. 产品验收、绑定提交独立审查、Windows 便携包；干净机验收保留真实未测状态。

## 语义与验收
按原方案与冻结参考定义，尚未核实部分为 UNKNOWN。解析预期不由被测实现生成。真实样本不提交 Git。

## 验证与独立审查
2026-10-14：基线 dev.py check --all 退出 0（35 测试）；首个 WB 核心
完整 dev.py check --all 退出 0（61 测试，Ruff、Pyright strict、2 项 import-linter、隔离 wheel）。
23 个 WB 数值测试、3 个导入图正/负例，未改变旧预期或 skip。
真实检测、GUI/产品安装包未测；独立审查尚未执行。
参考来源冻结 8 文件的 SHA 和本地字节快照，真实标注尚未冻结，不能宣称 T-001 全部完成。
门禁增加真实 import-linter 和隔离安装，没有削弱原检查。uv.lock 仅新增 wb-tool workspace，
构建后端固定 uv_build==0.13.0。independence 在实际第二独立模块出现时增加，当前不造空合约。

## 下一步
TIFF 输入、稳定 lane_id 半开 ROI 与原始均值剖面已实现（wb-tool 0.2.0）；
单页灰度、RGB/不透明 RGBA，uint8/uint16，显式极性，原始字节与读取数组保护。
5 张本地真实 TIFF 只读输入/10 行剖面烟测通过，私有摘要保存在 .local/wb-real-input.json。
77 项最终完整检查通过，含 independence 传递依赖负例。
依赖声明新增已有锁版本 numpy/tifffile，无版本升级；积分 algorithm_id 不变。
隔离 wheel 改为干净环境依照 uv.lock 安装必要依赖，再 --no-deps 安装构建产物；
直接 offline pip 解析由于缺索引元数据失败，已改用锁文件 sync，不回退到源码导入。
当前执行子任务 T-004 手工标注分析用例；下一步 worker/工作区/UI 手工闭环，再自动候选。可选 OCR 优先问题未回复，默认先候选，
OCR 尚不以没有回复作永久排除或验收通过。
