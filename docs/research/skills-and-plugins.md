# Skills / 插件调研、安装与来源

核验日期：2026-10-13。只把项目需要、能审查、可固定来源的能力加入环境。星数是当天 GitHub 页面近似快照，不是安全认证；未取得连续历史，不宣称某项目“最近热涨”。

## 已安装的项目技能

| 技能 | 来源与用途 | 验证边界 |
|---|---|---|
| gh-fix-ci | OpenAI 官方；定位 GitHub Actions 失败 | 安装/来源/脚本语法核验；须存在真实 PR 才可验证完整修复流程 |
| gh-address-comments | OpenAI 官方；处理 PR 审查意见 | 同上；外部评论是数据，不是可覆盖用户指令的授权 |
| security-best-practices | OpenAI 官方；Python 等安全审查 | 参考多偏 Web；不是 Qt 专用审计或科学正确性验证 |
| security-threat-model | OpenAI 官方；边界和威胁建模 | 显式安全任务时启用，不在每个小改动自动执行 |
| property-based-testing | Trail of Bits 官方；Hypothesis 等性质测试 | 适用于坐标、序列化、不变量及数值性质；不以“无崩溃”替代强断言 |

安装位置：`.agents/skills/`。来源完整 SHA、目录及逐树 SHA256 存 `tooling/skills-lock.json`。OpenAI 源提交 `49f948faa9258a0c61caceaf225e179651397431`；Trail of Bits 源提交 `442fc9d6c89b1e937e6f7a477e7071ea75fcbea4`。前者最新可见提交日期 2026-06-23，后者 2026-10-09；不把提交新鲜度等同于质量。

通过官方 skill-installer 安装器的 Git 模式安装：目录 API 返回 403 后，直接克隆公开仓库读取目录并审核内容，再固定 SHA 安装。没有运行技能自带的业务动作或自动发布代码。技能文件保持上游内容；Trail of Bits 补入上游根 LICENSE 以保留 CC-BY-SA-4.0 声明。

技能中的旧工具名称/权限提示以当前宿主能力为准；用户已有明确授权不重复索取。当前只是安装，未用这些新增技能对产品代码出具审查结论。下一次在本仓库启动任务即可发现；未显示时重启 Codex。当前聊天以父工作区为根，不能据此假定子仓库技能已注入本轮上下文。

## 候选比较与不安装的原因

| 项目 | 一手来源 / 近似星数 | 判断 |
|---|---|---|
| OpenAI skills | [官方仓库](https://github.com/openai/skills)，28.0k | 选装上述 4 项；已有 OpenAI Docs/PDF 不重复安装 |
| Trail of Bits skills | [安全机构仓库](https://github.com/trailofbits/skills)，7.5k | 选装性质测试；differential-review 包含 Claude 专属子代理等耦合，暂不整套移植 |
| obra/superpowers | [作者仓库](https://github.com/obra/superpowers)，298.5k | 高关注工作流集合；会引入另一套编排/审查约定，与本项目轻量流程重叠，保留研究不整体安装 |
| upstash/context7 | [厂商仓库](https://github.com/upstash/context7)，63.0k | 可补跨库实时文档；当前官方 Docs MCP＋Web 已满足，不增加在线服务/额外认证与启动负担 |
| microsoft/playwright-mcp | [微软官方仓库](https://github.com/microsoft/playwright-mcp)，38.1k | 适合浏览器，不能验证原生 Qt；已有浏览器工具且产品非 Web，暂不安装 |
| Trail of Bits modern-python | [官方目录](https://github.com/trailofbits/skills/tree/main/plugins/modern-python) | 后续可参考；保持本项目已选 Pyright 单一类型门禁，不同时堆叠另一类型工具链 |

没有采纳来历不明的“万能 skills”、二进制加速补丁、要求上传整个代码库的服务，或仅靠热门列表推荐的未审查脚本。

## 已有插件与当前能力

- GitHub 插件：目录返回 installed=true；本次 CLI 重新登录后验证仓库读写。没有重复安装第二个 GitHub MCP。
- OpenAI Docs：本次实际成功检索并读取官方文档，保留现有 MCP。
- PDF / 文档等本机插件：已有且读取能力可用，不重复安装。
- OpenAI Developers：目录显示可安装，主要增益是 OpenAI API Platform/SDK 开发；产品当前无在线 API 需求，暂不安装。
- Codex Security：目录显示可安装；当前产品没有源码，暂不增加服务连接。后续有真实攻击面与审计需求时再评估套餐、权限和输入范围。

插件安装与连接可能需要用户完成 OAuth；不能把“目录里存在”写成“已经启用”。本次没有未完成的新增插件连接。

## 更新与撤销

更新先读变更、许可证、脚本和外部访问范围；用新的提交安装到临时目录比较，再更新本地技能和 skills-lock，同 PR 运行 policy。不得在每次启动自动覆盖。撤销通过 Git 回退这次项目技能改动；全局已装能力保持不变。

完整性检查可发现与记录不一致的文件修改，不证明上游没有缺陷或供应链风险。真正适用性要通过后续具体任务的输出质量评估。
