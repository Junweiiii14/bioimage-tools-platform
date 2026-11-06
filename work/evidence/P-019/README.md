# P019 候选自验与独审入口

阶段：实验工程研究MVP。范围/运行命令见[任务](../../tasks/P-019-bca-csv-adapter.md)和[工具README](../../../tools/bca/README.md)。准确候选SHA与PR在上游请求消息中绑定；本文属于该候选，不自称独审。

## 作者自验

Windows / Python3.12.14 / NumPy2.5.4，活动树bioimage-plan-sync；PR基线3947261244143e3414b9bbf151bbe77c6edb5991，保留2bfd40c前窗收尾。`uv lock --offline`、`uv sync --locked --all-groups --offline` exit0，只新增本地bca-tool，第三方版本/工件未升级。

- `uv run --locked --no-sync pytest tools/bca/tests tests/test_bca_host.py tests/test_import_contracts.py -q`：36 passed，exit0。覆盖CSV身份/数值/记录、非单调曲线、范围/partial、真实worker成功/失败/取消、Workspace重开与旧输出保护、传递导入负例。
- `uv run --locked --no-sync python -m tooling.import_contracts`：12 kept，exit0。新增BCA领域纯度及现有跨工具/平台禁入登记；正反例期望从11扩至12，未削弱既有门禁。
- 独立bca-tool wheel安装与CSV/API手算对照及worker hello：exit0，源码隔离且无Qt/runtime/WB/nuclei/SciPy，压缩wheel11629 bytes；本地原日志`.local/p019-bca-wheel.log`。正式门禁同探针已接tooling/installed_wheels.py。
- 最终数值代码真实CSV→worker→提交→重开均exit0，见[execution.json](execution.json)及[正式逐孔](results/wells.csv)、[样本](results/samples.csv)、[出处](results/provenance.json)。S1均值5008.680555555556、SD208.69470972519616 µg/mL；先平均吸光度再反算的5000不是本方法。源CSV及板记录摘要、请求身份、方法/API版本保存于出处。原P018参考未改写。
- 首次端点测试误用精确浮点相等，25.000000000000007与25相差7e-15；已按P018事前软件容差1e-10断言，无算法/科学阈值调整。初期格式/类型问题已修正，无ignore/skip新增。
- `uv run --locked --no-sync python dev.py check --all`：exit1，1757 passed / 2 failed / 10 warnings，1271.97s；前置policy、ruff、format、Pyright、import-linter及web门禁通过。两个失败为既有旋转canvas 5000ms超时（test_rotation_preview_and_one_real_click_commit[True]、test_rotation_handle_changes_main_frame_and_preserves_saved_preview_size），带SKIA/context lost日志。本地原日志`.local/p019-check-all.log`。不修改旧UI、容差或门禁来掩盖失败；CI渲染环境（QT_QPA_PLATFORM=offscreen、QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu）定向复验3 passed/33 deselected、10.72s、exit0（`.local/p019-rotation-ci-env.log`）；随后`python -m tooling.installed_wheels`完整独立安装/宿主/编排探针exit0（`.local/p019-wheels.log`）。不抹去初次失败，不能称本次本机全量通过或物理GPU根因解决。

24,365 bytes新工具Python源码，另有宿主CLI/装配；新环境未引入。示例首次新工作区执行1.4608s（已有环境/缓存，不是机器冷启动）；完整依赖磁盘与峰值内存未测。无新模型。共享执行/存储无实验分支；固定协议工具侧沿用既有消息形式，未新建引擎或插件框架。

## 来源与未验

自研增量：tools/bca、宿主bca_cli/bca_workflow_host、测试与显式依赖/边界登记。第三方保护：NumPy2.5.4、已锁所有第三方工件、P018冻结研究输入/探针/参考完全未改；未patch或monkey patch。本任务只消费P018契约，无新算法研究。

B021只从7a0d718bcb8b76d2a59124307ed91f4abfa69616带入任务、agreement、validation、final-delivery四份已核对收据；未采用其snapshot/规则回执。P018收尾2bfd40c保留。

同SOP真实逐孔/独立化学真值/LoQ/真人/用户安装均未验；研究状态不解除这些缺项。单节点覆盖本固定方法，GUI、自由拆分节点、全套可卸载矩阵及统一前端不属本轮。下一最小建议按主方案第11节集中统一已有工具入口/结果与编排，不继续扩孔板后端。

冻结前Git字节核验发现CSV换行正规化会使示例source_sha256失配；已为tools/bca/examples及本轮results加窄路径-text属性，保留生产者字节。入口摘要校验未放松。正常git commit首次因未激活环境找不到pre-commit被拒，改用uv run --locked --no-sync git commit后全部提交hook通过，没有跳过hook。

## R1：关闭指定独审两项发现（待增量复审）

[原报告](independent-review-0a73a4d.md)由指定审查者提供，准确0a73a4d结论changes_required；保留真实报告及diff --check仅CRLF告警的更正，不改成通过。

- R01：CLI在session释放存储后通过Workspace与validate_workflow_result_selection核对run/request/manifest、输入及结果实际字节。成功状态先显示verifying，只有完成核验才返回成功和路径；损坏/缺失返回failed/result_integrity，原账本和结果不修补。真实同长度篡改和缺失反例通过，正常及旧0.1.0重开无worker、不重算。
- R02：标准均值遵循P018探针的mean(raw)-blank；只在25/2000两端按原读数最大ULP的2倍判机器等价，再使用同一NumPy interp。不使用科学容差或全域钳制。Decimal确认的两项反例精确输出25/2000；向外1 ULP作为机器等价，向外1e-12仍范围外/partial。
- 包/API及module_version升0.1.1，implementation digest随源码改变。固定方法ID、schema1、科学支持范围及LoQ未知不变；这是既有含端点/核验恢复契约的bugfix，不迁移或覆盖旧成果。uv lock/sync offline只改本地BCA版本，无第三方升级。
- 定向pytest（同前命令）38 passed/8.58s/exit0；Ruff与Pyright strict exit0；新0.1.1独立wheel探针exit0。日志.local/p019-r1-tests.log、p019-r1-wheel.log。新完整执行/重开和旧0.1.0重开均exit0，见[execution-r1](execution-r1.json)、results-r1；旧execution/results保留，不覆盖历史。
- 未重跑未变科学研究、旧UI或全部本机测试；PR准确新候选须再经必需CI与指定增量独审。新增results-r1同样-text保留字节摘要。git diff --check的CRLF末尾告警仅在这些显式二进制保存路径，不能误报为无告警；不改原数据或全局检查规则。
