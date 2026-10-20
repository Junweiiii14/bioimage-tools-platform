# 积分上下文与目录输入（2026-10-18）

问题：41槽复核是否都是边界错误，能否扩大ROI解决？目录为什么不能直接识别待裁原图、同Fig不能拼图？

实证：48槽20仅零像素/8仅背景不足/13两者兼有；当前背景策略平滑检测、连续3–10点支持，但单lane裁图过紧可缺支持。33零值提示不等于33已证明物理饱和，不能删除质量规则来制造有效信号。上下文扩大25%仍39review，扩大50%又产生9未检出；原目标可能被全区更强峰替换，独审解析反例实测已证实。新数值策略应保存target区间与context及绝对坐标、旧策略可重放，背景条件不足仍保留原因。

主来源：访问2026-10-18，实际SciPy1.18.1/QtCore6.12.0/WebEngine6.140.0。

- [ImageJ用户指南，Gels与扫描定量](https://imagej.net/ij/docs/guide/146-30.html)：峰需按背景封底；超出线性响应范围不能从图像恢复真实丰度。是否已饱和须证据，不能只因一个极值像素直接认定。
- [SciPy peak_prominences](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.peak_prominences.html)：prominence是相对轮廓的高度，局部窗口影响背景评价范围；不是全峰积分或目标身份的保证。

目录主线发现：现discover_tiffs把所有TIFF都送入定量，包括带本软件显示标识的成图；实际目录另有同次采集(1)/(2)/(3)。旧自动导入还将每源分别放入独立Fig并标Unassigned。新增folder_sources@1只读元数据排除已知派生文件，并按明确采集编号优先主文件，不解码参考像素；literal_source_labels@1只读明确文件夹/文件名标签，不推断实验配对。真实目录经正常后台选出的8源与冻结源清单匹配，四Fig真实工作台端到端0，量值保持。未知第三方处理图不能只凭后缀可靠识别，手动原图选择保留。

适用限制：编号规则仅同目录同采集键，未提供主版本不排除编号文件；文件路径/命名可能有歧义，详情需可查看并允许显式文件选择。未知来源/实验科学语义仍不得靠热门算法猜测。具体命令/退出和剩余项见work/evidence/T-044/validation.md及任务。新策略或新文件格式出现时重新核验。

2026-10-18后继实施anchored_context@1：只有原目标背景不足才逐步5–25%扩区，
最高峰必须仍在目标内且无竞争信号；第一个完整候选优先，不能选最大面积。
8原图正常工作台48槽背景不足21→2、有效7→13；33零值风险不动，没有积分真值准确率。
新采样区和目标原坐标分别保存，旧请求序列化字节保持，历史结果不迁移。

序列化来源访问2026-10-18，实际Pydantic2.14.1：
[官方dataclass/TypeAdapter说明](https://pydantic.dev/docs/validation/latest/concepts/dataclasses/)
和[官方wrap serializer说明](https://github.com/pydantic/pydantic/blob/main/docs/concepts/serialization.md)。
用局部wrap serializer省略旧策略两个新默认字段；实际冻结worker NDJSON字节回归，
而非仅凭文档假设兼容。三份机器schema可选扩展单独审查，新策略由显式版本识别、
旧读取器拒绝新策略；不声称任何旧软件都能读新策略。
