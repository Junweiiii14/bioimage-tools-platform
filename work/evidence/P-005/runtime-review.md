# P005生产执行候选独立审查

## 第一轮：Request changes

准确总范围006e9f143c830f5e13be2932e8ac37a9f3a05ed1..5814e528abb2e8d387d1bc88e83612b1d2ec3175，重点b80b900..5814e52；非作者/root/p002_independent_review只读核验。

P2：合法非WB journal经prepare_wb_workspace(rerun=id)进入next()，StopIteration未回传异步消息，WorkflowSession._preparing保留，关闭无法drain。独立真实Workspace/WorkflowSession探针completed0/pendingTrue/services_closingFalse；显式补发探针清理回执后退出，不能把探针exit0当产品通过。建议rerun入口一次验证固定WB形状并抛ValueError，不扩大内部catch。

独立tests/test_workflow_session.py及test_workflow_window.py --basetemp=.local/p005-final-independent-5814：24pass116.56秒/exit0；另外两反例探针exit0确认缺陷；11源码摘要及wheel日志SHA一致，diff检查0。Windows11/Python3.12.14/Qt离屏。未跑全量或重建全部wheel，未修改共享文件。不接受该候选，先前组件接受保留。

## 作者修正与验证边界

rerun外部入口验证固定三个WB module ID及同一原始来源，再按已确认形状索引分析/发布节点；不捕获StopIteration、不把非WB适配成默认成功。新增真实通用journal→WorkflowSession.initialize→错误回传→异步关闭→重开原账本不变/无run的回归，1pass2.64秒；严格类型修正后继续定向验证。

旧5814全量本机运行已在约13%观察到F并伴历史GPU context日志，尚无完整trace/具体原因；因本轮产品修正主动中止，session19645终止exit1、pytest PID29552已查不存在，原日志.local/p005-final-check-5814e52.log保留，不声称通过。旧运行未设置CI已有--disable-gpu；新准确候选使用同一CI环境重新全验，未修改门禁或原失败预期。

## 第二轮：Accepted（生产候选）

非作者准确接受006e9f143c830f5e13be2932e8ac37a9f3a05ed1..384e5ba1137e55385e3a4b10f2e694b51840229a。独立新增异步回归及全部窗口6pass19.46秒/exit0；原反例Workspace重放收到一个ValueError回执、未创建run/exit0；全范围diff0、准确HEAD/clean。此前24pass116.56秒保留。不代替全量、wheels或M1/M2。新候选作者完整门禁exit0、1659pass928.26秒及全部隔离wheels通过，Linux必需CI1655pass/4既有skip738.87秒及wheels通过。科学与目标机缺项未关闭。

## Windows CI时限变更（单独说明）

run41413166304/job125170776585的服务器注解明确The job has exceeded the maximum execution time of 20m0s；job20m11秒/cancelled，pytest仍在82%继续通过、未出现FAILED断言行，不能写全量成功。新控制器19项实际worker故障/恢复用例在该机跨105.67秒，另有三节点/界面验证；这些真实用例已把本轮总作业推到现有时间上限之外。本机同源完整1659项和Linux1655项均已通过，未以超时取消代替断言成功。

仅Windows foundation作业总墙钟上限20→25分钟，Ubuntu保持20；所有检查命令、测试集合、单测超时/预期/skip/容差、必需检查和服务器规则不变。GitHub官方workflow-syntax定义job timeout为自动取消上限，contexts文档允许timeout-minutes使用matrix。来源：https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idtimeout-minutes 与 https://docs.github.com/en/actions/reference/workflows-and-actions/contexts ，访问2026-11-02。

原超时注解与完整日志SHA见ci-timeout-r1.json；资源配置增量仍需准确独审与新必需CI，不能把旧Linux/本机通过充作新Windows通过。产品源码保持384e5ba。
