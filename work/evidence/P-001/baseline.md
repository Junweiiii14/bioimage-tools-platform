# P001 基线接入与检查

2026-10-31，Windows 11 10.0.26200 / Python 3.12.14。执行树 `C:/Users/70236/ResearchVault/Codex-Workbench/bioimage-v0`，分支 `codex/p001-v0-baseline`，产品基线 dfc48ed7c2c944dc8f03c3931bc7985452a31393。T082原树clean，较fetch后的origin/main 18b5cf6领先28提交；冻结构建源码ed830e1与最后交接HEAD严格区分。旧主目录feat/T-021/bb5601a含大量他人dirty，未修改。既有安装和原图未触碰。

## 接入与集成策略

方案已按PR46当前2493e0be读取；尚未宣称最终合入，集成前继续复核最终HEAD。adopted-files.json逐项保存原样接入源提交及SHA256；source-inventory.json保留初次ac983007调查快照。P001任务激活和重叠AGENTS/README/架构/模块地图/AI流程/handoff采用T082为底语义合并，原snapshot逐字节归档；没有复制旧主目录规则或产品。

本轮只改计划/治理/证据，相对dfc48ed产品源码无差异。计划renderer是文档工具，保留源版本；锁文件不改。保留T082历史rules-context，实际PR以最新main为base重载P001当前回执与integration清单。PR46的B008发布状态由原聊天维护，不修改其工作树或任务；合入后将历史文件作为祖先保留。P任务当前执行权威在本执行树，PR46 planned版本是发布历史，不能独立继续推进。

## 实际验证

- `uv sync --locked --all-groups`：首轮沙箱uv缓存写入拒绝，exit1；提权在新树安装固定83包解析/82包安装，exit0，无锁变化，不修改T082环境。
- `uv run --locked --no-sync python dev.py context --task P-001 --scope . --base 18b5cf6de0c83b8c67f26433a6059d8dabf1f381 --record --integration`：exit0，已读输出及缺失截段的源规则；后续规则变化须重载。
- `.venv/Scripts/python.exe dev.py doctor`：exit0，Python/六项开发工具版本符合锁定值。
- `check_plan.py`：exit0，11工作包，P001 in_progress，其余planned；结构检查不证明产品或科学验收。
- WB analysis +真实RunSession定向基线：默认沙箱Temp不可写导致1 passed/17 setup errors；首次指定basetemp缺.local父目录同样1 passed/17 setup errors。创建.local并使用全新basetemp后，18 passed/9.27s，exit0。设置QT_QPA_PLATFORM=offscreen；未改测试、预期或容差。命令：`.venv/Scripts/python.exe -m pytest tools/wb/tests/test_analysis.py tests/test_run_session.py -q --basetemp=.local/pytest-p001-baseline-b`。
- `maintain_handoff.py --repo . --check`：exit0，warnings=0/unresolved=0。
- 完整产品门禁、独立wheel、GUI用户体验、本轮安装器构建未运行；先按P001治理范围完成独审，P002新行为实施后执行适用产品验证。旧T082完整检查属于历史准确提交，不作为新行为通过证据。

## P002调查结论

已核对四包README、tool_contracts.api、wb_tool的AnalysisRequest/analyze_annotations、现有worker、RunSession及Workspace提交契约。选择严格uint8/uint16原值+固定半开ROI/闭区间条带的成熟手工分析用例；归一化不在该用例本身，不能为它声称坏分母测试已覆盖。可用解析三角剖面及平坦/上下限/非法ROI/不支持dtype建立事前预期；旧路径与独立路径都需真实运行，差异非复制旧表。复用真实PID登记后放行请求、成功退出后终态CAS；候选清单验证与产物发布须有明确失败/取消行为。新契约按真实用例最小化，平台不引入WB语义。

科学留出、负责人判定、干净目标Windows和用户现场验收仍待外部条件；不阻塞已授权工程，不等价为新科学方法准入。

## 暂定集成候选

6421203以双亲合并已发布PR46 dca0061f与P001/T082链；冲突保留最新T082治理再接V0语义，B008原证据/任务不修改。P001暂以codex/b008-rd-plan-github为PR base，合入main前再次核对及重载。Node固定开发依赖`npm ci --ignore-scripts` exit0，报告4项moderate漏洞，未升级锁或运行自动fix；不宣称在线审计通过。基线规则重载后输出差异已逐段核读。
