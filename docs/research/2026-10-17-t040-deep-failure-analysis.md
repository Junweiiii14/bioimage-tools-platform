# T040 真实失败的深度技术解析

日期2026-10-17；产品f7a6651，审计HEAD cc626d7；锁定NumPy2.5.4、SciPy1.18.1、tifffile2026.9.20。本轮不更新依赖、不修改产品。

## 问题与验收

解释首轮1/8、参考辅助8/8以及旧峰边界17/48严重偏低的机制；区分原图、检测副本、展示像素、采样区域和生物学结论；审查脚本演示与普通UI产品能力差距。不能以输出数量、SHA或测试数量替代准确率。

完整报告与代码索引见 [深度技术限制报告](../../work/evidence/T-040/deep-technical-limitations.md)。本文件保存研究方法和来源，不重复大段技术内容。

## 最小实验与结果

1. `.local/t040/diagnosis/deep-causal-replay.py`，exit0：仅读取八张已授权原图，核对首尾SHA；膜定位crop_height60/2对照，三张失败细化膜高107/119/118，低于默认120。复放原五阈值与Marker规则，证明两张内参先得到8中心又被Marker误删至7；4H NSUN6四段被CV0.29368>0.15淘汰，再回退到两段。未读参考图，不是修复准确率试验。
2. `.local/t040/audit/deep-boundary-replay.py`，exit0：17个严重低值原ROI重跑旧边界路径全部复现。17/17只有一个included主峰且无border inset；最近原始profile局部谷优先造成峰旁端点。16/17低confidence<0.1是描述性统计，不是验收阈值。内部11ok/6needs-review，应用3valid/14quality_review。整窗对照不是科学真值。
3. 只读实际TIFF标签：原目录标准图1200DPI；每泳道1200px实际2.54cm。单Fig内嵌font160/heading190分别超模型上限96/128，普通model_validate实际失败；主项目及ZIP合法参数不连带受损。大拼图坐标缩略风险仅静态推导，本次总览1992×688未触发。

## 备选与决定

仅降膜高门槛不能修Marker误删与边界；仅旋转不能修所有N推断；直接全窗统一积分不能自动解决邻峰/背景；用显示图测量会改变原有采样语义。应分阶段消融：膜定位→角度→行/泳道结构→Marker去趋势→原坐标ROI→背景锚点→质量证据传递，并保留冻结旧WBQuant及Signal公式，用新版本策略承载边界改进。本报告提出候选方案，不宣称已实施。

## 外部来源（2026-10-17核验）

- [SciPy affine_transform](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.affine_transform.html)：输出坐标反向采样、插值、边界扩展。当前网页版本1.18.0，仓库锁1.18.1；仅援引基础语义，不假设两版运行完全等价。
- [SciPy peak_widths1.14.1](https://docs.scipy.org/doc/scipy-1.14.1/reference/generated/scipy.signal.peak_widths.html)：相对prominence宽度、交点插值。用于术语定义，不作为现版本所有实现细节的替代；实际行为以本机锁版与重放为准。
- [Bio-Rad Bulletin5809，2008](https://www.bio-rad.com/webroot/web/pdf/lsr/literature/Bulletin_5809.pdf)：直接读取PDF文字，第2–3页动态范围与饱和、第3页显示灰度映射；只支持一般数据限制，不确定本图采集链。
- PMC3971489本次直接打开遇验证码、Bio-Rad Total Protein Normalization页面遇重定向；不将未获取正文细节作为新个案归因证据。

## 限制与复核触发

八图已参与诊断，不能继续称独立盲测；后续需未参与调参真实图片。像素0平台来源、不同曝光的线性、整体峰值RSS、全check退出异常仍未知。任何策略/预处理/几何/单位/schema变更必须重新审查本报告；输出值复算一致不等于蛋白量准确。
