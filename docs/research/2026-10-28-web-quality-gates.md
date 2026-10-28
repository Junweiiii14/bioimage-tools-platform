# 工作台 JavaScript 最小质量门禁

问题：Python门禁不覆盖19个经典browser script，部分长行掩盖控制流；希望提高可读性并约束桥接身份，保持Qt和预览共用资源及当前协议。

2026-10-28核验[Prettier安装说明](https://prettier.io/docs/install)、[ESLint配置](https://eslint.org/docs/latest/use/configure/configuration-files)、[TypeScript checkJs](https://www.typescriptlang.org/tsconfig/checkJs.html)。npm官方注册表确认固定Prettier3.9.10、ESLint10.13.0、Espree11.2.0、TypeScript5.9.3的版本与工件完整性，依赖锁入package-lock。TypeScript5.9.3已有所需checkJs/JSDoc能力，不为此任务迁移到新大版本或引入运行时框架。

决定：先独立纯格式提交266c068（非作者19AST/注释一致、实际UI19通过），再加入版本固定的开发工具。沿用.editorconfig四空格，禁用嵌入语言格式化，保留模板字符串值。初始lint选择控制流、重复键/分支、不安全finally/optional chain等明确正确性规则；不宣称所有脚本已严格类型化。checkJs先覆盖实际高级请求生产函数和WorkBenchIdentity/JSDoc，保持原字段、顺序、schema_version=1和宿主独立验证。

未选择全仓JS转TypeScript/框架或强制所有旧脚本补类型：会把本项扩为UI迁移。没有因格式放宽已有行为断言。新增4个检查自身的验证：真实CLI拒绝格式错误、真实CLI拒绝不可达代码、同一tsconfig拒绝错误身份/请求类型、运行实际生成函数核对旧wire字符串。

门禁接到既有dev.py check、pre-commit和quality foundation Windows/Linux两平台。Node由.node-version固定26.7.0，npm ci --ignore-scripts重建锁依赖；检查不联网自动补工具。actions/setup-node官方v7标签经只读git ls-remote解析为949feb2413d6458794dcd2491c4babbbce0c15c1并固定，不修改现有必需检查名称或服务器规则。Node只用于开发，不进Python产品运行依赖。

限制：旧共享UI状态和动态Qt通道的大部分调用点仍未checkJs；后续R03在接收/诊断边界继续收口。新全仓门禁和远端CI结果分别记录，配置存在不是已经跑过。升级工具、补新的payload或改变script加载顺序时重新做负例和相应实际UI验证。
