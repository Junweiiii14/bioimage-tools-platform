# T-033 网页优先同源桌面界面

- 状态：implementing。用户2026-10-16要求先写网页，再一比一完成桌面；明确使用skill、专业审美与动效。已授权实现，不重复选方向。
- 基线7d97a6e，协调树codex/t033-web-first-ui，旧主目录dirty不动。
- 设计延续已确认图像中心三栏/平台/WB任务结构，网页先行，桌面QtWebEngine加载同一资源确保视觉同源；该组件已包含现有固定PySide6，无新增依赖或框架升级。
- 范围apps/desktop、tests、docs、work、.agent-handoff、PRODUCT.md、DESIGN.md、.impeccable。不改数值/科学schema；用户原图/历史输出不可覆盖、不提交。
- 网页可操作预览和桌面真实工作流必须区分；演示操作不冒充真实计算。首屏精密图像工作区，工作台入口、复核、拼图、结果可切换，键盘/减少动效/错误状态可用。
- 技能：Taste已读，明确不适合应用屏幕，不照搬营销页面；借用此前product-performs方向。Impeccable Operate用于前端实现/动效/独审。
- 验证：浏览器桌面/窄屏、同资源桌面截图与交互；真实导入自动创建及输出/取消；独立审查与明确兼容边界。
