# B019方案验证

基线main f2a7a7801930a3ea5a14565c11eda84636bec933，Windows/PowerShell，Python3.12.14借用bioimage-v0环境执行当前树文档工具；Node、锁定marked17.0.5、headless Edge。产品源码与运行门禁未改。

- 4.2三份文档以准确基线Git blob字节保存，SHA256见archive-manifest.json；不改历史正文。旧snapshot原字节保存为.txt，避免移动位置后把内部相对链接当当前导航；初次链接检查发现该归档相对路径，转换为明确的原位置语义快照，当前导航另设。
- `npm run build --prefix docs/plans/renderer`退出0，五份HTML；渲染器改名build-current，页壳不再把历史WB研究标成当前方案版本，正文日期各自保留。
- `node work/evidence/B-019/verify_documents.cjs`退出0；五份HTML桌面/390宽、菜单/搜索/打印、锚点/本地文件和离线请求均通过。当前章节数10/7/8/5/7按新文档更新，不修改B018历史检查或降低产品预期。
- `python work/programs/scientific-agent-platform/check_plan.py`退出0，15工作包/10卡；已有完成状态保留，P004/P010 planned。新工作包W14只登记调研；W06不再无条件依赖新几何，但真正需要新几何时必须显式登记P004及科学验证前置，不豁免方法验收。
- `python -m ruff format --check .`退出0，1243文件格式通过。
- 无新增实验实测、独立用户试用、付费验证或目标机验收，不以规划和文档检查宣称这些已完成。PR既有完整检查仍需核验准确提交。

- 修正归档展示方式后，250个本地Markdown链接无缺失；三份快照与基线Git blob SHA一致。主方案390宽截图人工查看无裁切；五文档脚本检查结果见html-validation.json。policy退出0，git diff --check退出0。
