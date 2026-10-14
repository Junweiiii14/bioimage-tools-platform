# 元信息导入范围与只读选型

日期2026-10-14；Python3.12.14，现有标准库zipfile/csv/ElementTree，未新增第三方运行依赖。任务T-017，用户总体方案7.1/7.2要求原图批量导入、缩略图、实验项目/Fig/蛋白/N/空位/顺序/备注，Excel和文件名提取可修正。CLX按用户说明忽略，不推断_0/_1。

## 样例证据

只读查看用户项目工作簿：1表、50行49列，含订单、条数、内参、备注，190个公式；嵌入6个TIFF使总解压量约59MB，但工作表XML约54KB。此表是项目记录/计算布局，不具有“原图文件→蛋白/N”的完整映射键。不能因相近编号自动绑定。实际文件不改写、不执行其公式或附带程序。

## 备选和决定

不需要Excel自动化或完整重算/编辑库：产品只导入有限字面元信息且必须识别公式缓存。采用有界OOXML子集读取器，明确拒绝不支持格式，用户选择表头/列/目标并确认。引入openpyxl等新依赖可扩展复杂格式，但当前没有格式/日期/图表/公式求值需求，不以库默认行为扩展产品语义。CSV用标准库，文件名用明确字面分段，不开放任意正则或脚本。

预算只统计实际解析的XML，不解码嵌入图像：初次实样验证因全包解压大小预算拒绝；定位到图像后收窄到实际读取部件，单部件/累计XML及单元格预算保持。新增33MiB忽略图像和重复大区域反例，不以提高所有数据限额解决问题。

## 原始资料

- [Microsoft Working with sheets](https://learn.microsoft.com/en-us/office/open-xml/spreadsheet/working-with-sheets)，2026-10-14访问；页面引用ISO/IEC29500:2016，说明sheet关系、cell类型、v值及共享字符串；v也可能是公式计算缓存，因此不能只读v。
- [Microsoft Working with formulas](https://github.com/OfficeDev/open-xml-docs/blob/main/docs/spreadsheet/working-with-formulas.md)，2026-10-14检索；公式元素独立于缓存值。应用实现保守屏蔽公式/ref区域。
- [Python XML vulnerabilities](https://docs.python.org/3.12/library/xml.html#xml-vulnerabilities)与[zipfile decompression pitfalls](https://docs.python.org/3.12/library/zipfile.html#decompression-pitfalls)，2026-10-14访问；官方指出XML/压缩输入的资源风险。本实现预检DTD/ENTITY、限制UTF-8和STORE/DEFLATE、不extract、按实际读取部件与格数预算，不声称通用沙箱。在线3.12文档显示维护版本3.12.15，运行仍为项目锁定3.12.14，本轮未升级解释器。

## 验证与限制

解析型预期和反例、实际Qt预览/应用/保存重开/取消/晚到结果、已测4000/空/0保持及N变更失效、v5下OCR/归一化保留，详见work/evidence/T-017/validation.md。用户表原SHA前后相同；未将其任何公式/缓存/编号写入实验项目。真实映射与完整大批体验、独审仍待验收。若需.xls/严格OOXML、日期格式解释、跨表公式或每行不同实验项目，需新契约与兼容实验。
