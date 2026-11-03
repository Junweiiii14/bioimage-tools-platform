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

- 合入依赖main5d6e03b后重新加载准确规则回执。四模块README只加当前/历史边界，未改src、测试或公共契约；325个本地Markdown链接核验无缺失。旧主目录先归档再更新短恢复路由，未覆盖旧源码/规划；handoff检查无未解决项。手机HTML截图人工查看未见裁切。

## 最终集成

候选8e99409be20de20856e7dd1b52d5743559344340；质量run41642082896、规则run41642082867，四项必需检查success。Windows1692 passed/10 warnings/1098.46s；Linux1688 passed/4既有平台skip/10 warnings/998.09s；两平台独立安装后的真实工作流通过。条件native-case跳过，不当作目标机验收。PR54正常merge至f2a7a7801930a3ea5a14565c11eda84636bec933。Issue57保留真实缺口；新方案从B019开始。
