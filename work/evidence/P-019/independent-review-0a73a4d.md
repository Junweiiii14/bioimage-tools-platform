# P019 指定独立审查：changes_required

审查窗口 `01a1af0d-808e-7131-ae29-237aded27938`，2026-11-06。当前工程MVP存在两项已复现的实质问题，修正后按准确新候选复审；CI通过不能代替关闭本报告发现。

- PR：https://github.com/Junweiiii14/bioimage-tools-platform/pull/71
- Base：`3947261244143e3414b9bbf151bbe77c6edb5991`
- Candidate：`0a73a4d2753ddee0a94a172110b5102b9b39bfab`
- 独立检出：`bioimage-review-p019`，detached；作者开发树及成果未改，tracked保持干净。
- 范围：P018固定方法的CSV/显式板记录、数值结果、真实worker与Workspace提交/重开、取消/失败、包边界和独立wheel。GUI、完整可卸载矩阵、科学/LoQ、真人和安装不属本轮承诺。

## P019-R01 / P1：重开未核验结果内容却宣告成功

位置：`apps/desktop/src/bioimage_app/bca_cli.py:91-95`。成功账本的结果路径被直接加入输出，没有在重开时验证这些结果文件的实际内容。共享load路径只读账本，Workspace恢复检查登记元数据不等于检查payload；新CLI承诺的“重开校验已有资产”没有成立。

主审实际先通过CLI生成、提交并成功重开一个工作区，然后只复制审查者自己的工作区。在副本中把已提交`wells.csv`的S1 `original_ug_ml`改为`999999`，SHA256从`52b2c0fc7387457fe27a8f9ff04678128a23ec6ac7bb5e70f642585ccd180f87`变为`46b16b54c890c9945922006ec2972dc467a2ec7fe0704b7b7ab6dd90c9c19abb`。对副本执行`--reopen <原execution_id>`，实际exit0、state=succeeded、message/error_code为空，outputs仍提供损坏成果路径。原成功工作区摘要未变。

影响：误改或损坏的科研数值会被作为成功恢复的历史成果返回，与冻结出处/摘要不一致。不是要求防御任意攻击或引入新框架，而是当前重开契约必须成立。

最小整改：在重开成功及列出成果前复用现有Workspace资产、运行请求/结果清单的校验能力；损坏或缺失时返回非成功与具体原因，outputs为空。保留历史，不自动重算、修补或覆盖原结果。补结果损坏/缺失的实际回归，并保留正常重开无worker、结果不变的验证；不要求泛化重写执行链。

证据：审查树`.local/reviewer-e2e-a196a0dc/reopen-corruption.json`及同名stdout/stderr；正常流程在同目录`independent-results.json`。

## P019-R02 / P2：合法校准端点被浮点舍入判为范围外

位置：`tools/bca/src/bca_tool/domain/plate.py:73-79`。校正样本与标准均值使用不同浮点运算，严格比较会拒绝数学上相等的端点，违反P018“25至2000 µg/mL，含端点”的冻结口径。

保持示例空白均值0.05和其他数据，仅作以下变更并重算CSV摘要，两例都通过真实`read_plate`输入验证：

| 反例 | 数学期望 | 实际结果 |
|---|---|---|
| 25标准A2=0.070、B2=0.072，样本C1=0.071 | assayed=25 µg/mL | corrected样本0.02099999999999999小于标准均值0.020999999999999998，below_supported_range/null |
| 2000标准A9=1.103、B9=1.105，样本C1=1.104 | assayed=2000 µg/mL | corrected样本1.054大于标准均值1.0539999999999998，above_supported_range/null |

两例S1有效孔数均错误降为1，汇总变为partial，均值/SD清空。Decimal独立确认样本原读数精确等于相应标准重复均值；这不是实验LoQ或范围外推需求。

最小整改：处理机器舍入级的端点等价，补上下端点及真正越界仍被拒绝的回归。不能用宽泛近似钳制扩大支持范围，不修改NumPy或添加依赖；只调整扣空白/均值顺序不能保证消除此类误差。

证据：审查树`.local/plugin-review-p019/probe_endpoints.py`、两组CSV/record及`endpoint-counterexamples.log`。来源专项子审先实际复现，主审再用独立venv的`-I -B`执行确认；退出码0表示反例脚本完成，不表示产品满足端点契约。

## 已通过的独立检查

主审专属环境执行`uv sync --locked --all-groups --offline` exit0，没有修改共享venv；随后用`python -I`核实bca_tool、bioimage_app、platform_runtime实际来自本审查树。Python3.12.14、NumPy2.5.4。

- `pytest tools/bca/tests tests/test_bca_host.py tests/test_import_contracts.py -q`：36 passed/12.58s/exit0，QT_QPA_PLATFORM=offscreen、QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu。已有测试未覆盖上述两项反例。
- 独立CLI新工作区→真实worker→提交→正常重开均exit0。从28孔原始CSV以Decimal50重新计算逐孔逆值、预稀释、技术汇总：S1均值5008.6805555555555067、SD208.6947097251962489 µg/mL，逐孔原浓度最大差约1.12e-13，低于原软件容差1e-10；其余4样本partial汇总留空，其中PARTIAL仍保留1个有效孔。原始身份、读数、方法/API版本和出处输入摘要核对一致。
- 重复使用已有工作区开始分析返回exit2/input_failed，所有工作区文件摘要前后不变；正常重开无worker、路径及三份输出字节不变。CSV/record原件摘要未变。
- 执行链子审在同一独立venv真实worker：accepted后立即取消→cancelled/exit0/无候选目录；冻结输入SHA不匹配→failure/exit2/无目录；错误run身份cancel→failure/exit2/无目录；旧attempt回复明确拒绝。证据`.local/worker-review/summary.json`及各场景JSON。它们是worker协议实测，不冒称额外故障注入了完整Workspace提交事务。
- 主审实际构建tool-contracts与bca-tool wheel并用`installed_check`安装到独立环境，exit0；通过CSV/API数值及worker hello，API在安装环境中，未装Qt/runtime/WB/nuclei/SciPy。本次bca wheel为11552 bytes；不将压缩wheel大小冒充完整依赖或运行内存。
- 边界子审实际`tooling.import_contracts --no-cache`：12 kept/0 broken/exit0；新增BCA约束与反例未削弱原规则。78个第三方锁对象含版本/工件摘要完全不变，只增加本地包登记。P018方法/探针/参考和其他上游算法未改。
- `.gitattributes`仅示例及本轮结果设置-text，diff未禁用；Git blob与检出字节一致，源/record/结果摘要相符。P019前23孔字段保留P018参考，另5孔满足重复/partial示例；没有修改冻结参考。
- 主审准确base/head的rule_context check exit0。`git diff --check`实际exit2，报告4个受-text保护的示例/结果文件的CRLF为trailing whitespace；逐个原始Git字节检查确认没有CRLF之外的行尾空格/tab。原日志保存在`.local/diff-check-0a73a4d.txt`，未改门禁/配置或改写字节摘要以消除告警。首次汇总误用了后续git status的退出0，此处已更正，不作为新增代码阻断。GitHub审查时PR71 base/head一致，rules-context与desktop-environment已成功，两平台CI仍运行；未提前宣告完整CI成功。

## 未验与回传

没有重跑全产品本地测试、全部既有wheel/GUI或完整插件卸载矩阵；作者本地1757pass加2个既有canvas失败仍为作者证据，不能改记为主审全量通过。第三方未升级，未重审未变科学来源。无同SOP真实化学板、独立真值、LoD/LoQ、真人、安装器或目标机验收，原限制保留。

本报告已按用户授权回传上游，修复留原开发窗口。仅要求关闭R01/R02及其针对性回归，再提供准确新head检查受影响增量；不要求重做历史研究、添加大测试矩阵或为小收据反复推送。当前候选不得因CI成功而合入，本审查未代签合并。
