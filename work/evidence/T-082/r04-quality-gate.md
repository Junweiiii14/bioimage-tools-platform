# R04 固定开发检查

基线bd79474（纯格式产品266c068）。只增加开发依赖，不改变Python锁或产品框架。package-lock保留全部工件integrity；Node26.7.0/npm11.19.0本机执行。Prettier3.9.10、ESLint10.13.0、Espree11.2.0、TypeScript5.9.3固定，使用ignore-scripts安装，工具缺失/版本不符失败。

`dev.py check --all`保留policy/Ruff/严格Pyright/导入契约/pytest/wheel，并在pytest前运行web_quality；pre-commit的相关文件与现有quality两平台foundation也接同一检查。新增actions/setup-node固定官方v7提交，不改服务器规则、必需检查名、科学容差或原有门禁。远端未运行。

`makeAdvancedRequest`从既有advanced.js原地对象构造提取到一个已checkJs的纯函数，保留schema/字段/顺序/value对象；HTML在消费者前加载。真实类型约束覆盖共享项目/会话/修订身份和请求生成处，不虚称整个UI完成类型化。宿主原验证、pending/失败和大小限制仍在原处。

## 验证

- `npm ci --ignore-scripts --no-audit --no-fund`从锁重建79个依赖，exit0；`npm run check:web`及`uv run --locked --no-sync python -m tooling.web_quality`均exit0。
- 格式检查覆盖20个产品JS、lint当前全脚本0错误，checkJs strict/noEmit通过。
- 4个检查自身的验证全部通过：实际Prettier CLI坏格式exit1/合法exit0；实际ESLint CLI不可达代码exit1/合法exit0；真实生产函数和同一tsconfig的错误revision与requestId被类型诊断拒绝；实际请求wire精确保持。
- 实际受影响QtWebEngine：`QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu pytest tests/test_workbench_advanced.py tests/test_web_intake_supervision.py -q --tb=short`，**3 passed / 13.62s / exit0**（通过uv锁环境运行，Windows进程局部环境）。格式阶段更广19项见r04-format.md。
- 新Python入口/原dev.py Ruff和严格定向Pyright均exit0。npm audit当前0已知漏洞；不表示无未知漏洞。

第一次格式门禁发现Prettier的intake_groups方法链需第二次格式化，仅合并断行，没有表达式改变；最终检查幂等。首次类型负例夹具因Windows分隔符不一致，虚拟文件被识别为不存在（6053），修正路径归一后得到预期2322/2345类型错误；未忽略诊断或降低约束。

准确提交独审及最终冻结树全门禁待办。R03接下来复用现有DesktopDiagnostics补状态解析/渲染异常，R05数据端口在后续实现。
