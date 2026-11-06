# P-018 固定BCA方法与研究输入契约

<!-- PROGRAM_TASK_META {"id":"P-018","status":"in_progress","work_package":"W07","depends_on":["P-017"],"execution_root":"C:\\Users\\70236\\ResearchVault\\Codex-Workbench\\bioimage-plan-sync","owner":"Codex BCA method research","base_commit":"dc2609dd79de98a63d4e8283e6c6db9e7c8e28ba","head_commit":null} -->

## 范围与验收

2026-11-06上游按用户持续授权在新窗口派发，已实际建立无预算goal。仅本共享树；保留0d134926收尾祖先。P018已查重。固定一种BCA单板方法的同体积、零标准空白、单位、范围与模型含义，核官方来源；有界寻找可许可同口径真实参考，缺失如实记录。直接调用成熟API做透明解析合成最小验证，交付方法契约候选与逐孔/样本输出说明。不得把软件复现或合成例当化学有效性；不改产品包、GUI、正式锁、算法本体或历史证据。不触碰旧dirty树、安装、原图；不外联、花费或发布。

完成自验后冻结base/head及证据，回传上游指定独审，正常PR及必需CI；修复留本窗，不自合并。B021规则由独立树维护，合入后重载main/context。最终更新交接、释放树并关闭goal，本窗不接新任务。

## 实验前判据

拟固定Pierce BCA MAN0011430 Rev D标准微孔板25 uL/200 uL、37 C/30 min、562 nm；确认原文后选公开API支持的逐点线性插值，禁止外推，不采用全域OLS默认。以手算分段中点及稀释倍数验证逆算；容差1e-10（仅双精度软件数值）。验证空白扣除、非单调标准、非有限值、超范围返回空数值与原因；不推测LoQ。真实数据检索限厂家资料、P017已知候选及一次定向公开数据搜索，不无限扩候选。

## 当前状态

来源/契约/探针已形成候选，见docs/research/2026-11-06-bca-method-contract.md及work/evidence/P-018/README.md。解析合成数值验证通过，完整真实板参考仍缺；不授科学或产品准入。8f947b4研究内容经指定独审pass；已合B021/main dc2609dd并重载规则，待准确最终增量复核与PR必需CI/上游集成。
