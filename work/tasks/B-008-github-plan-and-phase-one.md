# B-008 新研发方案发布GitHub与第一阶段派发

## 状态

- 2026-10-31；方案发布及新窗口派发已执行，下述最终闭合条件全部满足时complete，否则in_progress。
- 用户明确授权：新版方案放入GitHub并整理仓库；第一阶段交给新窗口，GPT-6 Astra，目标模式持续推进。

## 范围和结果

- 核对远端main、PR、分支与较新本地产品树，保留旧dirty与历史产品限制。
- 从实际远端main建立隔离文档分支，发布B007方案、数据登记、必要依据、第一阶段任务与入口；不夹带本地主目录产品dirty、原图/样本包、安装包或旧规则回执。
- 整理README/计划目录与首阶段GitHub任务；主分支经PR和必需检查处理，不删除历史分支、不关闭未解决缺项。
- 第一阶段定义为V0旧WB独立运行完整切片，先P001接入较新产品基线再推进P002及该交付必需配套；保留当前界面风格与科学公式，不自动扩展V1/IF/Agent。
- 创建新项目聊天，显式模型gpt-6-astra，提示创建真实goal并持续开发；核验启动状态，不只投递一句计划。

## 验证与完成

已建立GitHub第一阶段issue #44及milestone 2；依赖维护索引#45保留三个未解决PR和历史日志。

文档构建、链接/17条数据登记核验、计划检查、Ruff与离线policy均退出0；环境及限制见work/evidence/B-008/publication-notes.md。首次CI的两份Markdown Python示例缺空行已按固定Ruff格式化，不变代码语义或门禁。

已发布分支codex/b008-rd-plan-github，首提交ac983007f8fa99a4566ae9aa363eb164982713bb，PR46。首提交P卡独审Accepted；可移植性独审发现便携HTML证据相对链接失效，已改为明确GitHub证据链接，最终准确提交增量审查仍需核对。

新聊天ID：01a190e6-02b1-74e3-a7b9-bd5fbc3f36fe，host local，create_thread显式model gpt-6-astra。已由read_thread及wait_threads读到执行者确认create_goal及get_goal均为active、无token预算，并已开始恢复较新产品基线。本任务只负责派发，不把V0标为完成。具体分派核验见thread-dispatch.json。

## 最终闭合条件

最终PR46准确HEAD的非作者审查Accepted，rules-context、foundation Windows、foundation Ubuntu和desktop-environment四必需检查均SUCCESS，正常merge后main树与该HEAD相同，发布工作树干净；GitHub方案、issue44/milestone2与维护索引45可读，新聊天真实目标active且已着手执行。只有这些事实同时成立才complete；PR最新状态是闭合证据，不用未来检查结果预写成功。首轮失败保留。禁止绕过门禁合并、把文档发布等同T082/V0产品完成，或覆盖旧dirty、原图/历史/安装。
