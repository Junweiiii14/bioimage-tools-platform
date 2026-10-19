# E6/T059 验证（实施中）

base8bf01f9，产品8feffce；规则已加载并与此前完整输出逐节比对，变化的index/snapshot/backlog/task通过PowerShell干净重读，未据乱码/截断改代码。基线两模式各20新进程实际0及预设阈值见baseline.md/export-before.json。

首轮性能改动：旧同修订PNG/TIFF/ZIP复用一份渲染；新Fig TIFF复用完整已保存PNG，来源绑定intake_saved_figure@1。原值/科学/项目schema不变。适配验证上下文由预览/编码两个真实消费者复用，未建通用平台抽象或全局原值缓存。

定向旧/新渲染、完整PNG/TIFF像素/来源、CSV、原值/缺图、旧归档故障与大图预览共44 passed/9.13s，实际0（.local/t059-render-second.txt）。首轮1failed41passed/10.54s，原局部PIL导入提取后预览NameError，已恢复预览局部导入；TYPE_CHECKING不当作运行时导入。Pyright初次dict未知/Generator标注已按实际类型修正，无ignore。未改断言/时限/容差/预算。

优化后20样本、真实宿主/完整门禁/最终独审尚未完成，E6仍implementing。科学/真实确认批次/目标机缺口保持。
