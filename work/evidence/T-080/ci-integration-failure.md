# 首次准确最终HEAD完整CI失败

PR40，HEAD `f363f37ab86012afa19e7e83eb4a158137bf9e00`，quality运行39929846271。
Linux：31 failed/1233 passed/510.62s；Windows：30 failed/1234 passed/530.35s。两者均失败，未进入全部wheel成功结论；rules-context和desktop-environment通过。前一产品HEAD运行39929534976已被明确取消，不作成功证据。

原始完整失败日志保留ignored `.local/T080/final-ci-failure.log`。当前仍未合入、构建或安装新版；源码独审Accepted不覆盖这次新反证。

待分类修复：

- reliable_geometry反例经公共新算法fallback被接受：端部弱/偏移/高条带、marker误认、局部噪声、错误N子集等。按目标保留真实弱/阴性泳道、N不冲突与注册约束分析；不能直接修改旧否定断言为通过。远弱杂点/部分第二行的常见策略变化需明确科学契约和独审。
- 两个pair-registration案例接受policy4与旧测试预期policy3不符：核是否真正有有效注册与完整槽位证据，再决定兼容预期。
- visible-export仍找旧project.zip，应按已批准完整交付新名字核验同一恢复内容。
- grouped安装诊断、sequence诊断断言、Linux batch lane overview UI失败，需读真实trace而非以GPU日志直接判环境。
- FigureComposition/DisplayFrame公开schema快照与新版本字段、旧边界错误消息未同步，需检查契约更新遗漏。

下一步只跑上述有新证据的定向复现，修复及独立增量审查后再提交新准确HEAD CI；保持现有门禁、原始素材及失败证据。

## 第一批兼容修复（未提交）

诊断和visible export验证改为新交付实际文件名“项目恢复.zip/灰度汇总”，CSV/XLSX逐内容/样式比较保持；sequence断言使用已批准v4的本Fig复核门禁名，旧v3严格暂停测试仍在。补FigureComposition公开schema的sampling_policy九行；旧within_roi@1恢复明确“超出原图ROI”错误，新within_source@2仍拒绝原图越界，未放宽边界。

`pytest tools/wb/tests/test_standard_display.py tests/test_visible_export_desktop.py tests/test_intake_diagnostic_lifecycle.py -q --tb=short --show-capture=no` 首轮11pass/1fail/51.30s，漏掉动态拼接measurements后缀；修正同一命名后仅visible export重验1pass/9.54s/exit0。完整内容比较与原ZIP不变断言全保留；Qt构造弃用和字体提示保留。日志ci-compat-repair.log/ci-visible-export-repair.log。无运行中Qt进程或exec session。

算法反例尚未修复。须结合用户已批准“明显主行优先/远弱干扰不阻断/少数项目错裁可接受”分类，不能为旧罕见拒绝测试把新策略整体退回旧严停；也不能把显式N内的弱/阴性样本丢掉。任何预期调整须解释政策适用范围并独立审查。

## 明显核心数量冲突定向修复（工作树中，仍待审查）

发现 `_basin_centers` 会为了压到N合并由深谷分开的明显核心，且二重条带就可被marker假设剔除。当前增量只允许谷/较弱峰比例至少0.5的碎核合并，深谷多峰保留count conflict；marker至少三脊，避免二重样本自动当marker。新策略常见场景11项保持通过；与exclusions/ambiguity/local_noise合并定向34项为16pass/18fail/5.99s，exit1，完整日志`.local/T080/ci-prominent-count-probe.log`。本次没有修改旧测试预期，未宣称全部算法通过。

尚余弱端部、偏形核心、部分另一主行、三重样本/marker、peer重复行注册等分类。当前guard阈值与marker改动须通过真实原图的有界影响复查、科学契约及独审后才可冻结；仍未跑完整CI。不要简单恢复原策略全部硬停，也不要以N外弱点的旧拒绝预期等同新需求。


## 2026-10-23 增量修复与预期迁移

- 最终HEAD f363f37 CI失败仍保留；本节为后续未提交修复，不回写旧通过状态。
- 独立科学分类：N外低显著结构/6像素小点可忽略，但显式N内弱槽不能删；明显强第三带/tall/doublet不能合并为N。旧纯domain严格拒绝断言保留。公共API新增主带完整原坐标覆盖、固定N、未审核、输入像素不变断言；显式N=3时检查完整槽或拒绝。伙伴未注册可继续所选信号，不伪造注册/辅助裁图。
- common@1尚未发布的实现修复：marker至少3脊（双带不足证据）；主行成员容差包含相邻doublet；碎片间距以实际相邻核心正间距中位数的0.75及膜尺度0.55两者较小者限制，避免宽膜内短行误合并；profile深谷比<0.5不为压到N合并。工程阈值不是实验标准。检测复制仍不进入定量。首版几何空隙限制导致真实18/21，被后继替代，保留现场。
- `pytest`此次7算法文件：58 passed/8.48s/exit0；包含11个common回归、强第三带和doublet拒绝、弱/阴性槽、配对与SHA篡改读回。
- 真实公共API有界回放 `.local/T080/common-ci-guard-v2-impact/report.json`：21来源案例全部自动采纳，18policy4/3policy3，9采集组两来源均可及3PNG转换图可；39原文件、转换图、历史基线SHA不变。该来源诊断不是21独立项目，不证明80%项目正确率。前版18/21日志完整保留。
- 合并定向命令包含上述7文件、standard_display、visible_export_desktop、intake_diagnostic_lifecycle及批量曲线UI单例：71 passed/58.32s/exit0，日志 `.local/T080/ci-repair-focused.log`。未重复全量；完整门禁交GitHub准确新HEAD。
- Linux原曲线UI失败各AND分量未捕获，原因UNKNOWN。现在仅在测量前有界等待真实入场动画结束，原lane3/4控制点/220px精确断言全保留；不增加容差。Windows本地通过不代替Linux新CI。
- 独审最少补项：未注册guided_common policy4真实提交raw crop后materialize，保留全部3原图SHA、仅所选1张原值裁图、2伙伴状态未生成：1 passed/1.57s/exit0。首试沿用旧阶段ticket被正确拒绝，修测试按既有真实工作流重新claim，不改产品票据门禁。
- 环境同当前Win11/Python3.12.14，依赖和锁文件不改。新HEAD独审/CI/PR合入/包构建与安装验证仍待完成。
