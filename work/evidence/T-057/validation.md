# E4/T057 验证（实施中）

base1719a2d，Win11/Python3.12.14/Qt6.12.0，锁未改。
核心首批3 passed/2.42s，定向Pyright与Ruff0；旧E2/E3核心14 passed/4.44s。
覆盖两Fig一缺一完整、同名蛋白不串、schema13/旧读拒绝、实际资产恢复路径重映射、
未claim/取消/变源不发布、完整成图后才可measure、空回复不作done、实际原数组三角
解析积分400/800按源倍数、无信号not_detected、显示lane_unit120→60请求逐字相同。
运行引用在纯应用测试中是显式合成RunRecord/已验证结果，不冒充真实worker或收据。

首轮测试误用measurement.area而现有公开字段是signal，改用真实字段保持解析预期；
旧修订伪造先被ProjectRowAnalysis拒绝，后将伪造改为合法修订但错误极性，以确实
检验冻结请求不一致拒绝。没有放宽答案/容差/skip/门禁。动态列表补显式类型，
未添加类型忽略。宿主/真实worker/界面/完整门禁与最终独审未完成。

## 宿主与界面候选（待最终提交）

- 真实桌面闭环1 passed/8.42s：成图与请求先实际保存，prepare_run读取的冻结JSON中compose done、measure running，两个真实pid worker成功、平坦原图未检测不作零，schema13重开核验同RunRecords与缓存。
- 三种失败/取消与真闭环合计4 passed/12.63s：compose终态CAS失败、measure claim CAS失败、晚到成图取消均不启动测量、不装假产物；单测量取消1 passed/4.78s，首行真实准备后取消并恢复launch，下一来源未启动。
- 核心/桌面/前端联合31 passed/33.68s；最后桌面/前端27 passed/32.89s，真实WebChannel保持layout/results、图块回正确原行、同名蛋白标行序、有效/待复核原始积分分列、固定N与本Fig重试。
- 大图预览2048边限制，原PNG字节不变，保留原source ROI/output_box，单独preview_output_box/preview_source_to_output缩放；四核心3.44s。单独preview_binding绑定当前项目修订/成图资产摘要/输入，不把旧PNG修订改成新原始证据。
- 旧E3重开期望12随显式新schema13升级改为13；旧不支持legacy命令错误文案“尚未接通”改为真实的阶段执行入口，拒绝与无处理断言保留。新大图测试起初误将row_id已单列的manifest ROI预期为也含lane_id；改为显式原坐标四边+独立row_id集合与变换不变量，无放宽几何预期。
- 最后Pyright0、Ruff0；纯核心增量e8e2f96非作者17 passed/3.12s及独立错行顺序/取消/恢复摘要探针0，无P0–P2，不代表宿主已独审。
- 同源浏览器合成预览1280×720，.impeccable/review/t057-browser-{intake,stages,figure,results}.png已逐张打开核验；本地fixture的CPU数值/合成RunRecord仅作视觉，不冒充真实进程/科学真值。真实worker另由上列桌面测试证明。首轮fixture误用reviewed而非ready裁图enum已修正，并按真实ledger使未处理行pending；二轮同视口复验完成。Tab实测从Fig标题到手形平移；切results焦点为结果标题。
- E4 detector仅一次，.local/t057-design-detector.json为[]、0 findings；未重扫。完整门禁及宿主/界面最终独审未完成，E4仍implementing。
