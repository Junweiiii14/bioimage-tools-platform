# T-050：元信息先行的WB自动流程与结构收敛规划

- 状态：review（规划与GitHub草稿PR已交付；S1/S2已确认，独立定量须保留OCR，未实施产品）
- 日期：2026-10-19
- base commit：221a2dff610554092a881fc396010f032b31ae33（GitHub main）；产品只读审计基线a234354。
- 用户授权：理解并澄清需求后更新GitHub最初开发规划；改进建议供用户审核。
- 已确认：每Fig固定样本槽位N包含空位、不含Marker；缩略图/原名批量分配并确认Fig/蛋白；先拼图再触发定量，计算始终读原始像素。
- 范围：README.md、docs/wb-development-plan-v2.md、work/tasks/T-050-metadata-first-plan.md、work/evidence/T-050、.agent-handoff。原始PDF、代码、依赖、算法和数据不修改。
- 产出：新版流程/验收/模块结构与成本优化计划；区分已确认需求和待审建议；文档PR，不夹带未集成产品分支。
- 验收：事实绑定产品审计基线，原始PDF摘要不变，规则回执/链接/diff检查及独立文档审查；GitHub链接可审阅。主分支合并须PR及必需检查，未运行测试如实说明。

## 交付与验证

- GitHub草稿PR：https://github.com/Junweiiii14/bioimage-tools-platform/pull/16；仅文档，不合并main。
- 历史方案942ecaa独立审查无阻塞；本次S1/S2确认与独立OCR要求修订后重新审查，见work/evidence/T-050/independent-review.md。
- 本地链接、diff、规则回执、policy及handoff容量通过；PDF原blob不变。仅治理验证，不表示产品通过。
- GitHub检查异步运行，最终状态以PR为准，不把初版head检查套到后继。
- 下一步：按已确认的S1/S2、独立定量OCR及跨蛋白独立槽位规划，核对真实仪器多曝光规则，再建立M0实施任务。

- 后续澄清已确认：同Fig仅共享N，不保证跨蛋白样本顺序；以行ID+本行slot ID填表，没有映射不自动跨蛋白配对。增量独立审查已绑定942ecaa，无阻塞。

- 2026-10-19用户批准异常局部暂停、独立结果目录，并明确单独灰度定量仍需OCR；不推断为批准OCR安装包拆分。新批量不用OCR，独立拼图定量保留OCR。
