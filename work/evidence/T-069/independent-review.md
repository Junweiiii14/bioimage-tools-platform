# T069绑定独立审查

非作者t064_independent_review，只读冻结archive，不改产品/Git/证据。

## 独立发行与安装诊断

base e9ce125b904bee445acd2f0f6b81a38bd82093ae → head745d0431c979915b25f8e09595754761500973ef：范围内无新增可证实P0–P2。

实际run_cli_review.py：新grouped CLI17项检查/两个真实worker PID/9.625s实际0；旧intake CLI14项/9.907s实际0；已有报告拒绝覆盖实际1/内容不变；grouped启动故障实际1、所属资源/窗口清理完成；构建旗标互斥实际2。run_namespace_review.py：真实GroupedIntakeTest构造隔离1通过/3.22s实际0。最终两审查命令均0。四种安装AppId独立，新channel/设置/目录/快捷方式与manifest映射相符。

应用通过-I冻结源码bootstrap执行，worker所用118份源码与冻结内容相符。未运行完整门禁、私图链、安装构建、PS5.1自检，也未重新验证独立灰度/OCR；结论不表示离线包已交付。

## 真实数据发现的多根导入修复

base989234f500bbf77b4569ec81a4b0a2e6575bad05 → headfb95c91315d516565c4991a2e4cb33c5c3e6e72b：原多根忙态缺陷resolved，无新增可证实P0–P2。

run_review.py冻结复验6通过/7.54s实际0：同次两根来源独立、原保存重开/重复跳过；单文件使用父根且不导入邻居；嵌套根正反顺序均最具体归属/去重，位深/尺寸/原图保持；越根和有效+越根混合输入整体在begin_operation前拒绝，无忙态/部分导入。没有重复745已通过的诊断、完整门禁或私图链。

所有脚本/日志保留忽略的.local/t069-{independent,multi-root}-review；产品后继若实质修改对应路径须重新审，不将本结果扩展至尚未构建的安装包。
