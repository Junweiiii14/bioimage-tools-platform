# B018 收尾验证

环境：Windows、PowerShell；已有bioimage-v0环境Python3.12.14执行当前工作树命令，Node与marked17.0.5、headless Edge。PR基线6e0dcd44ae726caffa9215da49bcf569737258cd。

- P009白名单复制并核验：两个原CI gzip及解压SHA与integration.json完全一致；ba07dba与merge6e0dcd4 tree相同。原文收尾来源摘要见p009-transfer.json；随后仅在任务卡加固定版本引用，原始元数据/验收含义保留。
- 原PR54失败已定位到4.0历史方案232行Python示例的空行；Ruff格式化仅增加一空行，原字节可从e9d2125历史恢复。不改门禁、公式、预期值或测试。
- `npm ci --prefix docs/plans/renderer --ignore-scripts`：退出0，锁定依赖安装，无锁文件变化。
- `npm run build --prefix docs/plans/renderer`：退出0，默认已指向当前五文档构建器；旧脚本输出改为.local历史目录。
- `node work/evidence/B-018/verify_documents.cjs`：退出0；五文档1440/390宽度，无外层横溢、缺失本地链接、锚点错误、脚本异常或外网请求；菜单/搜索/打印检查通过。结果html-validation.json。
- `python work/programs/scientific-agent-platform/check_plan.py`：退出0，14工作包/9卡；P001/2/3/5/6/7/8/9 done，P004 planned。候选不等于授权。
- `python -m ruff format --check .`：退出0，1232文件格式通过。
- 一次整理脚本在默认GBK读取build.mjs时停止；改为显式UTF-8并从中断点继续，已重新生成与验证，不覆盖源数据，不把首次脚本视为成功。
- 本轮未运行产品全量/科学/真实用户/目标机验证。原P009 CI保留准确提交归属；本PR完整必需CI尚需核验，不以文档检查代替。

- 历史构建 `npm run historical-v4 --prefix docs/plans/renderer`：退出0，固定4.0源输出到.local历史目录，当前五份HTML未覆盖。根AGENTS仅更新过期恢复指令，不变更质量/数据/合并约束；重新加载回执。
