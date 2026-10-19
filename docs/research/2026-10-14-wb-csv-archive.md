# WB CSV 文字与归档证据（2026-10-14）

问题：CSV 没有 XLSX inlineStr 类型，科研标签可能以等号、正负号、@、换行开头。如何避免表格程序把标签当公式，同时保留数字/空值和原始文字？

已核对官方来源：

- [Python 3.12 csv](https://docs.python.org/3.12/library/csv.html)：writer 使用标准字段/引号转义；QUOTE_NONNUMERIC 区分未引用数字，None 写为空字段。实测运行时3.12.14，网站当前3.12.15文档；使用既有稳定API，无新增依赖。
- [OWASP CSV Injection](https://community.owasp.org/attacks/CSV_Injection)：仅包引号不足以阻止公式；引用/转义可能在表格程序重新保存时被移除，各软件行为不一致，没有适用于所有消费者的通用清洗方法。

决定：XLSX 保持原文字的明确字符串类型；CSV 所有数据字符串前置普通文字 `text:`，以固定版本声明可逆编码，受控表头不编码。数值仍交 writer 作为 float/int，None 保留空字段。这个选择牺牲 CSV 直接展示的简洁性，避免依赖某一版本 Excel 的引号/单引号/tab 特殊行为；CSV 选择器提示该前缀。程序使用时去掉恰好一个前缀，不能全部替换。

验证：标准库reader读回带逗号/引号/CR/LF、中文、全角等号、前导零、空字符串与已有text:的标签；QUOTE_NONNUMERIC读回真实0为float、缺失为空。CSV/XLSX/ZIP使用同一表构建器并逐字段/原OOXML比较；没有以数字转字符串代替原数值。未执行外部表格软件兼容矩阵，不声称任意二次编辑/恶意改写后仍安全。

归档决定：保留现有manifest v1和原像素裁剪，新增archive.json v2索引实际字节摘要、大小/角色、运行验证和缺项。重读工作区请求/结果而非复用显示缓存；仅保存历史证据，不导入或伪造本地成功。标准库ZIP/CSV/hashlib及已有Pillow/tifffile无版本变更。若未来增加ZIP导入、签名、流式大项目或第三方CSV适配，须重审信任、预算和编码契约。
