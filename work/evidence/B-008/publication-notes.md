# B008 发布说明与验证

2026-10-31用户授权新版方案进入GitHub、整理入口，并用GPT-6 Astra新聊天在目标模式推进第一阶段。当前提交基于远端main `18b5cf6de0c83b8c67f26433a6059d8dabf1f381`，是文档/计划发布；本地实际产品T082 `dfc48ed7c2c944dc8f03c3931bc7985452a31393`领先28提交，未通过本次文档发布自动集成。

## 发布范围

- 主方案3.0、旧2.0快照与B005治理补充、17条公开数据登记、必要B004/B007研究及审阅依据；本次白名单和源/发布摘要见source-transfer-manifest.json。
- README和计划目录区分产品使用、未来研发、数据、历史；V0阶段单独给可执行范围和完成条件。
- P卡统一新版接口名、数据用途、性能目标及V0真实worker/提交/恢复/图形对照；状态保留planned，P001仍负责接入真实产品树。
- 不携带私有图、实际公开数据小样、安装包、模型、旧dirty产品或B005–B007旧规则回执。main既有历史回执保持原样；本PR只新增B008当前回执。

## 可移植构建变化

原本机交付的内嵌字体HTML约24MB，原文及旧审阅摘要继续保留在本地历史。GitHub版把3个本机证据链接改为仓库相对路径，去除机器根路径显示，统一LF；科学正文不改写。生成HTML复用仓库已有Noto Sans SC资源，约344KB，可在完整克隆中离线打开。便携模式仍可生成内嵌字体的单文件到.local。

新文档构建器为docs/plans/renderer/build.mjs，单独固定marked 17.0.5（与本机原构建器版本相同）；包/锁仅属于文档工具，无产品锁文件或CI门禁变化。npm来源为registry.npmjs.org，MIT及完整性摘要在package-lock.json。安装时关闭依赖脚本；未修改npm全局配置。

已有check_plan.py首次发布时Ruff报SIM102/E501及格式差异。修正为等价合并条件、断行和格式化；不改变任务依赖准入行为。其检查仍不替代科学/权限/用户验收。

## 已运行

- `npm install --prefix docs/plans/renderer --package-lock-only --ignore-scripts --no-audit --no-fund`、`npm ci ...`及`npm run build ...`均退出0。Node v26.7.0，仅安装一个文档依赖。
- `uv run --locked --no-sync ruff check`与`ruff format --check`针对发布的计划检查器；初次失败如上，修复后通过。
- `uv run --locked --no-sync python work/programs/scientific-agent-platform/check_plan.py`退出0：六P任务planned，仅P001依赖就绪。
- `uv run --locked --no-sync python dev.py policy`退出0，扫描当前main的173个产品文件；未把这当T082或新产品功能验证。
- `publication-validation.json`：13章、49表、17数据记录、仓库相对链接存在、无file://证据链接，字体存在。
- context使用目标树自己的dev.py，显式UV_PROJECT_ENVIRONMENT指向已安装的产品venv，仅`--no-sync`跑文档/规则检查，未同步/升级该环境。规则变化后重新生成唯一B008回执，最终检查绑定PR base/head。

GitHub必需CI、提交独审和新聊天goal状态将在B008任务卡及对应GitHub对象中记录；不伪造已经完成的集成或用户科学验收。

## 首轮失败与修正

首次commit钩子在新worktree空venv中找不到ruff，退出2；显式选择已安装的T082 venv且--no-sync后，三个原有钩子全部通过，未跳过钩子或改变产品依赖。

首提交ac983007的GitHub quality run 41181434999在两平台均被Ruff格式检查阻止：3.0及2.0归档的Python示例各缺一个空行。仅补格式要求的空行，重建HTML并更新投影摘要；随后本机全仓Ruff format --check报告990文件已格式化。没有修改原始本地交付、公式、测试或CI门禁。

ac983007的非作者P卡/阶段计划审查Accepted；另一审阅者发现便携模式将输出移到.local后仍留三处相对证据链接，报告Blocked。已仅对便携模式将这三处改为GitHub main文件链接，并说明查看外部证据需要联网和文档PR已合入。仓库模式相对链接保持，字体与正文仍可离线读取。最终增量审查结论绑定最后提交记录于PR46；本文件不提前声称其通过。

Edge headless仓库版实际打开：13章/49表，WB Sans字体loaded，无pageerror/requestfailed，1440px下正文无横向溢出，截图已视检。原始烟测保留本机.local/B008-html-smoke.json与PNG，不作为新产品验收。便携修正后重新构建并独立核验链接。

GitHub阶段issue44、milestone2及维护issue45已创建。GPT-6 Astra新聊天返回ID并已开始基线接入，目标active的执行者核验见thread-dispatch.json。B008完成只按任务卡最终闭合条件与GitHub准确HEAD事实判定。
