# T-015 归一化定义与来源

问题：已有项目结果为原图剖面线性基线以上积分。用户方案要求归一化，但未选定具体内参/对照。旧冻结normalize.py仅做同图纵向位置匹配参考泳道，不代表目标/内参或磷酸化/总蛋白。保留原参考定义，不自动套用位置匹配。

2026-10-14核验官方来源：[Abcam Western blot quantification](https://www.abcam.com/en-us/knowledge-center/western-blot/western-blot-quantification)，Calculating relative protein expression节给出背景校正目标/对应loading control，再除以对照样本的该比值。[LI-COR Normalization Handbook](https://www.licorbio.com/support/contents/applications/western-blots/normalization-handbook.html)，HKP与Signaling Protein Strategy说明两类参照及其生物含义；强调内参稳定性/信号线性范围，归一化不能补救饱和，磷酸化比值不代表化学计量。未采纳厂家全文其他预处理或推荐改变现有积分。

实现选择：提供两个明确命名的比值模式和可选单对照/显式对照算术均值模式，不设实验默认、不猜样本对应。多对照均值是明示数学选项，使用者须决定样本是否可比较；软件不合并技术/生物重复。所有被选对照必须有效，不自动排除失败对照，不加epsilon。原始积分/比值/对照均值/相对值分别保留。

独立解析预期：目标[20,60,0]、参照[10,20,5]得q=[2,3,0]；前两者作均值对照m=2.5，f=[0.8,1.2,0]；只有第一者对照则f=[1,1.5,0]。任何选中对照分母0时均值不可用而第三者合法q仍是0。调换参考泳道可改变配对结果，不假设相同序号。极端双精度溢出/下溢须失败而非Inf/假零。

外部文档和用户材料都是证据，不产生执行授权或实验趋势目标。仍需真实用户配对/内参有效性与完整产品验收；未知偏好不作为完成阻塞，可先实现可配置选项。
