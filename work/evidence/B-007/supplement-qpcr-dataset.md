## qPCR补充：真实RDML逐孔数据已经取得

作者公开的[`rpa.rdml`固定文件](https://raw.githubusercontent.com/ramiromagno/rdml/fe484d11594735cfe2d65dcbcc1f58f9315a849b/datasets/rpa.rdml)提供8×12板布局、90个反应、3个有处理说明的鸡胚样本及10个靶标；每个样本×靶标组合有3个技术孔，3个靶标标为内参。实际检查得到88个Cq、2个缺失值，每孔另有61个扩增数据点，适合开发孔表导入、技术重复、缺失处理、接管重算与报告链。[作者论文及数据许可](https://link.springer.com/article/10.1186/s13104-017-2533-9)声明数据适用CC0；固定提交下载与本地文件逐字节一致。

其效率字段为空、所有参照样本标志均为false，内参稳定性、生物重复和独立相对表达真值未提供；morpholino对照也不能自动视为siRNA的匹配对照。完整计算演练必须显式给定设计和方法参数，不能默认E=2、把技术孔当生物学n，或将晚期Cq自动视为合格。该文件不是本项目全部qPCR方法的科学验证集。

本地`development-samples/rpa.rdml`为149,863字节，SHA256为`d77d72b962c94449d2844a071501d2ae920722f4a8816a967a49495a10eb4880`；`rpa-source-verification.json`保存逐孔解析和来源。孔位按RDML 1.2行优先规则还原；B10/B11缺Cq，归属R-HCtrl13×GusBP1，不能零填充或仍记为3个有效孔。未做完整XSD验证、产品reader或新Cq算法，原始数据读得出不等于整条方法已通过。
