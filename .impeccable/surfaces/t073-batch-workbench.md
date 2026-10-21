# T073 仪器批次工作台

- Target: apps/desktop/src/bioimage_app/web_ui/intake{,_groups,_views}.js; intake_workbench.css
- Mode: Operate; Windows QtWebEngine / local HTML; code-led scoped redesign.
- User scope: 六项自动裁图修复，简洁清晰的专业工作台、HTML先预览、同规范落实软件和独立前端审核。
- References and rationale: docs/research/2026-10-21-wb-workbench-ui.md。
- Prototype: docs/prototypes/t073；明确合成示例，不作为科学计算或保存证据。

THESIS: 让用户从顶部Fig计划连续推进，随时看清当前蛋白、图像、阶段和唯一必要动作。

OWN-WORLD: 白色工具栏、矿物灰绿工作面#f4f6f5、图像台#e9ede9、深绿文字#22332f、
青绿主操作#087e71；Windows系统中文UI字体。视觉材料是真实科学图片和数据，
其余为平面控件，不造物理仪器装饰。警告只标真正需处理的状态。

STORY: 配置顶部Fig/N/逐行蛋白并手选原图；全部裁剪→全部拼图→全部定量→统一结果。
左侧对象、中间图像/当前蛋白曲线、右侧属性；窄窗口把属性放入详情抽屉。

FIRST VIEWPORT: 顶部56px项目栏与58px五阶段栏，配置表主次清晰，下方三张来源并列。
处理页215px对象栏、弹性画布、268px属性；1024px保留184px对象栏及可打开详情。
结果表按蛋白逐行、泳道逐列；状态与完整记录可到达。

FORM: 延用既有Operate方向的code-led工作流，本轮没有comp抽签/新种子；
源于明确产品对象与已打开的交互HTML。输入/IME/主动浏览不抢焦点，保存提交成功
才推进；140–200ms控件反馈，系统与应用减少动效均覆盖；图像/曲线/数值不装饰插值。

软件适配：真实范围/槽位/来源来自后端，原型演示N1–8不限制产品支持范围。
实际项目可有额外保存/历史/错误状态，保留文件菜单和高级能力入口；示例图不进入软件。
截图与交互测试/来源核验各自证明自己的范围，最终以T073任务的绑定提交独审和安装验收为准。
