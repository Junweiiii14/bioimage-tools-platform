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
