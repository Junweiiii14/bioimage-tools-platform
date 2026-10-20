# T066独立审查

冻结初审head c78c6066aaed4365e30d2b82a613f3b2a9186cdd，base6bba535。

实现非作者t064_independent_review：冻结7/7.27s实际0；发现P2，错误弹窗内明确的“重新选择项目”按钮也被统一动作的全局dialog保护挡住。冻结真实Web反例1failed/4.39s实际1，choose调用为空而预期open_project。没有其他可证实P0–P2；初审不是通过。

界面非作者impeccable_finish_reviewer：disposition fix。初始焦点、冲突反馈/禁存、窄窗、体系匹配；重绘设置列表时只恢复键位input，禁用/恢复/保存按钮焦点丢失且滚动重置。要求按控件类型/动作ID恢复焦点与滚动，保存暂禁时有稳定回退。仅只读检查/截图，未运行程序或detector。

只读documenter：No changes。PRODUCT/surface/README/契约已对应21动作、760px dialog及窄窗、系统中文13/12/20局部字阶；全局DESIGN/sidecar无变。预存漂移不扩范围。

作者修复：键盘继续受dialog保护，只有当前session错误dialog内明确open按钮走同一打开动作；设置列表保留控件身份、scrollTop，保存暂禁时焦点落status，实际回执后恢复原保存按钮。新增真实反例2项，快捷键9项/6.88s实际0，待新head原非作者复验。没有改变科学算法、时限或旧测试预期。

同时实现非作者独立核验T065窄CI测试修正a263fee：无行动项，产品无diff，原身份/非忙态加强成功条件，20秒和完整来源断言不变；冻结1/4.46s实际0。该结论不自动外推T066修正head。
