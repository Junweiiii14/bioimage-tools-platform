# E6/T059 验证（实施中）

base8bf01f9，产品8feffce；规则已加载并与此前完整输出逐节比对，变化的index/snapshot/backlog/task通过PowerShell干净重读，未据乱码/截断改代码。基线两模式各20新进程实际0及预设阈值见baseline.md/export-before.json。

首轮性能改动：旧同修订PNG/TIFF/ZIP复用一份渲染；新Fig TIFF复用完整已保存PNG，来源绑定intake_saved_figure@1。原值/科学/项目schema不变。适配验证上下文由预览/编码两个真实消费者复用，未建通用平台抽象或全局原值缓存。

定向旧/新渲染、完整PNG/TIFF像素/来源、CSV、原值/缺图、旧归档故障与大图预览共44 passed/9.13s，实际0（.local/t059-render-second.txt）。首轮1failed41passed/10.54s，原局部PIL导入提取后预览NameError，已恢复预览局部导入；TYPE_CHECKING不当作运行时导入。Pyright初次dict未知/Generator标注已按实际类型修正，无ignore。未改断言/时限/容差/预算。

优化后20样本、真实宿主/完整门禁/最终独审尚未完成，E6仍implementing。科学/真实确认批次/目标机缺口保持。

## 性能比较和所属Qt测试

- 优化前后各模式20新进程0：旧p50 -28.91%/解码8→4/布局3→1；新 -17.78%/解码12→9/布局3→1，p95与RSS满足原冻结阈值，详见performance-comparison.md。性能子阶段225cac8静态非作者独审无P0–P2，未冒充全E6完成。
- 旧FigureProjectView与OCR/元数据/归一化面板的六个明确测试文件改为显式owned_widgets登记；每个所属纯控件正常close/deleteLater/GUI线程等待native无效。无全局发现/GC扫除，异步应用窗口仍用原资源关闭fixture。失败路径探针证明所属控件已失效且未登记控件仍有效。31 passed/8.94s0（.local/t059-owned-tests.txt），全仓Pyright0。
- 后继Ruff要求循环闭包显式绑定及合并with，已机械修正、定向类型0；无断言/skip/时限改变。原生purecall UNKNOWN依旧开放；未据这31项销账，最终inventory/退出另验。

## 阶段分页（待最终整体验证）

现有阶段列表由前50条截断改为50条分页，仍保持清单顺序和稳定ID动作；忙碌时只读翻页，不发后端写命令；刷新保持当前页/标题焦点，新项目和缩短列表时夹紧页码。10UI/11.51s实际0，覆盖104步骤末页输出失败/忙态/焦点/重试digest和缩短列表。全仓Pyright0、Node语法0；E6 detector一次仅intake.js，结果[]（0primary/0advisory），未再扫描。无新CSS token或设计漂移修复。
