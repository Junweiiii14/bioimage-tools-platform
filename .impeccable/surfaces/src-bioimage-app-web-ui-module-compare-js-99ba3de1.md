---
version: 1
slug: "src-bioimage-app-web-ui-module-compare-js-99ba3de1"
primary_target: "apps/desktop/src/bioimage_app/web_ui/module_compare.js"
related_targets: ["apps/desktop/src/bioimage_app/web_ui/module_compare.css"]
---

# P002 旧方法对照

Mode: Operate · existing Windows QtWebEngine surface extension · code-led.
Scope: 固定样例的运行、差异、来源和重开。用户已明确要求保持当前视觉语言；不更改主流程、实验草稿或主题。

## Direction contract
THESIS: 让用户从真实输出判断旧入口与独立模块是否一致，异常值保持空缺及原因。
OWN-WORLD: 沿当前T075/T077墨绿、青柠、本地Noto Sans SC、明亮工作面和40px操作控件；使用现有颜色变量适配四主题。
STORY: 顶栏进入旧方法对照，选固定样例并选新工程保存位置，运行后看并排数值与差异，再关闭并重开验证保存。
FIRST VIEWPORT: 受保护焦点的轻量对照窗口；标题与关闭在顶端，样例和运行按钮一行，状态紧随其后；主体为真实差异表，来源折叠；底部重开和工程文件夹动作。窄窗口控件换行，表格局部滚动。
FORM: 局部扩展既有工作台，不做概念投票；复用现有dialog形态以避免与主WB计算同时发起。运行中取消/关闭等待真实进程退出和存储排空，完毕才恢复原工作台焦点。
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Evidence
既有视觉证据work/evidence/T-077/platform-1440.png，与现行design_tokens.css核对一致。未引入图片或新字体。真实工作台运行/重开/原项目保留及退出排空测试2 passed（.local/p002-ui-capture-check.txt）。1440×900与960×640实际截图经impeccable_finish_reviewer审阅，局部视觉结论ship；documenter结论No changes，保持DESIGN.md。此结论不代替最终提交代码独审、科学准入或用户现场验收；预先存在的sidecar漂移保留。
