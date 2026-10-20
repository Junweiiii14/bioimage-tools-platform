# T071 独立审查

## 纯核心增量 edb5a5e

- 非作者审查者 `/root/t064_independent_review`；绑定 edb5a5ed7c5cdbcc98eb034e35dcb3ac6c8b6a97，比较基线 0a966e84c7c07ca26dd71fade4dfe27e6bb4e435。
- 结论：Accepted；未发现可证实的 P0–P2。归档副本与共享工作树隔离，禁止 PySide/pytestqt 导入；未修改共享产品/Git。
- 四个核心测试文件加九个独立反例，共 40 passed / 6.55s，实际退出 0，包含 80 个 Hypothesis 输入。
- 验证新组不继承排除、异常整批暂停、旧策略继续其他 Fig、部分修订保留其他 Fig 已完成证据、标签调整复用同原值运行（合成证据）。
- 隔离比较基线与被审提交的五种旧格式：manifest 1/2/3（grouping 1）及 workflow 1/2，完整 JSON 和 intake/workflow 摘要逐字节相同；比较器与两个子进程实际退出 0。
- 本地细节 `.local/t071-independent-edb5a5e/review.log`。此审查不覆盖后续单一启动、CAS、网页导航、安装诊断与打包；最终产品提交仍需独审。

## 产品增量 2a676e3 初审（待复审）

- 非作者t064_independent_review，edb→2a676e32b25e5081393788d7c18aadd04729d88a。隔离AST会话控制24通过/2失败、5.47s实际1；发现一个P2：预览资产/渲染回调遇到直接关闭或同key代际失效，未结束已拥有的busy。正常取消再关闭分支不属此缺陷。其余CAS/取消/旧代际、别Fig历史保持通过；未运行Qt/私图。修复需绑定新提交复审。
- 新鲜t071_finish_reviewer：八张有效图（五Qt配置/网格1440、1024、390及三同源冻结DOM的1280阶段图）与源码审查为fix：P1手动浏览未停止跟随，P2暂停原始诊断缺可操作说明，P2重新载入未说明丢弃草稿。布局绘制无有效截图，不记通过；无需替换视觉体系。三项已修复，待最终确认批次及绑定复审。

## 最终产品 c9355ba 复审

- 非作者t064_independent_review绑定c9355bae7dd038e70cc1b57fe6e10c043aa46c49（2a→c935）；原P2 resolved，同key关闭/代际失效结束所属操作，旧key不结束新操作/不安装预览。AST/纯会话控制32项/4.98s实际0，含原CAS六分支与prepare/continue历史保护。
- 参考与兼容纯控制40项/4.80s实际0，含80例既有性质和50例独立reference子集性质；缺观察/混合raw/读取失败/错SHA拒绝伪参考。旧保存分组保留source选择、只提供新candidate，旧行式确认项目无grouped_draft且绑定/确认摘要不变。七种旧wire和digest由两隔离进程逐字节比较0。
- 旧manifest2、grouping=None且proteins空的池仅首次快照提供参考候选，project JSON/digest不变；此形状不能持有来源对应或有效确认。因此合同收窄为已有分组/行式对应/已执行项目不自动分类重排，不为文案扩展做schema迁移。
- 产品增量Accepted，无其他可证实P0–P2。静态+纯隔离边界，未运行Qt、真实worker、私图或完整门禁；不冒充这些验收。
- UI非作者t071_finish_reviewer绑定同一c935：ship（限定原三项及相关新增范围）。自主浏览/选源焦点保护、中文暂停说明/折叠原诊断、明确放弃重载均resolved；参考单列和快捷键继续/仅保存静态路由resolved。三张有效Qt配置图1440/1024/390，加五张同源DOM IAB1280图（grid/references/review/quant/results）逐一审阅。重复配置命名图不计网格证据；layout无有效绘制图，不在ship范围；新增快捷键未独立动态按键，未运行第二detector/Qt。证据本地.impeccable/review/final，私图不入库。

- 最后修复后documenter t071_documenter仅补web-workbench surface的行为和证据边界；既有DESIGN/sidecar/PRODUCT保持，普通Operate延伸不引入新设计体系，不顺带修复旧漂移。brief diff检查0，未运行第二detector/Qt。

## 安装诊断取证修复 20c106f

- 非作者t064_independent_review绑定7e6568300e5eded27001b25c01f35bc451310224→20c106f6e34523bfb39c00d687b7c1faccbb8fc9：Accepted，无可证实P0–P2。
- 冻结AST原样提取observed/traced_save及实际host.save/_storage_reply，18纯控制/1.67s实际0（.local/t071-diagnostic-20c106f/run_review.py）。编码/存储前不观测，CAS/guard/代际/取消不伪造事件；成功安装后先观测再原after一次；异常不吞，patch正常/异常均恢复。精确集合拒绝缺项/外来或重复target凑数，屏障违规仍失败。
- 时限120/150秒、25ms轮询、真实网页导航/worker/原像素/输出/重开/关闭要求不变；生产调度、CI和其他UI无diff。未运行Qt/worker/完整门禁。初版独立.local探针nested-with AST定位错误收集exit2，仅修该探针遍历后通过；无产品/门禁变化。

## 真实数据证据只读复核

- 非作者t064_independent_review冻结20c106f公开API，只读本地TIFF/SQLite/输出；Accepted。未运行GUI/worker，未重跑数值流程，也未外传私图。
- 核对47组（19执行、28参考）、85来源/76内容SHA、74稳定槽位；两次快照共38份裁剪与原图ROI逐数组、dtype和shape一致（uint16×16、uint8×22）。208历史草稿资产摘要有效；196→197只失效一个Fig，其余18个Fig裁剪/成图/分析完整对象保持，206→207重开结果不变；81个持久运行快照符合整批屏障。
- 20个成功RunRecord/PID、38结果来源引用及请求source_sha256有效；旧/新输出254/255成员的SHA和大小、表内74槽位身份逐项核对。19项来源/ROI/标签/N与控制器选择表一致，后续修订仅首行ROI的y±2。
- 当前104个源文件与既有T069持久114项清单的对应子集摘要一致。本轮104项初始清单仅在控制器内存，没有独立持久逐文件启动清单；不得补称已有该证据。属于已见参考辅助回归，不证明生物配对、科学真值或留出准确率。
- 首个合并探针在像素/历史核对完成后误用AnalysisRequest.asset_sha256而退出1；改用公开source_sha256后只续核剩余run/output，6.28s实际0，另选择/历史控制1.66s实际0；未重复数值流程。

## 所属端口关闭顺序 a952555

- 非作者t064_independent_review绑定cb2c26a63eb4a5c00994094d0f1441f06fa9553e→a9525556369e5757ae87c862e5b332c675921de7：Accepted，无新增可证实P0–P2。
- 冻结实际save/_storage_reply/closeEvent/_finish_close、全部closed回调及resources_closed，11纯控制/1.50s实际0（.local/t071-close-order-a952555/run_review.py）；diff检查0。最终编码/CAS成功后才关闭WB，失败不关闭端口、不提前成功；WB完全closed后才关storage，提前closed和重复close均正确。恢复/selection/扫描未结束时，即使双端口closed也不宣告完成。
- 未启动Qt、worker或完整门禁。接受局部顺序修正，原Windows原生挂起仍需新CI验证，不表示历史native UNKNOWN已解决。
