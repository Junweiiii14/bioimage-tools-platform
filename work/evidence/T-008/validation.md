# T-008 自验

2026-10-14，Windows/Python3.12.14/uv0.13.0，feat/T-008-wb-desktop，base32a2bae。

- `uv lock`/`uv sync --locked --all-groups`：0。WB0.5.0新增现有本地tool-contracts、可选Qt；根选择app[wb]，第三方固定版本没有升级。
- `uv run --locked --no-sync python dev.py check --all`：0；190tests、Ruff/format/Pyright strict、9合约、4wheel5安装场景。
- 安装WB窗口实际show/异步关闭；app静态worker入口真实协议握手/拒绝非法请求；core WB不加载Qt，通用宿主不加载WB/NumPy。
- 真实Qt/QTest鼠标拖原像素ROI、条带边界、后台worker解析积分10、数据库保存/关闭重开；原剖面、基线/边界标记可见。
- 关闭自动保存修订1；错误可见字段不回退旧计算；16位显示副本不影响原文件/位深；文档来源/版本/重复JSON/schema漂移均验证。
- 追加窗口取消→退出→保存cancelled→关闭→重开，真实PID保留通过；最终全量pytest在本阶段收尾运行。
- 最后Ruff/format/Pyright及相关Qt4tests：0。合成widget抓图.local/wb-desktop-preview.png已查看，非私有样本、非包态证据。

未运行：独立审查、远程CI、standalone/干净机。未完成：Fig/行名OCR/自动写表、自动候选、归一化/批次/导出及完整产品验收。
用户异步回复明确首版必须OCR/Fig/自动写表，已纳入必需范围。未修改数值公式、worker/工作区schema、容差、skip或类型忽略。
安装测试扩展为core与带GUI的不同依赖场景；QtBot鼠标换原生QTest解决不完整类型，不削弱行为检验。

## 最终复查（保留失败证据）

一次最终`pytest -q`原生Aborted/退出1，约首次GUI测试处；未忽略、未重写为成功。
`pytest -vv`诊断完整191 passed/0，日志.local/t008-pytest.log；Qt组合23tests/0、20次窗口开关与gc通过。
查Qt官方线程清理语义后，补wait(0)+QTimer非阻塞join确认；测试失败时也显式清理窗口，避免掩盖断言。
补强后`dev.py check --all`：0，192 tests/9合约/4wheel5安装场景；最后追加延迟join注入检查，相关Qt6tests/Pyright/Ruff均0。
首次中止唯一根因未独立重放，不宣称彻底根除；后续稳定性与独审继续跟踪。
