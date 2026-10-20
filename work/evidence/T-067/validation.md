# T067 作者验证

工作树wb-grouped-intake，Python3.12.14/Windows，固定依赖不变。冻结提交由后续独审记录绑定。

- 核心分组修订新9项首跑8pass1fail/6.35s实际1：合成标签“Updated protein”超过既有标签宽度，显示适配器正确拒绝；改用同样语义的短测试标签AKT2，未改排版阈值/数值预期。
- 核心新修订/原分组/工作流/裁剪/完整Fig/输出合计45项/11.23s实际0。包括同内容不同来源身份仍撤回审核、取消源/N待定可重开、改N和移Fig、其他Fig真实run保持、标签/排序重成图复用原真实run、原@1 wire shape无editing字段。
- 新真实Storage/CAS与网页入口2项/4.47s实际0；有过裁剪attempt后明确返回分组，保存无来源草稿，禁止执行，真实重开按精确project_id/非忙态等待，重选源是pending，不恢复旧成功；原输入字节保持。
- 相关导入网页/真实宿主/快捷键52项/74.22s实际0。Qt SharedImage/context-lost诊断原样保留，不据此推断失败原因。
- Pyright 0 errors、定向Ruff/diff实际0；测试访问类型增加实际isinstance断言，没有ignore、skip、容差/旧预期调整。
- 合成Qt截图.local/t067-visual：entry、editing-desktop1440、editing-narrow620；实际脚本0、无文档横溢出。首次返回保留旧滚动导致标题离屏，已修进入编辑时回顶部并聚焦h1；复抓同一批状态并实际看图。新网页焦点/scrollTop断言1项/2.75s实际0。没有新图片资产或重复detector；截图不证明科学选择。

最终本地check --all/真实三目录完整链/新包尚未运行，留P7/P8；非作者独审、产品PR及四服务器检查另计。旧原生UNKNOWN及外部科学/干净机/DPI缺口保留。

独审定向修正后：快捷键/导入网页26项20.22s实际0，Pyright0、Ruff0。截图以真实crop/figure/output三能力flag重抓：进入编辑前有原图/布局/结果入口，编辑后仅分组页；实际脚本0、root已看图。测试Qt focusProxy增加非空断言解决静态类型要求，没有ignore。
