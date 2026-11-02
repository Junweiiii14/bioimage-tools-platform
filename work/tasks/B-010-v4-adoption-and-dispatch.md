# B-010 4.0方案接入与新执行聊天派发

状态：done，2026-11-02。同步与派发完成，不表示产品验收已完成。

用户授权：同步新版到实际开发目录，先完成独立WB模块验收，再推进通用工作流执行与可视化编排；新聊天使用gpt-6.1-sol、medium，启用目标模式持续工作。

基线：bioimage-v0，codex/p002-wb-headless-module，78403be43b225da3626e3a6ef0a8aeda2cbbbaec；既有未跟踪work/evidence/P-002/frozen-runs/保留。旧执行聊天已idle/interrupted，避免并行写产品树。

范围：白名单同步4.0方案/研究/内容审查，旧目标方案归档，保留较新治理与P卡；语义更新授权和入口。P002状态不改done、不改产品。新聊天继续P002并负责后续任务拆分/登记、代码、验证与准确提交独审。创建后核实实际目标模式。

验收：源目标摘要、HTML重建、计划检查、handoff维护、新聊天模型设置与get_goal实际证据。未知科学/目标机事项保留，安装器发布/数据上传/外联不扩权。

## 同步与派发证据

- 10个白名单文件源目标SHA一致，主源5a1eb003deacbad724c348937900530a29a2f9eb9b8b956eff1cc43b7068b62b，详见transfer-manifest.json。
- 目标树原方案及snapshot先备份.local/B-010-before；发布版3.0另归档，产品文件和P002状态保留。
- npm ci（锁定marked17.0.5）、npm run build、plan checker、268个HTML链接/锚点及摘要验证、git diff --check、规则重载均exit0。handoff维护exit0，归档1段旧日志，unresolved=0。
- 未运行产品测试/科学/目标机验收；没有远端发布。同步改动尚待新执行者正常提交/审查/集成。
- 新聊天01a199d4-dac3-7dd3-af35-cdad7d361934，host local，create_thread明确gpt-6.1-sol/medium。目标模式须以goal-state.json和实际工具返回核实。

目标状态已核实：新聊天active，原生goal active、无token预算；真实执行目录bioimage-v0，正在恢复P002门禁与验收。证据goal-state.json/dispatch.json。后续代码与交接由新聊天唯一执行，本派发聊天不并行修改产品。
