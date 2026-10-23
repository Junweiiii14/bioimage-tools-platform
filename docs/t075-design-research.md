# T075 参考与设计决策

2026-10-22 阅读官方页面；下表的 WB 实现是本项目的设计决策，不是对参考产品缓动、时长或代码的断言。
本轮是桌面工具设计：用户需要完整 Fig、明确原图和可恢复操作。视觉表现服务于这些工作。

| 参考画面 / 官方来源 | 体验意图 | WB 使用位置 | 实现约束 |
|---|---|---|---|
| [Linear 界面更新](https://linear.app/now/behind-the-latest-design-refresh) | 降低界面竞争，稳定主操作位置 | 顶部工作步骤、单区主按钮、来源侧栏 | 状态更新不重建正在输入的控件 |
| [Things 功能展示](https://culturedcode.com/things/features/) | 信息在原位置展开，保留任务上下文 | 精确参数、来源与质量说明 | 按用户操作展开；不因鼠标经过改变布局 |
| [Craft：Beyond CSS](https://www.craft.do/blog/going-the-extra-mile-bartek) | 微小选择反馈也需跨平台一致 | 按钮、主题选中、折叠与保存反馈 | 本地 SVG、真实回执、固定 WebEngine 中检查 |
| [Raycast 技术复盘](https://www.raycast.com/blog/a-technical-deep-dive-into-the-new-raycast) | 桌面网页交互连续，避免中间空帧 | 首次配色、抽屉、窗口变化 | 首屏前注入已验证偏好；不依赖动画计时提交 |
| [Amie Tasks](https://amie.so/documentation/features/tasks) | 直接安排对象，操作目标明确 | Fig 排序与落点提示 | 仅移动明确身份；键盘上移/下移同样可用 |
| [Arc Peek](https://resources.arc.net/hc/en-us/articles/19335302900887-Peek-Preview-Sites-From-Pinned-Tabs) | 预览后可返回原位置 | 来源短预览与固定详情 | 350ms 是 WB 选择；点击和键盘可获得同样信息 |
| [Superlist 基础](https://help.superlist.com/en/articles/10050-superlist-basics-lists-tasks-sections-meetings-explained) | 按内容分组，复杂性逐层出现 | 结果概览、完整记录、高级工具 | 单位、缺项、错误和未保存状态不能折叠掉 |
| [Figma 2024 复盘](https://www.figma.com/blog/figma-2024-we-shipped-it-you-shaped-it/) | 可收起工具，为内容腾出空间 | 右侧工具区、矩阵与成图画布 | 由用户主动收起；记住选择；入口一直可见 |
| [Carbon Motion](https://www.carbondesignsystem.com/building-blocks/foundations/motion/overview) | 日常反馈敏捷，关键转换更有表现力 | 即时按压、面板、页面、首页纸张悬停 | 120/220/320ms 是 WB 参数；ROI、科学曲线不弹跳 |

固定选择：forest 默认，ember / iris / neutral 可选；comfortable 默认，compact 只改间距；expressive 默认，gentle / reduced 可选，系统减少动态优先。
字体为本地 Noto Sans SC，来源和摘要见 `web_ui/fonts/source.json`；正文14px，辅助至少12px。
主题缩略图是共享 token 的真实组件，科学画布始终中性；导出图不继承 UI 配色。

同源边界：`index.html` 及相同 JS/CSS/字体直接装入 WebEngine。显式 `?preview=1` 使用合成资料适配器；默认桌面入口连接 QWebChannel。
预览的任何数值都标记为演示值，不能称为科学结果或真实保存。正式软件的完成状态依据真实事务回执。

视觉验收保留 1440×900、960×640 与高缩放内容区状态，四主题和关键交互。核对使用的 renderer、DPR、font status、console 和文件摘要；未稳定绘制的抓图不是验收证据。
