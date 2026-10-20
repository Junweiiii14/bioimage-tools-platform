# T070 规划核验

环境Windows/PowerShell，活动树wb-grouped-intake，基线main6916b3a816b9a547ffdedf032a9dba82ce119c9d，规划分支codex/fig-sequence-plan。

- 只读核对HEAD/branch/dirty、main及现有分组/清单/账本/宿主/网页实现；开始时Git干净，fetch实际0。
- 已取得四项用户澄清：连续顺序分配、每Fig手填N、自动推进仅需人工时暂停、整批裁剪/拼图/定量/结果顺序。方案已定稿待审核，批准前不实施。
- `uv run --locked --no-sync python dev.py context --task T-070 --scope docs --scope work --scope .agent-handoff --scope AGENT_HANDOFF.md --record`实际0；回执base6916、四范围、七份规则hash与base一致；输出保存忽略的.local/t070-context.txt并按相关规则/任务阅读。
- `git diff --check`实际0；已安装maintain_handoff.py实际0，changed=0/warnings=0/unresolved=0。
- 审核稿/任务/索引10个相对链接检查有效，实际0；产品/测试/依赖/CI路径无diff。
- 未运行产品测试、Qt/WebEngine、自检、完整门禁、构建或安装；本轮仅规划，旧956等结果不验证本次拟议交互。尚未提交/推送/创建PR，不宣称产品已修改。

后续验收按方案执行，不以本文件的规划核验替代产品验证。

用户批准后：新受管树wb-fig-sequence从最新main6916b3a建立，分支codex/fig-sequence-automation；uv sync --locked --all-groups实际0，锁未变。仅明确承接方案、T070任务及两份证据，逐文件SHA及旧源不变记录于.local/t070-transfer.json，原规划树dirty未动。新树重新加载同四scope的T070回执实际0；此提交用于保留规划来源，实施另用T071当前回执和显式集成来源，不删除或冒充旧未提交回执已在main。
